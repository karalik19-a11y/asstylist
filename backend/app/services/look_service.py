"""Look generation + persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..engine.body import BodyProfile, body_from_dict
from ..engine.look_builder import LookGenerationError, LookRequest, LookResult, generate_look
from ..engine.options import SLOT_CATEGORIES
from ..engine.palette import PaletteProfile, palette_from_dict
from ..engine.ranking import ENGINE_VERSION, RankingContext, rank_candidates
from ..models import Look, LookItem, User
from ..telegram.auth import TelegramUser
from . import catalog_service, fashion_engine_service


def _find_user(session: Session, telegram_id: str) -> User | None:
    return session.execute(select(User).where(User.telegram_id == telegram_id)).scalar_one_or_none()


def get_or_create_user(session: Session, identity: TelegramUser) -> User:
    user = _find_user(session, identity.telegram_id)
    if user is None:
        candidate = User(
            telegram_id=identity.telegram_id,
            username=identity.username,
            first_name=identity.first_name,
            is_demo=identity.is_demo,
        )
        session.add(candidate)
        try:
            session.commit()
            session.refresh(candidate)
            return candidate
        except IntegrityError:
            # Два параллельных запроса (например, авторизация и история) могут
            # создать демо-пользователя одновременно: строку уже вставил сосед,
            # поэтому просто читаем её вместо падения в 500.
            session.rollback()
            user = _find_user(session, identity.telegram_id)
            if user is None:
                raise
            return user

    changed = False
    if identity.username and user.username != identity.username:
        user.username = identity.username
        changed = True
    if identity.first_name and user.first_name != identity.first_name:
        user.first_name = identity.first_name
        changed = True
    if changed:
        session.commit()
    return user


def to_engine_request(payload: dict[str, Any], vision: dict[str, Any] | None) -> LookRequest:
    budget = float(payload.get("budget_rub", 50_000))
    budget = max(settings.budget_min_rub, min(settings.budget_max_rub, budget))
    query = payload.get("query")
    niche_raw = payload.get("niche_level")
    try:
        niche_level = int(niche_raw) if niche_raw is not None and str(niche_raw) != "" else None
    except (TypeError, ValueError):
        niche_level = None
    return LookRequest(
        style=payload.get("style", "minimal"),
        mood=payload.get("mood", "calm"),
        occasion=payload.get("occasion", "everyday"),
        season=payload.get("season", "all"),
        presentation=payload.get("presentation", "unisex"),
        height_cm=float(payload.get("height_cm", 172)),
        weight_kg=float(payload.get("weight_kg", 68)),
        budget_rub=budget,
        preferred_colors=list(payload.get("preferred_colors") or []),
        avoid_colors=list(payload.get("avoid_colors") or []),
        size=payload.get("size"),
        plan=payload.get("plan"),
        vision=vision,
        query=str(query).strip() if isinstance(query, str) and query.strip() else None,
        niche_level=niche_level,
        # Without explicit weights the engine would score everything 0.0 and
        # silently degrade to "cheapest item per slot".
        weights=settings.resolved_ranking_weights(),
    )


def build_look_result(items: list[Any], request: LookRequest) -> LookResult:
    """Собрать образ: движок ASSTYLIST, при неудаче — прежний ранжировщик.

    Режим задаётся ``FASHION_ENGINE_MODE``: ``hybrid`` (по умолчанию) — движок
    с откатом, ``engine`` — только движок, ``legacy`` — прежний ранжировщик.
    """
    mode = (settings.fashion_engine_mode or "hybrid").strip().lower()

    if not settings.fashion_engine_enabled or mode == "legacy":
        result = generate_look(items, request)
        result.diagnostics["engine"] = {
            "pipeline": "legacy-ranker",
            "enabled": False,
            "runtime_mode": mode,
        }
        return result

    try:
        return fashion_engine_service.generate_look(items, request)
    except LookGenerationError as exc:
        if mode == "engine" or not settings.fashion_engine_allow_fallback:
            raise
        result = generate_look(items, request)
        result.diagnostics["engine"] = {
            "pipeline": "legacy-ranker",
            "enabled": True,
            "runtime_mode": mode,
            "fallback": "fashion-engine-error",
            "fallback_reason": str(exc),
        }
        result.diagnostics.setdefault("warnings", []).append(
            f"Образ собран резервным ранжировщиком: {exc}"
        )
        return result


def generate_and_save(
    session: Session,
    user: User,
    payload: dict[str, Any],
    vision: dict[str, Any] | None,
    *,
    save: bool = True,
    photo_digest: str = "",
    photo_path: str = "",
    ai_provider: str = "local",
) -> Look:
    engine_request = to_engine_request(payload, vision)
    items = catalog_service.eligible_items(session)
    result = build_look_result(items, engine_request)

    look = Look(
        user_id=user.id,
        style=engine_request.style,
        mood=engine_request.mood,
        occasion=engine_request.occasion,
        season=engine_request.season,
        presentation=engine_request.presentation,
        height_cm=engine_request.height_cm,
        weight_kg=engine_request.weight_kg,
        budget_rub=engine_request.budget_rub,
        total_rub=result.total_rub,
        body_json=json.dumps(result.body.to_dict(), ensure_ascii=False),
        palette_json=json.dumps(result.palette.to_dict(), ensure_ascii=False),
        ranking_json=json.dumps(
            {
                "cohesion": result.cohesion,
                "verdict": result.verdict,
                "diagnostics": result.diagnostics,
                "engine": result.diagnostics.get("engine"),
                "query": engine_request.query,
                "weights": engine_request.weights or settings.resolved_ranking_weights(),
                "preferred_colors": engine_request.preferred_colors,
                "avoid_colors": engine_request.avoid_colors,
                "size": engine_request.size,
                "budget": {
                    "total_rub": result.total_rub,
                    "budget_rub": engine_request.budget_rub,
                    "utilization": round(result.total_rub / engine_request.budget_rub, 3)
                    if engine_request.budget_rub
                    else 0.0,
                },
            },
            ensure_ascii=False,
            default=str,
        ),
        tips_json=json.dumps(result.tips, ensure_ascii=False),
        summary=result.summary,
        score=result.score,
        photo_digest=photo_digest,
        photo_path=photo_path,
        ai_provider=ai_provider,
        engine_version=ENGINE_VERSION,
    )
    if save:
        session.add(look)
        session.flush()

    for index, item in enumerate(result.items):
        row = LookItem(
            look_id=look.id if save else 0,
            position=index,
            slot=item["slot"],
            product_id=None,
            sku=item["sku"],
            category=item["category"],
            name=item["name"],
            brand=item["brand"],
            price_rub=item["price_rub"],
            url=item["url"],
            image_url=item.get("image_url", ""),
            colors=json.dumps(item.get("colors", []), ensure_ascii=False),
            color_hexes=json.dumps(item.get("color_hexes", []), ensure_ascii=False),
            score=item["score"],
            breakdown_json=json.dumps(item.get("breakdown", {}), ensure_ascii=False),
            reasons_json=json.dumps(item.get("reasons", []), ensure_ascii=False),
            verification_status=item.get("verification_status", "verified"),
            verification_score=item.get("verification_score", 0.0),
            alternatives_json=json.dumps(item.get("alternatives", []), ensure_ascii=False),
        )
        look.items.append(row)

    if save:
        session.commit()
        session.refresh(look)
    return look


def serialize_look(look: Look) -> dict[str, Any]:
    ranking = look.loads(look.ranking_json, {})
    body = look.loads(look.body_json, {})
    palette = look.loads(look.palette_json, {})
    budget_info = ranking.get("budget", {})
    utilization = budget_info.get("utilization")
    if utilization is None:
        utilization = round(look.total_rub / look.budget_rub, 3) if look.budget_rub else 0.0

    from ..engine.options import SLOT_LABELS

    items = []
    for row in sorted(look.items, key=lambda entry: entry.position):
        # Атрибуты движка хранятся внутри того же JSON, чтобы не менять схему БД:
        # см. fashion_engine_service._engine_item_meta.
        breakdown = dict(row.breakdown())
        engine_meta = breakdown.pop("engineAttributes", None)
        items.append(
            {
                "position": row.position,
                "slot": row.slot,
                "slot_label": SLOT_LABELS.get(row.slot, row.slot),
                "sku": row.sku,
                "category": row.category,
                "name": row.name,
                "brand": row.brand,
                "price_rub": row.price_rub,
                "url": row.url,
                "image_url": row.image_url,
                "colors": row.colors_list(),
                "color_hexes": row.color_hexes_list(),
                "fit": "regular",
                "score": round(row.score, 4),
                "breakdown": breakdown,
                "engine": engine_meta or {},
                "reasons": row.reasons(),
                "verification_status": row.verification_status,
                "verification_score": round(row.verification_score, 3),
                "source": "",
                "alternatives": row.alternatives(),
            }
        )

    return {
        "id": look.id,
        "created_at": look.created_at,
        "user_id": look.user_id,
        "style": look.style,
        "mood": look.mood,
        "occasion": look.occasion,
        "season": look.season,
        "presentation": look.presentation,
        "height_cm": look.height_cm,
        "weight_kg": look.weight_kg,
        "budget_rub": look.budget_rub,
        "total_rub": look.total_rub,
        "budget_utilization": utilization,
        "score": look.score,
        "verdict": ranking.get("verdict", {}),
        "cohesion": ranking.get("cohesion", {}),
        "summary": look.summary,
        "tips": look.loads(look.tips_json, []),
        "body": body,
        "palette": palette,
        "plan": ranking.get("diagnostics", {}).get("plan", ""),
        "engine_version": look.engine_version,
        "engine": ranking.get("engine") or {},
        "diagnostics": ranking.get("diagnostics", {}),
        "items": items,
        "is_favorite": look.is_favorite,
        "version": look.version,
        "ai_provider": look.ai_provider,
        "photo_digest": look.photo_digest,
    }


def _restore_context(look: Look) -> tuple[RankingContext, dict[str, Any]]:
    ranking = look.loads(look.ranking_json, {})
    body: BodyProfile = body_from_dict(look.loads(look.body_json, {}))
    palette: PaletteProfile = palette_from_dict(look.loads(look.palette_json, {}))
    ctx = RankingContext.build(
        style=look.style,
        mood=look.mood,
        occasion=look.occasion,
        season=look.season,
        presentation=look.presentation,
        palette=palette,
        body=body,
        weights=ranking.get("weights") or settings.resolved_ranking_weights(),
        preferred_colors=ranking.get("preferred_colors") or [],
        avoid_colors=ranking.get("avoid_colors") or [],
        size=ranking.get("size"),
    )
    return ctx, ranking


def swap_slot(session: Session, look: Look, slot: str, extra_exclusions: list[str] | None = None) -> Look:
    """Replace one slot with the next best eligible candidate, keeping the budget."""
    if slot not in SLOT_CATEGORIES:
        raise LookGenerationError(f"Неизвестный слот: {slot}")

    target = next((item for item in look.items if item.slot == slot), None)
    if target is None:
        raise LookGenerationError(f"В образе нет позиции «{slot}»")

    ctx, _ranking = _restore_context(look)
    ranked, _rejected = rank_candidates(catalog_service.eligible_items(session), ctx, look.budget_rub)

    # Замена вещи тоже идёт через движок: он решает, что сильнее по эстетике
    # и вкусу, приложение по-прежнему держит бюджет и верификацию.
    if settings.fashion_engine_enabled and (settings.fashion_engine_mode or "").strip().lower() != "legacy":
        try:
            ranked = fashion_engine_service.rerank_for_slot(ranked, slot, look=look, ctx=ctx)
        except Exception:  # движок не должен ломать замену вещи
            pass

    # Exclude every SKU already in the look — including the one being replaced —
    # otherwise "swap" just hands back the same item.
    used = {item.sku for item in look.items}
    used.update(extra_exclusions or [])
    others_total = look.total_rub - target.price_rub

    pool = [s for s in ranked if s.item.category in SLOT_CATEGORIES[slot] and s.sku not in used]
    if not pool:
        raise LookGenerationError("Для этой позиции больше нет доступных замен")

    affordable = [s for s in pool if others_total + s.item.price_rub <= look.budget_rub] or pool
    chosen = affordable[0]  # already sorted best-first by rank_candidates

    target.sku = chosen.sku
    target.category = chosen.item.category
    target.name = chosen.item.name
    target.brand = chosen.item.brand
    target.price_rub = chosen.item.price_rub
    target.url = chosen.item.url
    target.image_url = chosen.item.image_url
    target.colors = json.dumps(chosen.item.colors, ensure_ascii=False)
    target.color_hexes = json.dumps(chosen.item.color_hexes, ensure_ascii=False)
    target.score = chosen.score
    target.breakdown_json = json.dumps(chosen.breakdown, ensure_ascii=False)
    target.verification_status = chosen.item.verification_status
    target.verification_score = chosen.item.verification_score

    from ..engine.explain import item_reasons

    body: BodyProfile = body_from_dict(look.loads(look.body_json, {}))
    palette: PaletteProfile = palette_from_dict(look.loads(look.palette_json, {}))
    reasons = item_reasons(
        chosen,
        {"style": look.style, "mood": look.mood, "palette_label": palette.season_label, "silhouette_ru": body.silhouette_ru},
    )
    engine_meta = chosen.breakdown.get("engineAttributes") if isinstance(chosen.breakdown, dict) else None
    if isinstance(engine_meta, dict) and engine_meta:
        reasons = [
            f"Разбор: {engine_meta.get('role_label', 'вещь образа')} · "
            f"{engine_meta.get('taste_label', '')} ({engine_meta.get('fashion_score', 0)}/100)"
        ] + reasons
    target.reasons_json = json.dumps(reasons, ensure_ascii=False)
    target.alternatives_json = json.dumps(
        [
            {"sku": alt.sku, "name": alt.item.name, "brand": alt.item.brand, "price_rub": alt.item.price_rub}
            for alt in pool[1:4]
        ],
        ensure_ascii=False,
    )

    look.total_rub = round(sum(item.price_rub for item in look.items), 2)
    look.version += 1
    ranking = look.loads(look.ranking_json, {})
    budget_block = ranking.setdefault("budget", {})
    budget_block.update(
        {
            "total_rub": look.total_rub,
            "budget_rub": look.budget_rub,
            "utilization": round(look.total_rub / look.budget_rub, 3) if look.budget_rub else 0.0,
        }
    )
    look.ranking_json = json.dumps(ranking, ensure_ascii=False, default=str)
    session.commit()
    session.refresh(look)
    return look


def list_looks(session: Session, user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    looks = (
        session.execute(
            select(Look).where(Look.user_id == user_id).order_by(Look.created_at.desc()).limit(limit)
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": look.id,
            "created_at": look.created_at,
            "style": look.style,
            "mood": look.mood,
            "occasion": look.occasion,
            "season": look.season,
            "total_rub": look.total_rub,
            "budget_rub": look.budget_rub,
            "score": look.score,
            "is_favorite": look.is_favorite,
            "items_count": len(look.items),
            "summary": look.summary,
        }
        for look in looks
    ]


def get_look(session: Session, look_id: int, user_id: int | None = None) -> Look | None:
    stmt = select(Look).where(Look.id == look_id)
    if user_id is not None:
        stmt = stmt.where(Look.user_id == user_id)
    return session.execute(stmt).scalar_one_or_none()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
