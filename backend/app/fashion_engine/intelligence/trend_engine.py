"""TrendEngine v2 — freshness-aware fashion intelligence.

The engine distinguishes mass visibility from fashion relevance. Social signals
are corroborated across TikTok, Pinterest, Instagram and Reddit adapters when
available; the committed radar is a refreshable September 2026 seed.
"""

from __future__ import annotations

from .. import keywords as kw
from .. import lexicon
from ..types import ProductItem
from .trend_radar_v2 import RADAR_VERSION, CURRENT_SIGNALS, radar_for, source_diversity_score

_THESIS_TRIGGERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Modern Craftsman", ("workwear", "chore coat", "field jacket", "barn jacket", "американск")),
    ("Leather Weather", ("leather", "кож", "moto", "косух")),
    ("Broken-down Prep", ("surf prep", "ivy", "prep", "boat shoe", "американск")),
    ("Romantic Menswear", ("romantic", "романт", "drape", "драп", "sheer", "прозрач", "lace", "кружев")),
    ("Military Romance", ("military", "милитари", "военн", "victorian", "викториан")),
    ("Archive Reconstruction", ("archive", "архив", "deadstock", "reworked", "rework", "deconstructed", "деконстру")),
    ("Technical Romantic", ("technical", "techwear", "техно", "nylon", "нейлон", "mesh", "сетк")),
    ("90s Americana Recut", ("americana", "90s", "plaid", "клетк", "frontier", "workwear")),
    ("Accessory-first Styling", ("chain", "цеп", "cuff", "браслет", "charm", "брелок", "pins", "значк")),
    ("Dusty Pink Accent", ("pink", "розов", "rose", "пыльно-розов")),
    ("Sport Couture", ("sport", "спорт", "track", "football", "racket", "retro trainer")),
    # Kept as fallback language, but intentionally lower priority in niche mode.
    ("Quiet Luxury Tailoring", ("cashmere", "кашемир", "quiet luxury", "тих", "camel")),
    ("Minimal Precision", ("minimal", "минимал", "clean lines", "лаконич", "monochrome", "монохром")),
    ("Industrial Romanticism", ("sheer", "прозрач", "сетк", "industrial", "индустриальн")),
    ("Transparent Layering", ("sheer", "прозрач", "сетк", "mesh")),
    ("Deconstructed 90s Minimalism", ("deconstructed", "деконстру", "асимметр", "raw", "90s")),
    ("Neo-Gothic Editorial", ("black", "черн", "leather", "кож", "velvet", "бархат", "gothic", "готич")),
    ("Post-Punk Archive", ("black", "черн", "punk", "панк", "archive", "архив")),
    ("Archive Revival", ("archive", "архив", "vintage", "винтаж")),
    ("Exaggerated Volume", ("oversized", "оверсайз", "volume", "объемн")),
)


class TrendEngine:
    def __init__(self) -> None:
        self.emerging_aesthetics = list(kw.EMERGING_AESTHETICS)
        self.rising_silhouettes = list(kw.RISING_SILHOUETTES)
        self.recurring_materials = list(kw.RECURRING_MATERIALS)
        self.radar_version = RADAR_VERSION

    def enrich(self, item: ProductItem) -> ProductItem:
        """Add trend relevance while penalising stale/generic aesthetics."""
        attributes = item.fashion_attributes
        if attributes is None:
            return item
        text = f"{item.name or ''} {item.brand or ''} {attributes.aesthetic or ''} {' '.join(item.tags or [])}".lower().replace("ё", "е")

        trend_relevance = 0.30
        interesting = 0.28
        popular = 0.20
        radar = radar_for(text, niche_level=80)

        for row in radar[:5]:
            corroboration = source_diversity_score(row["sources"])
            contribution = row["score"] * corroboration
            trend_relevance = max(trend_relevance, contribution)
            interesting = max(interesting, contribution * (0.72 + 0.28 * row["niche"]))
            if not row["avoidAsGeneric"]:
                popular = max(popular, row["score"] * 0.85)

        for silhouette in self.rising_silhouettes:
            if silhouette.lower() in text or silhouette.split(" ")[0] in text:
                trend_relevance += 0.10
                interesting += 0.08

        for material in self.recurring_materials:
            if material.split(" ")[0] in text:
                trend_relevance += 0.06

        if getattr(attributes, "historical_reference", None) or item.source_type in ("archive", "marketplace"):
            interesting += 0.10

        attributes.trend_relevance = min(1.0, round(trend_relevance, 3))
        attributes.interesting_trend_score = min(1.0, round(interesting, 3))
        attributes.popular_trend_score = min(1.0, round(popular, 3))
        attributes.current_relevance = min(1.0, round(interesting * 0.82 + popular * 0.18, 3))
        return item

    def suggest_theses(self, items: list[ProductItem], user_query: str) -> list[str]:
        query_theses = set(self.theses_from_query(user_query))
        pool_text = " ".join(f"{item.name} {item.brand} {' '.join(item.tags)}" for item in items)
        pool_text = f"{pool_text} {(user_query or '')}".lower().replace("ё", "е")

        radar = radar_for(pool_text, niche_level=80)
        from_radar = [row["label"] for row in radar[:6]]
        from_query: list[str] = []
        from_pool: list[str] = []
        for thesis, triggers in _THESIS_TRIGGERS:
            if thesis in query_theses:
                from_query.append(thesis)
            elif any(trigger in pool_text for trigger in triggers):
                from_pool.append(thesis)

        theses = from_query + from_radar + from_pool
        if not theses:
            theses = ["Contemporary Editorial", "Refined Utilitarian"]
        return list(dict.fromkeys(theses))

    def theses_from_query(self, user_query: str) -> list[str]:
        query_text = (user_query or "").lower().replace("ё", "е")
        tokens = lexicon.tokenize(query_text)
        found: list[str] = []
        for thesis, triggers in _THESIS_TRIGGERS:
            if any(kw.keyword_hit(query_text, tokens, trigger) for trigger in triggers):
                found.append(thesis)
        return found


__all__ = ["TrendEngine"]
