"""Orchestrates the whole engine: body → palette → ranking → budget → look."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .body import BodyProfile, analyze_body
from .budget import LookDraft, build_look
from .explain import item_reasons, look_summary, look_tips, personal_note
from .options import SLOT_CATEGORIES, SLOT_LABELS, SLOT_PLANS, plan_for_season
from .palette import PaletteProfile, analyze_palette
from .ranking import (
    ENGINE_VERSION,
    CatalogItem,
    RankingContext,
    ScoredItem,
    default_weights,
    look_cohesion,
    look_score,
    palette_from_style,
    rank_candidates,
    style_verdict,
)


class LookGenerationError(RuntimeError):
    pass


@dataclass
class LookRequest:
    style: str
    mood: str
    height_cm: float
    weight_kg: float
    budget_rub: float
    occasion: str = "everyday"
    season: str = "all"
    presentation: str = "unisex"
    preferred_colors: list[str] = field(default_factory=list)
    avoid_colors: list[str] = field(default_factory=list)
    size: str | None = None
    plan: str | None = None
    weights: dict[str, float] | None = None
    vision: dict[str, Any] | None = None
    exclude_skus: list[str] = field(default_factory=list)
    #: Свободный текстовый запрос («грязный индустриальный образ с прозрачным
    #: верхом») — уходит в движок ASSTYLIST Fashion Engine как основа запроса.
    query: str | None = None
    #: Явный уровень ниши 0…100 (иначе выводится из стиля).
    niche_level: int | None = None


@dataclass
class LookResult:
    items: list[dict[str, Any]]
    total_rub: float
    budget_rub: float
    score: float
    verdict: dict[str, str]
    cohesion: dict[str, float]
    summary: str
    tips: list[str]
    body: BodyProfile
    palette: PaletteProfile
    plan: str
    diagnostics: dict[str, Any]
    #: Короткое объяснение «почему этот образ именно вам» (цветотип, силуэт, повод).
    personal_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": self.items,
            "total_rub": self.total_rub,
            "budget_rub": self.budget_rub,
            "budget_utilization": round(self.total_rub / self.budget_rub, 3) if self.budget_rub else 0.0,
            "score": self.score,
            "verdict": self.verdict,
            "cohesion": self.cohesion,
            "summary": self.summary,
            "personal_note": self.personal_note,
            "tips": self.tips,
            "body": self.body.to_dict(),
            "palette": self.palette.to_dict(),
            "plan": self.plan,
            "engine_version": ENGINE_VERSION,
            "diagnostics": self.diagnostics,
        }


def _medians(products: list[CatalogItem]) -> dict[str, float]:
    buckets: dict[str, list[float]] = {}
    for product in products:
        buckets.setdefault(product.category, []).append(product.price_rub)
    medians: dict[str, float] = {}
    for category, prices in buckets.items():
        prices.sort()
        mid = len(prices) // 2
        medians[category] = prices[mid] if len(prices) % 2 else round((prices[mid - 1] + prices[mid]) / 2, 2)
    return medians


def _resolve_plan(request: LookRequest, by_slot: dict[str, list[CatalogItem]]) -> str:
    """Pick a plan that the catalog can actually fulfil."""
    candidates = [request.plan] if request.plan else []
    # A tight budget cannot carry a coat *and* everything else — drop the layer
    # first rather than overspending.
    if request.budget_rub < 15_000 and not request.plan:
        candidates.extend(["light", "dress"])
    candidates.append(plan_for_season(request.season, request.occasion))
    for fallback in ("layered", "light", "dress"):
        if fallback not in candidates:
            candidates.append(fallback)

    for plan_id in candidates:
        plan = SLOT_PLANS.get(plan_id)
        if not plan:
            continue
        ok = True
        for slot, spec in plan["slots"].items():
            if spec.get("required") and not by_slot.get(slot):
                ok = False
                break
        if ok:
            return plan_id
    return candidates[0] if candidates[0] in SLOT_PLANS else "layered"


def _items_by_slot(products: list[CatalogItem]) -> dict[str, list[CatalogItem]]:
    by_slot: dict[str, list[CatalogItem]] = {slot: [] for slot in SLOT_CATEGORIES}
    for product in products:
        for slot, categories in SLOT_CATEGORIES.items():
            if product.category in categories:
                by_slot[slot].append(product)
    return by_slot


@dataclass
class PreparedPool:
    """Общая подготовка для обоих пайплайнов (ранжировщик приложения / движок).

    ``look_builder.generate_look`` (legacy-путь) и
    ``fashion_engine_service.generate_look`` (движок) работают на одном и том
    же пуле: проверенные товары → жёсткие исключения → скоринг → слоты → план.
    """

    body: BodyProfile
    palette: PaletteProfile
    ctx: RankingContext
    ranked: list[ScoredItem]
    rejected: list[dict[str, Any]]
    candidates_by_slot: dict[str, list[ScoredItem]]
    catalog_by_slot: dict[str, list[CatalogItem]]
    plan_id: str
    plan: dict[str, Any]

    def scored_by_sku(self) -> dict[str, ScoredItem]:
        return {scored.sku: scored for scored in self.ranked}


def prepare_pool(products: list[CatalogItem], request: LookRequest) -> PreparedPool:
    """Отобрать пул, посчитать контекст, разложить кандидатов по слотам."""
    if not products:
        raise LookGenerationError("Каталог пуст — не из чего собрать образ")

    body = analyze_body(request.height_cm, request.weight_kg, request.presentation, request.vision)
    palette = analyze_palette(request.vision, request.preferred_colors, palette_from_style(request.style))

    pool = [p for p in products if p.sku not in set(request.exclude_skus)]
    if not pool:
        raise LookGenerationError("Все товары каталога исключены")

    ctx = RankingContext.build(
        style=request.style,
        mood=request.mood,
        occasion=request.occasion,
        season=request.season,
        presentation=request.presentation,
        palette=palette,
        body=body,
        weights=request.weights or default_weights(),
        preferred_colors=request.preferred_colors,
        avoid_colors=request.avoid_colors,
        size=request.size,
        category_medians=_medians(pool),
    )

    ranked, rejected = rank_candidates(pool, ctx, request.budget_rub)
    ranked_by_category: dict[str, list[ScoredItem]] = {}
    for scored in ranked:
        ranked_by_category.setdefault(scored.item.category, []).append(scored)

    candidates_by_slot: dict[str, list[ScoredItem]] = {slot: [] for slot in SLOT_CATEGORIES}
    for slot, categories in SLOT_CATEGORIES.items():
        merged: list[ScoredItem] = []
        for category in categories:
            merged.extend(ranked_by_category.get(category, []))
        merged.sort(key=lambda s: (-s.score, s.item.price_rub, s.item.sku))
        candidates_by_slot[slot] = merged

    catalog_by_slot = _items_by_slot(pool)
    plan_id = _resolve_plan(request, {k: v for k, v in catalog_by_slot.items() if v})
    plan = SLOT_PLANS[plan_id]

    return PreparedPool(
        body=body,
        palette=palette,
        ctx=ctx,
        ranked=ranked,
        rejected=rejected,
        candidates_by_slot=candidates_by_slot,
        catalog_by_slot=catalog_by_slot,
        plan_id=plan_id,
        plan=plan,
    )


def generate_look(products: list[CatalogItem], request: LookRequest) -> LookResult:
    prepared = prepare_pool(products, request)
    body = prepared.body
    palette = prepared.palette
    ctx = prepared.ctx
    ranked = prepared.ranked
    rejected = prepared.rejected
    candidates_by_slot = prepared.candidates_by_slot
    plan_id = prepared.plan_id
    plan = prepared.plan

    draft: LookDraft = build_look(candidates_by_slot, plan["slots"], request.budget_rub)

    picked = draft.picked
    if len(picked) < 3:
        raise LookGenerationError(
            "Недостаточно подходящих товаров: попробуйте увеличить бюджет или смягчить требования"
        )

    # render items in the order declared by the plan (coat → top → bottom → ...)
    slot_order = {slot: spec.get("order", 9) for slot, spec in plan["slots"].items()}
    slot_of: dict[str, str] = {}
    for slot, scored in picked.items():
        slot_of[scored.sku] = slot
    ordered_items = sorted(picked.values(), key=lambda s: slot_order.get(slot_of[s.sku], 9))

    chosen = list(picked.values())
    cohesion = look_cohesion(chosen, ctx)
    score = look_score(chosen, cohesion)
    verdict = style_verdict(score)

    ctx_info = {
        "style": request.style,
        "mood": request.mood,
        "palette_label": palette.season_label,
        "silhouette_ru": body.silhouette_ru,
    }

    items_payload: list[dict[str, Any]] = []
    for index, scored in enumerate(ordered_items):
        slot = slot_of[scored.sku]
        alternatives = [
            {
                "sku": alt.sku,
                "name": alt.item.name,
                "brand": alt.item.brand,
                "price_rub": alt.item.price_rub,
                "score": round(alt.score, 3),
                "colors": alt.item.colors,
            }
            for alt in candidates_by_slot.get(slot, [])
            if alt.sku != scored.sku
        ][:3]
        items_payload.append(
            {
                "position": index,
                "slot": slot,
                "slot_label": SLOT_LABELS.get(slot, slot),
                "sku": scored.sku,
                "category": scored.item.category,
                "name": scored.item.name,
                "brand": scored.item.brand,
                "price_rub": scored.item.price_rub,
                "url": scored.item.url,
                "image_url": scored.item.image_url,
                "colors": scored.item.colors,
                "color_hexes": scored.item.color_hexes,
                "fit": scored.item.fit,
                "score": round(scored.score, 4),
                "breakdown": scored.breakdown,
                "reasons": item_reasons(scored, ctx_info),
                "verification_status": scored.item.verification_status,
                "verification_score": round(scored.item.verification_score, 3),
                "source": scored.item.source,
                "alternatives": alternatives,
            }
        )

    tips = look_tips(list(body.tips), palette.to_dict(), request.style, picked)
    summary = look_summary(
        request.style,
        request.mood,
        request.occasion,
        draft.total_rub,
        request.budget_rub,
        picked,
        score,
    )

    diagnostics = {
        "plan": plan_id,
        "plan_description": plan["description"],
        "candidates_total": len(ranked),
        "rejected_total": len(rejected),
        "rejected_sample": rejected[:10],
        "dropped_slots": draft.dropped_slots,
        "warnings": draft.warnings,
        "budget": draft.to_dict(),
        "weights": ctx.weights,
        "excluded_skus": request.exclude_skus,
    }

    return LookResult(
        items=items_payload,
        total_rub=draft.total_rub,
        budget_rub=request.budget_rub,
        score=score,
        verdict=verdict,
        cohesion=cohesion,
        summary=summary,
        tips=tips,
        body=body,
        palette=palette,
        plan=plan_id,
        diagnostics=diagnostics,
        personal_note=personal_note(
            style=request.style,
            mood=request.mood,
            occasion=request.occasion,
            palette=palette,
            body=body,
            picked=picked,
            total_rub=draft.total_rub,
            budget_rub=request.budget_rub,
        ),
    )
