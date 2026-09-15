"""ItemValidator — порт ``src/validation/ItemValidator.js``.

Гарантирует, что в образ попадают только реальные товары с достаточной
уверенностью: имя, бренд, ссылка на источник, confidence ≥ min_confidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..types import ProductItem

VALID_CATEGORIES: tuple[str, ...] = (
    "top", "shirt", "blouse", "jacket", "coat", "blazer", "trousers", "jeans", "pants", "skirt",
    "dress", "boots", "sneakers", "shoes", "belt", "scarf", "cardigan", "knit", "sweater",
    "jumpsuit", "shorts", "leggings", "bag", "backpack", "clutch", "tote", "vest", "accessory",
)


@dataclass
class ItemValidation:
    valid: bool
    confidence: float
    reason: str | None = None


class ItemValidator:
    def __init__(self, min_confidence: float = 0.6) -> None:
        self.min_confidence = float(min_confidence)

    def validate(self, item: ProductItem | None) -> ItemValidation:
        if item is None:
            return ItemValidation(valid=False, confidence=0.0, reason="null item")
        if not item.name or len(item.name) < 3:
            return ItemValidation(valid=False, confidence=0.0, reason="missing or invalid name")
        if not item.brand or item.brand.lower() == "unknown":
            return ItemValidation(valid=False, confidence=float(item.confidence or 0.3), reason="missing brand")
        if not item.source_url or item.source_url == "unknown":
            return ItemValidation(valid=False, confidence=0.4, reason="missing sourceUrl")
        if float(item.confidence or 0) < self.min_confidence:
            return ItemValidation(valid=False, confidence=float(item.confidence or 0), reason="confidence too low")
        return ItemValidation(valid=True, confidence=float(item.confidence or 0.7))

    def filter_valid(self, items: list[ProductItem]) -> list[ProductItem]:
        return [item for item in items if self.validate(item).valid]
