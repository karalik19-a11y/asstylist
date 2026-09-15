"""ProductIdentityResolver — порт ``src/validation/ProductIdentityResolver.js``.

Один и тот же товар, пришедший из нескольких источников, схлопывается в одну
позицию: ключ ``brand::name``, победитель — с большим confidence/fashionScore.
"""

from __future__ import annotations

import re

from ..types import ProductItem

#: Unicode-aware: в оригинале регулярка была латиница-онли, из-за чего все
#: русскоязычные названия схлопывались в пустую строку и вещи разных
#: категорий одного бренда считались дублями.
_NON_WORD = re.compile(r"[^\w]", re.UNICODE)


class ProductIdentityResolver:
    def identity_key(self, item: ProductItem) -> str:
        brand = _NON_WORD.sub("", (item.brand or "unknown").lower())
        name = _NON_WORD.sub(" ", (item.name or "").lower())
        words = [word for word in name.split() if len(word) > 2][:5]
        return f"{brand}::{''.join(words)}"

    def resolve(self, items: list[ProductItem]) -> list[ProductItem]:
        resolved: dict[str, ProductItem] = {}
        for item in items:
            key = self.identity_key(item)
            current = resolved.get(key)
            if current is None or self._score(item) > self._score(current):
                resolved[key] = item
        return list(resolved.values())

    @staticmethod
    def _score(item: ProductItem) -> float:
        bonus = 10 if item.source_type == "designer" else 0
        return float(item.confidence or 0) * 100 + float(item.fashion_score or 0) + bonus
