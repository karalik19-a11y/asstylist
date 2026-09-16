"""Fashion Ranking Engine.

Deterministic, explainable, dependency-free scoring. Every item gets a
breakdown so the UI can show *why* it was chosen.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .body import BodyProfile, silhouette_fit_score
from .colors import COLORS, harmony_score
from .options import formality_for_occasion, style_by_id
from .palette import PaletteProfile

ENGINE_VERSION = "1.0.0"

#: Baseline weights. Every key must appear in the item breakdown, and the values
#: are normalised at build time so they always sum to 1.0.
DEFAULT_WEIGHTS: dict[str, float] = {
    "style": 0.28,
    "mood": 0.15,
    "silhouette": 0.16,
    "color": 0.15,
    "formality": 0.08,
    "season": 0.05,
    "value": 0.08,
    "verification": 0.05,
}


def default_weights() -> dict[str, float]:
    total = sum(DEFAULT_WEIGHTS.values()) or 1.0
    return {key: value / total for key, value in DEFAULT_WEIGHTS.items()}

#: Which style tags count as a partial match for a requested style.
STYLE_AFFINITY: dict[str, set[str]] = {
    "minimal": {"old_money", "business_casual", "avantgarde", "techwear", "office_siren"},
    "old_money": {"minimal", "business_casual", "romantic", "dark_academia"},
    "streetwear": {"athleisure", "techwear", "grunge", "y2k", "indie_sleaze"},
    "business_casual": {"minimal", "old_money", "office_siren", "dark_academia"},
    "techwear": {"streetwear", "minimal", "athleisure", "gorpcore"},
    "romantic": {"boho", "old_money", "minimal", "balletcore"},
    "athleisure": {"streetwear", "techwear", "minimal", "gorpcore", "y2k"},
    "grunge": {"streetwear", "boho", "avantgarde", "indie_sleaze"},
    "boho": {"romantic", "grunge", "minimal"},
    "avantgarde": {"minimal", "techwear", "grunge"},
    "office_siren": {"business_casual", "old_money", "minimal", "y2k"},
    "gorpcore": {"techwear", "athleisure", "streetwear"},
    "y2k": {"streetwear", "indie_sleaze", "athleisure", "office_siren"},
    "indie_sleaze": {"grunge", "y2k", "streetwear", "avantgarde"},
    "dark_academia": {"old_money", "business_casual", "minimal", "romantic"},
    "balletcore": {"romantic", "minimal", "old_money", "athleisure"},
}

MOOD_AFFINITY: dict[str, set[str]] = {
    "confident": {"bold", "elegant", "energetic"},
    "calm": {"cozy", "elegant", "mysterious"},
    "playful": {"energetic", "bold", "cozy"},
    "bold": {"confident", "energetic", "mysterious"},
    "cozy": {"calm", "playful", "romantic"},
    "elegant": {"confident", "calm", "mysterious"},
    "energetic": {"bold", "playful", "confident"},
    "mysterious": {"elegant", "bold", "calm"},
}

SEASON_ADJACENCY: dict[str, set[str]] = {
    "spring": {"summer", "autumn", "all"},
    "summer": {"spring", "all"},
    "autumn": {"spring", "winter", "all"},
    "winter": {"autumn", "all"},
    "all": {"spring", "summer", "autumn", "winter"},
}


@dataclass
class CatalogItem:
    """A verified catalog row flattened into engine-friendly shape."""

    product_id: int
    sku: str
    category: str
    name: str
    brand: str
    price_rub: float
    url: str
    image_url: str
    colors: list[str]
    color_hexes: list[str]
    styles: list[str]
    moods: list[str]
    silhouettes: list[str]
    gendered: list[str]
    seasons: list[str]
    sizes: list[str]
    fit: str
    formality: int
    rating: float
    reviews_count: int
    verification_status: str
    verification_score: float
    source: str


@dataclass
class RankingContext:
    style: str
    mood: str
    occasion: str
    season: str
    presentation: str
    palette: PaletteProfile
    body: BodyProfile
    weights: dict[str, float]
    preferred_colors: list[str] = field(default_factory=list)
    avoid_colors: list[str] = field(default_factory=list)
    size: str | None = None
    category_medians: dict[str, float] = field(default_factory=dict)
    target_formality: int = 2

    @classmethod
    def build(
        cls,
        *,
        style: str,
        mood: str,
        occasion: str,
        season: str,
        presentation: str,
        palette: PaletteProfile,
        body: BodyProfile,
        weights: dict[str, float],
        preferred_colors: list[str] | None = None,
        avoid_colors: list[str] | None = None,
        size: str | None = None,
        category_medians: dict[str, float] | None = None,
    ) -> "RankingContext":
        return cls(
            style=style,
            mood=mood,
            occasion=occasion,
            season=season,
            presentation=presentation,
            palette=palette,
            body=body,
            weights=weights or default_weights(),
            preferred_colors=preferred_colors or [],
            avoid_colors=avoid_colors or [],
            size=size,
            category_medians=category_medians or {},
            target_formality=formality_for_occasion(occasion),
        )


@dataclass
class ScoredItem:
    item: CatalogItem
    score: float
    breakdown: dict[str, float]

    @property
    def sku(self) -> str:
        return self.item.sku


def _style_match(item: CatalogItem, style: str) -> float:
    if not item.styles:
        return 0.35
    if style in item.styles:
        return 1.0
    if set(item.styles) & STYLE_AFFINITY.get(style, set()):
        return 0.55
    return 0.12


def _mood_match(item: CatalogItem, mood: str) -> float:
    if not item.moods:
        return 0.4
    if mood in item.moods:
        return 1.0
    if set(item.moods) & MOOD_AFFINITY.get(mood, set()):
        return 0.6
    return 0.2


def _season_match(item: CatalogItem, season: str) -> float:
    if not item.seasons or season == "all" or "all" in item.seasons:
        return 1.0
    if season in item.seasons:
        return 1.0
    if set(item.seasons) & SEASON_ADJACENCY.get(season, set()):
        return 0.65
    return 0.15


def _value_score(item: CatalogItem, category_medians: dict[str, float]) -> float:
    rating_norm = max(0.0, min(1.0, item.rating / 5.0))
    review_norm = max(0.0, min(1.0, math.log10(max(1, item.reviews_count)) / 3.0))
    median = category_medians.get(item.category, 0.0)
    if median > 0:
        ratio = item.price_rub / median
        price_fairness = 1.0 if ratio <= 1.0 else max(0.0, 1.0 - (ratio - 1.0))
    else:
        price_fairness = 0.7
    return round(0.5 * rating_norm + 0.25 * review_norm + 0.25 * price_fairness, 3)


def _color_match(item: CatalogItem, ctx: RankingContext) -> float:
    base = harmony_score(item.colors, list(ctx.palette.recommended), list(ctx.palette.avoid))
    if ctx.preferred_colors and set(item.colors) & set(ctx.preferred_colors):
        base = max(base, 0.95)
    return round(base, 3)


def hard_exclusions(item: CatalogItem, ctx: RankingContext, budget_rub: float) -> list[str]:
    """Reasons this item can never appear in the look."""
    reasons: list[str] = []
    if item.price_rub <= 0:
        reasons.append("invalid_price")
    if item.price_rub > budget_rub:
        reasons.append("over_budget")
    if item.verification_status not in ("verified", "warning"):
        reasons.append("not_verified")
    if ctx.avoid_colors and set(item.colors) <= set(ctx.avoid_colors):
        reasons.append("avoided_colors")
    if ctx.size and item.sizes and ctx.size.upper() not in [s.upper() for s in item.sizes]:
        reasons.append("size_unavailable")
    if ctx.presentation == "masculine" and ("feminine" in item.gendered or item.category == "dress"):
        reasons.append("presentation_mismatch")
    return reasons


def score_item(item: CatalogItem, ctx: RankingContext) -> ScoredItem:
    breakdown = {
        "style": _style_match(item, ctx.style),
        "mood": _mood_match(item, ctx.mood),
        "silhouette": silhouette_fit_score(item.fit, item.silhouettes, ctx.body),
        "color": _color_match(item, ctx),
        "formality": round(max(0.0, 1.0 - abs(item.formality - ctx.target_formality) / 4.0), 3),
        "season": _season_match(item, ctx.season),
        "value": _value_score(item, ctx.category_medians),
        "verification": round(max(0.0, min(1.0, item.verification_score)), 3),
    }
    total = sum(breakdown[key] * weight for key, weight in ctx.weights.items() if key in breakdown)
    return ScoredItem(item=item, score=round(total, 4), breakdown=breakdown)


def rank_candidates(
    items: list[CatalogItem],
    ctx: RankingContext,
    budget_rub: float,
) -> tuple[list[ScoredItem], list[dict[str, Any]]]:
    """Score everything, split into usable candidates and rejected rows."""
    scored: list[ScoredItem] = []
    rejected: list[dict[str, Any]] = []
    for item in items:
        exclusions = hard_exclusions(item, ctx, budget_rub)
        if exclusions:
            rejected.append({"sku": item.sku, "name": item.name, "reasons": exclusions})
            continue
        scored.append(score_item(item, ctx))
    scored.sort(key=lambda s: (-s.score, s.item.price_rub, s.item.sku))
    return scored, rejected


# ---------------------------------------------------------------------------
# Look-level cohesion
# ---------------------------------------------------------------------------


def _pairwise_color_cohesion(items: list[ScoredItem]) -> float:
    if len(items) < 2:
        return 1.0
    pairs = 0
    total = 0.0
    for i, a in enumerate(items):
        for b in items[i + 1 :]:
            pairs += 1
            total += harmony_score(a.item.colors, b.item.colors, [])
    return round(total / pairs, 3) if pairs else 1.0


def look_cohesion(items: list[ScoredItem], ctx: RankingContext) -> dict[str, float]:
    if not items:
        return {"color": 0.0, "style": 0.0, "formality": 0.0, "palette": 0.0, "overall": 0.0}

    color = _pairwise_color_cohesion(items)

    style_hits = sum(1 for s in items if _style_match(s.item, ctx.style) >= 0.55)
    style = round(style_hits / len(items), 3)

    formalities = [s.item.formality for s in items]
    mean = sum(formalities) / len(formalities)
    variance = sum((f - mean) ** 2 for f in formalities) / len(formalities)
    formality = round(max(0.0, 1.0 - math.sqrt(variance) / 2.0), 3)

    palette = round(sum(s.breakdown.get("color", 0.0) for s in items) / len(items), 3)

    overall = round(0.35 * color + 0.25 * style + 0.2 * formality + 0.2 * palette, 3)
    return {"color": color, "style": style, "formality": formality, "palette": palette, "overall": overall}


def look_score(items: list[ScoredItem], cohesion: dict[str, float]) -> float:
    if not items:
        return 0.0
    avg_item = sum(s.score for s in items) / len(items)
    return round(100 * (0.62 * avg_item + 0.38 * cohesion.get("overall", 0.0)), 1)


def style_verdict(score: float) -> dict[str, str]:
    if score >= 88:
        return {"grade": "A", "title": "Образ уровня стилиста", "note": "Собрано цельно: палитра, силуэт и повод совпали."}
    if score >= 78:
        return {"grade": "B", "title": "Сильный образ", "note": "Почти идеально — один-два элемента можно усилить."}
    if score >= 65:
        return {"grade": "C", "title": "Рабочий образ", "note": "Базово хорошо, но есть заметный разброс по стилю."}
    return {"grade": "D", "title": "Требует правок", "note": "Стоит поменять пару вещей — нажмите «Заменить»."}


def palette_from_style(style: str) -> list[str]:
    return list(style_by_id(style).get("palette_hint", []))


def describe_colors(color_ids: list[str]) -> str:
    names = [COLORS[cid].ru for cid in color_ids if cid in COLORS]
    return ", ".join(names[:3]) if names else "нейтральная гамма"
