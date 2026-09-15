"""OutfitScorer — порт ``src/outfit/OutfitScorer.js``.

Многомерная оценка образа: совместимость силуэтов, гармония цвета,
баланс пропорций, фактуры, логика слоёв, визуальная иерархия, оригинальность,
модовая релевантность и цельность. Итог — 0…100.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..types import OutfitCandidate, ProductItem, UserStyleProfile


@dataclass
class OutfitScore:
    outfit_score: float
    breakdown: dict[str, float] = field(default_factory=dict)


class OutfitScorer:
    def score(self, outfit: OutfitCandidate, user_profile: UserStyleProfile | dict | None = None) -> OutfitScore:
        profile = user_profile or UserStyleProfile()
        if isinstance(profile, dict):
            profile = UserStyleProfile.from_dict(profile)
        items = outfit.items or []
        if len(items) < 2:
            return OutfitScore(outfit_score=0.0, breakdown={})

        breakdown = {
            "silhouetteCompatibility": self._silhouette_compatibility(items),
            "colorHarmony": self._color_harmony(items),
            "proportionBalance": self._proportion_balance(items),
            "textureCompatibility": self._texture_compatibility(items),
            "layeringLogic": self._layering_logic(items),
            "visualHierarchy": self._visual_hierarchy(items),
            "originality": self._originality(items),
            "fashionRelevance": self._fashion_relevance(items),
            "cohesion": self._cohesion(items, outfit.styling_thesis),
            "wearability": self._wearability(items, profile),
        }

        outfit_score = round(
            breakdown["silhouetteCompatibility"] * 0.16
            + breakdown["colorHarmony"] * 0.12
            + breakdown["proportionBalance"] * 0.13
            + breakdown["textureCompatibility"] * 0.08
            + breakdown["layeringLogic"] * 0.10
            + breakdown["visualHierarchy"] * 0.12
            + breakdown["originality"] * 0.12
            + breakdown["fashionRelevance"] * 0.09
            + breakdown["cohesion"] * 0.08
        )
        return OutfitScore(outfit_score=max(0.0, min(100.0, float(outfit_score))), breakdown=breakdown)

    # ─── метрики ──────────────────────────────────────────────────────
    @staticmethod
    def _silhouettes(item: ProductItem) -> list[str]:
        return list(getattr(item.fashion_attributes, "silhouette", []) or ["regular"])

    def _silhouette_compatibility(self, items: list[ProductItem]) -> float:
        silhouettes = [entry for item in items for entry in self._silhouettes(item)]
        has_volume = any(entry in ("oversized", "voluminous", "structured") for entry in silhouettes)
        has_fitted = any(entry in ("fitted", "slim") for entry in silhouettes)
        score = 60.0
        if has_volume:
            score += 20
        if has_volume and has_fitted:
            score += 15
        return min(100.0, score)

    def _color_harmony(self, items: list[ProductItem]) -> float:
        colors = [
            item.fashion_attributes.color
            for item in items
            if item.fashion_attributes and item.fashion_attributes.color not in (None, "", "unknown")
        ]
        if not colors:
            return 50.0
        unique = len(set(colors))
        if unique <= 2:
            return 90.0
        if unique == 3:
            return 75.0
        return 55.0

    def _proportion_balance(self, items: list[ProductItem]) -> float:
        def has(words: tuple[str, ...]) -> bool:
            return any(any(word in (item.category or "").lower() for word in words) for item in items)

        score = 40.0
        if has(("top", "shirt", "blouse", "jacket", "coat", "blazer", "knit", "cardigan", "sweater")):
            score += 20
        if has(("trouser", "jean", "pant", "skirt", "short")):
            score += 20
        if has(("boot", "sneaker", "shoe")):
            score += 15
        return min(100.0, score)

    def _texture_compatibility(self, items: list[ProductItem]) -> float:
        textures = [
            (getattr(item.fashion_attributes, "texture", "") or getattr(item.fashion_attributes, "material", ""))
            for item in items
            if item.fashion_attributes
        ]
        textures = [texture for texture in textures if texture]
        has_sheer = any(texture in ("sheer", "fluid") for texture in textures)
        has_heavy = any(texture in ("heavy", "textured") for texture in textures)
        if has_sheer and has_heavy:
            return 92.0
        if len(set(textures)) >= 2:
            return 80.0
        return 65.0

    def _layering_logic(self, items: list[ProductItem]) -> float:
        layers = [
            item
            for item in items
            if any(word in (item.category or "").lower() for word in ("coat", "jacket", "cardigan", "blazer"))
            or getattr(item.fashion_attributes, "layering_potential", "") == "high"
        ]
        if layers and len(items) >= 3:
            return 85.0
        return 60.0

    def _visual_hierarchy(self, items: list[ProductItem]) -> float:
        scores = sorted((float(item.fashion_score or 50) for item in items), reverse=True)
        top = scores[0]
        second = scores[1] if len(scores) > 1 else 0.0
        if top - second > 12:
            return 90.0
        if top > 80:
            return 75.0
        return 55.0

    def _originality(self, items: list[ProductItem]) -> float:
        average = sum(float(item.fashion_score or 50) for item in items) / len(items)
        niche_count = len(
            [
                item
                for item in items
                if item.taste_category in ("niche", "archive", "editorial", "cult", "exceptional")
            ]
        )
        return min(100.0, average * 0.6 + niche_count * 12)

    def _fashion_relevance(self, items: list[ProductItem]) -> float:
        average = sum(
            float(getattr(item.fashion_attributes, "current_relevance", 0.5) or 0.5) * 100 for item in items
        ) / len(items)
        return round(average)

    def _cohesion(self, items: list[ProductItem], thesis: str) -> float:
        if not thesis:
            return 60.0
        thesis_words = thesis.lower().split()
        matches = 0
        for item in items:
            text = f"{item.name} {item.brand} {' '.join(item.tags or [])}".lower().replace("ё", "е")
            cultural = list(getattr(item.fashion_attributes, "cultural_reference", []) or [])
            if any(word in text or any(word in reference for reference in cultural) for word in thesis_words):
                matches += 1
        return min(100.0, 50 + (matches / len(items)) * 50)

    def _wearability(self, items: list[ProductItem], profile: UserStyleProfile) -> float:
        experimental = len([item for item in items if float(item.fashion_score or 0) > 90 or item.taste_category == "exceptional"])
        if profile.niche_level < 60 and experimental > 2:
            return 55.0
        return 80.0
