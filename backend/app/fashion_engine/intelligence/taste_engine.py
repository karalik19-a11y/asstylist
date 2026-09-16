"""TasteEngine v2 — fashion taste, niche pressure and anti-generic ranking."""

from __future__ import annotations

from dataclasses import dataclass, field

from .. import keywords as kw
from ..helpers import int_clamp
from ..types import ProductItem, UserStyleProfile


@dataclass
class TasteResult:
    fashion_score: int
    taste_category: str
    generic_score: int
    components: dict[str, float] = field(default_factory=dict)


class TasteEngine:
    def evaluate(self, item: ProductItem, profile: UserStyleProfile | dict | None = None) -> TasteResult:
        profile = profile or UserStyleProfile()
        if isinstance(profile, dict):
            profile = UserStyleProfile.from_dict(profile)
        attributes = item.fashion_attributes
        text = f"{item.name or ''} {item.brand or ''} {' '.join(item.tags or [])}".lower().replace("ё", "е")

        uniqueness = self._uniqueness(item, attributes, text)
        design_quality = self._design_quality(attributes, text)
        silhouette_strength = self._silhouette_strength(attributes)
        cultural_relevance = self._cultural_relevance(attributes)
        editorial_value = float(getattr(attributes, "editorial_relevance", 0.4) or 0.4) * 100
        styling_potential = float(getattr(attributes, "styling_potential", 50) or 50)
        niche_factor = self._niche_factor(item, attributes, text, profile)
        current_relevance = float(getattr(attributes, "current_relevance", 0.5) or 0.5) * 100
        interesting_trend = float(getattr(attributes, "interesting_trend_score", 0.3) or 0.3) * 100
        generic_factor = self._generic_factor(item, attributes, text)

        # v2 deliberately rewards current + niche signals more than generic virality.
        fashion_score = round(
            uniqueness * 0.17
            + design_quality * 0.15
            + silhouette_strength * 0.13
            + min(100.0, cultural_relevance) * 0.10
            + editorial_value * 0.11
            + styling_potential * 0.11
            + niche_factor * 0.12
            + current_relevance * 0.06
            + interesting_trend * 0.05
            - generic_factor * (0.18 + 0.10 * (profile.niche_level / 100.0))
        )

        brand = (item.brand or "").lower()
        if any(prestige in brand for prestige in kw.PRESTIGE_BRANDS):
            fashion_score += 12

        # Marketplace listings need evidence beyond a luxury name: avoid letting
        # an unverified branded listing win purely because the brand is prestigious.
        if item.source_type == "marketplace" and float(item.confidence or 0) < 0.72:
            fashion_score -= 6

        clamped = int_clamp(fashion_score)
        category = self._assign_category(clamped, generic_factor, niche_factor, attributes, text, brand)
        return TasteResult(
            fashion_score=clamped,
            taste_category=category,
            generic_score=generic_factor,
            components={
                "uniqueness": round(uniqueness, 2),
                "designQuality": round(design_quality, 2),
                "silhouetteStrength": round(silhouette_strength, 2),
                "culturalRelevance": round(min(100.0, cultural_relevance), 2),
                "editorialValue": round(editorial_value, 2),
                "stylingPotential": round(styling_potential, 2),
                "nicheFactor": round(niche_factor, 2),
                "currentRelevance": round(current_relevance, 2),
                "interestingTrend": round(interesting_trend, 2),
                "genericFactor": round(generic_factor, 2),
            },
        )

    def should_reject(self, item: ProductItem, taste: TasteResult, threshold: float = 55) -> bool:
        """Reject generic filler harder as the user's requested niche level rises."""
        threshold = threshold + max(0, 65 - 55 * (taste.generic_score / 100.0))
        return taste.generic_score > 68 and taste.fashion_score < threshold

    def _uniqueness(self, item: ProductItem, attributes, text: str) -> float:
        score = 40.0
        if float(getattr(attributes, "rarity", 0) or 0) > 70:
            score += 30
        if any(word in text for word in ("archive", "rare", "limited", "архив", "лимит", "deadstock", "reworked")):
            score += 25
        if getattr(attributes, "construction", "") == "deconstructed":
            score += 15
        if item.source_type in ("independent", "archive", "marketplace"):
            score += 8
        return min(100.0, score)

    def _design_quality(self, attributes, text: str) -> float:
        score = 45.0
        if getattr(attributes, "construction", "") in ("tailored", "deconstructed"):
            score += 20
        silhouette = list(getattr(attributes, "silhouette", []) or [])
        if {"structured", "architectural"} & set(silhouette):
            score += 15
        if any(word in text for word in ("designer", "atelier", "ателье", "handmade", "ручн")):
            score += 10
        return min(100.0, score)

    def _silhouette_strength(self, attributes) -> float:
        strong = {"oversized", "deconstructed", "structured", "elongated", "voluminous"}
        count = len(strong & set(getattr(attributes, "silhouette", []) or []))
        return min(100.0, 40 + count * 25)

    def _cultural_relevance(self, attributes) -> float:
        cultural = list(getattr(attributes, "cultural_reference", []) or [])
        return len(cultural) * 15 + (20 if getattr(attributes, "subculture", None) else 0)

    def _niche_factor(self, item: ProductItem, attributes, text: str, profile: UserStyleProfile) -> float:
        score = 30.0
        if float(getattr(attributes, "rarity", 0) or 0) > 60:
            score += 25
        if any(word in text for word in ("independent", "emerging", "niche", "нишев", "deadstock", "reworked", "archive")):
            score += 20
        if item.brand and not self._is_mass_market(item.brand):
            score += 15
        if item.source_type == "marketplace":
            score += 8
        if profile.niche_level > 70:
            score += 10
        return min(100.0, score)

    def _generic_factor(self, item: ProductItem, attributes, text: str) -> float:
        score = 20.0
        if self._is_mass_market(item.brand or ""):
            score += 50
        if any(word in text for word in ("basic", "classic fit", "regular fit", "базов", "классическ", "old money", "quiet luxury")):
            score += 20
        if "regular" in (getattr(attributes, "silhouette", []) or []) and getattr(attributes, "construction", "") == "standard":
            score += 15
        if not (getattr(attributes, "cultural_reference", []) or []) and float(getattr(attributes, "rarity", 0) or 0) < 40:
            score += 15
        return min(100.0, score)

    def _is_mass_market(self, brand: str) -> bool:
        lowered = (brand or "").lower()
        return any(mass in lowered for mass in kw.MASS_MARKET_BRANDS)

    def _assign_category(self, score: int, generic: float, niche: float, attributes, text: str, brand: str) -> str:
        if score >= 90 and (float(getattr(attributes, "rarity", 0) or 0) > 80 or "cult" in text):
            return "exceptional"
        if score >= 85 and ("archive" in text or "deadstock" in text or getattr(attributes, "historical_reference", None)):
            return "archive"
        if score >= 80 and (float(getattr(attributes, "editorial_relevance", 0) or 0) > 0.7 or "runway" in text):
            return "editorial"
        if score >= 75 and niche > 65:
            return "niche"
        if score >= 70 and not self._is_mass_market(brand):
            return "designer"
        if score >= 55 and generic < 50:
            return "interesting"
        if generic > 65:
            return "generic"
        return "interesting"


__all__ = ["TasteEngine", "TasteResult"]
