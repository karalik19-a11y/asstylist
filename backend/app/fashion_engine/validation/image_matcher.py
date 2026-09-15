"""ImageMatcher — порт ``src/validation/ImageMatcher.js``.

Эвристическая сверка названия/тегов с заявленными визуальными признаками
(в проде здесь были бы vision-модели). Возвращает consistency 0…1.
"""

from __future__ import annotations

from ..types import ProductItem

_COLORS: tuple[str, ...] = ("black", "white", "grey", "navy", "beige", "brown", "olive", "red", "blue")


class ImageMatcher:
    def check_consistency(self, item: ProductItem) -> float:
        name = (item.name or "").lower()
        tags = [str(tag).lower() for tag in (item.tags or [])]
        attributes = item.fashion_attributes
        score = 0.7

        claimed_color = (getattr(attributes, "color", "") or self._extract_color(name) or "").lower()
        if claimed_color and claimed_color != "unknown":
            if claimed_color in name or claimed_color in tags:
                score += 0.1

        if any(word in name for word in ("sheer", "transparent", "mesh")):
            material = getattr(attributes, "material", "") if attributes else ""
            if material == "sheer" or "sheer" in tags or "mesh" in tags or "прозрач" in name:
                score += 0.1
            else:
                score -= 0.25

        category = (item.category or "").lower()
        if category and category.split(" ")[0] in name:
            score += 0.05

        return max(0.0, min(1.0, round(score, 3)))

    def should_reject(self, item: ProductItem, threshold: float = 0.45) -> bool:
        return self.check_consistency(item) < threshold

    @staticmethod
    def _extract_color(text: str) -> str | None:
        for color in _COLORS:
            if color in text:
                return color
        return None
