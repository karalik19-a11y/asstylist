"""MockRealProductProvider — порт ``src/search/providers/MockRealProductProvider.js``.

Справочник архетипов реальных дизайнерских вещей (Ann Demeulemeester,
Rick Owens, Margiela, Yohji…). В asStylist включается только явным флагом
``FASHION_ENGINE_ENABLE_MOCK=true`` — по умолчанию поиск идёт по каталогу
приложения, а этот провайдер остаётся для сравнения поведения с оригиналом.

``randomUUID()`` заменён на детерминированный ``stable_id``.
"""

from __future__ import annotations

from ...helpers import stable_id
from ...types import ProductItem
from ..provider import SearchContext, SearchProvider, ValidationOutcome

#: (name, brand, category, price, currency, source_type, availability, tags)
_REAL_CATALOG: tuple[tuple, ...] = (
    ("Sheer Viscose Long Sleeve Top", "Ann Demeulemeester", "top", 420, "EUR", "designer", "available", ["sheer", "transparent", "black", "long sleeve", "romantic", "archive"]),
    ("Mesh Layering Top", "Rick Owens", "top", 590, "EUR", "designer", "available", ["mesh", "sheer", "black", "layering", "industrial", "dark"]),
    ("Deconstructed Sheer Shirt", "Comme des Garçons Homme Plus", "shirt", 680, "USD", "designer", "limited", ["sheer", "deconstructed", "asymmetric", "avant-garde", "transparent"]),
    ("Transparent Organza Blouse", "Yohji Yamamoto", "blouse", 890, "EUR", "designer", "available", ["sheer", "organza", "black", "oversized", "romantic", "archive"]),
    ("Leather Biker Jacket (Archive)", "Helmut Lang", "jacket", 1450, "USD", "archive", "limited", ["leather", "black", "biker", "archive", "90s", "industrial"]),
    ("Oversized Wool Coat", "Balenciaga", "coat", 3200, "EUR", "designer", "available", ["oversized", "wool", "black", "volume", "coat", "contemporary"]),
    ("Deconstructed Tailored Blazer", "Maison Margiela", "blazer", 1650, "EUR", "designer", "available", ["deconstructed", "blazer", "tailored", "black", "archive", "minimal"]),
    ("Wide Leg Wool Trousers", "Lemaire", "trousers", 480, "EUR", "designer", "available", ["wide leg", "wool", "black", "minimal", "contemporary"]),
    ("Distressed Black Denim", "Undercover", "jeans", 520, "USD", "designer", "available", ["denim", "distressed", "black", "raw", "industrial"]),
    ("Leather Cargo Pants", "Julius", "trousers", 980, "EUR", "niche", "limited", ["leather", "cargo", "black", "industrial", "niche", "dark"]),
    ("Geobasket Sneakers", "Rick Owens", "sneakers", 1100, "EUR", "designer", "available", ["sneakers", "black", "leather", "industrial", "cult"]),
    ("Tabi Boots", "Maison Margiela", "boots", 990, "EUR", "designer", "available", ["boots", "tabi", "black", "leather", "cult", "archive"]),
    ("Combat Boots", "Ann Demeulemeester", "boots", 750, "EUR", "designer", "available", ["boots", "combat", "black", "leather", "romantic", "industrial"]),
    ("Leather Belt with Silver Hardware", "Chrome Hearts", "belt", 680, "USD", "cult", "limited", ["belt", "leather", "silver", "cult", "dark"]),
    ("Sheer Knit Cardigan", "Issey Miyake", "cardigan", 620, "EUR", "designer", "available", ["sheer", "knit", "cardigan", "layering", "experimental"]),
    ("Archive Military Jacket", "Ralph Lauren RRL", "jacket", 890, "USD", "archive", "limited", ["military", "jacket", "archive", "utilitarian", "industrial"]),
    ("Asymmetric Draped Top", "Rick Owens Lilies", "top", 480, "EUR", "designer", "available", ["asymmetric", "draped", "black", "sheer", "romantic", "dark"]),
    ("Heavy Wool Scarf", "Acne Studios", "scarf", 220, "EUR", "contemporary", "available", ["scarf", "wool", "black", "minimal", "layering"]),
)

_CONFIDENCE = {"designer": 0.92, "archive": 0.85, "niche": 0.82, "cult": 0.8, "independent": 0.78}


class MockRealProductProvider(SearchProvider):
    name = "mock-real-catalog"

    def search(self, query: str, context: SearchContext) -> list[ProductItem]:
        normalized = (query or "").lower()
        limit = int(context.limit or 8)
        niche = context.niche_level

        scored: list[tuple[float, tuple]] = []
        for row in _REAL_CATALOG:
            name, brand, category, _price, _currency, source_type, _availability, tags = row
            text = f"{name} {brand} {' '.join(tags)}".lower()
            score = 0.0
            for token in normalized.split():
                if len(token) > 2 and token in text:
                    score += 12
            for tag in tags:
                if tag in normalized:
                    score += 18
            if niche >= 75 and (source_type in ("niche", "archive") or "cult" in tags):
                score += 15
            if category in normalized:
                score += 10
            if score > 8:
                scored.append((score, row))

        scored.sort(key=lambda pair: (-pair[0], pair[1][0]))
        items: list[ProductItem] = []
        for _score, row in scored[:limit]:
            name, brand, category, price, currency, source_type, availability, tags = row
            items.append(
                ProductItem(
                    id=stable_id(brand, name, prefix="mock_"),
                    name=name,
                    brand=brand,
                    category=category,
                    price=float(price),
                    currency=currency,
                    image="",
                    source_url=f"https://example.invalid/{stable_id(brand, name, prefix='')}",
                    source_type=source_type,
                    availability=availability,
                    confidence=_CONFIDENCE.get(source_type, 0.78),
                    tags=list(tags),
                    description=" ".join(tags),
                )
            )
        return items

    def validate_item(self, item: ProductItem) -> ValidationOutcome:
        return ValidationOutcome(valid=True, confidence=float(item.confidence or 0.85))
