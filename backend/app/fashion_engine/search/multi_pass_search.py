"""MultiPassSearch — порт ``src/search/MultiPassSearch.js``.

PASS 1 — широкий поиск по расширенным запросам.
PASS 2/3 — Fashion Intelligence → Trend → Taste → anti-generic → бюджет.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..intelligence import FashionIntelligence, TasteEngine, TrendEngine
from ..types import ProductItem, StyleReference, UserStyleProfile
from .provider import SearchContext, SearchProvider
from .query_expander import QueryExpander


@dataclass
class DiscoveryResult:
    products: list[ProductItem] = field(default_factory=list)
    references: list[StyleReference] = field(default_factory=list)
    queries_used: list[str] = field(default_factory=list)
    raw_items: int = 0
    considered: int = 0
    dropped: dict[str, int] = field(default_factory=dict)

    @property
    def dropped_total(self) -> int:
        return sum(self.dropped.values())


class MultiPassSearch:
    def __init__(self, providers: list[SearchProvider] | None = None) -> None:
        self.providers: list[SearchProvider] = list(providers or [])
        self.expander = QueryExpander()
        self.intelligence = FashionIntelligence()
        self.taste = TasteEngine()
        self.trend = TrendEngine()

    def enrich(
        self,
        items: list[ProductItem],
        profile: UserStyleProfile,
    ) -> list[ProductItem]:
        """Оценить вещи движком, даже если они не попали в пул запросов.

        Отличие порта: приложение показывает слот целиком (например, при замене
        вещи), поэтому вещь нужна с атрибутами, fashion score и taste-категорией,
        даже когда расширенные запросы её не вернули. Уже обогащённые вещи
        пропускаются — повторный прогон ничего не меняет (детерминизм).
        """
        for item in items:
            if item.fashion_attributes is not None:
                continue
            item.fashion_attributes = self.intelligence.analyze(item)
            self.trend.enrich(item)
            taste = self.taste.evaluate(item, profile)
            item.fashion_score = taste.fashion_score
            item.taste_category = taste.taste_category
            item.generic_score = taste.generic_score
            item.taste_components = taste.components
            item.item_type = "product"
        return items

    def run(
        self,
        user_query: str,
        user_profile: UserStyleProfile | dict | None = None,
        options: dict | None = None,
    ) -> DiscoveryResult:
        options = options or {}
        profile = user_profile or UserStyleProfile()
        if isinstance(profile, dict):
            profile = UserStyleProfile.from_dict(profile)

        limit_per_query = int(options.get("limit_per_query", 6))
        max_products = int(options.get("max_products", 40))
        categories: list[str] = list(options.get("categories") or [])
        max_queries = options.get("max_queries")

        queries = self.expander.expand(user_query, profile)
        if max_queries is not None:
            # Живые провайдеры (Авито): каждый расширенный запрос — это HTTP.
            # Берём первые, самые точные расширения, остальные отбрасываем.
            try:
                queries = queries[: max(1, int(max_queries))]
            except (TypeError, ValueError):
                pass
        raw_items: list[ProductItem] = []

        for query in queries:
            for provider in self.providers:
                context = SearchContext(
                    user_profile=profile,
                    limit=limit_per_query,
                    categories=categories,
                )
                try:
                    found = provider.search(query, context)
                except Exception:  # провайдер падает — пайплайн продолжается
                    found = []
                for item in found:
                    item.provider = provider.name
                    item.original_query = query
                    raw_items.append(item)

        # Ранняя дедупликация по brand::name (как в оригинале)
        seen: set[str] = set()
        unique: list[ProductItem] = []
        for item in raw_items:
            key = f"{(item.brand or '').lower()}::{(item.name or '').lower()}"
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)

        dropped = {
            "antigeneric": 0,
            "confidence": 0,
            "budget": 0,
            "duplicates": max(0, len(raw_items) - len(unique)),
        }
        enriched: list[ProductItem] = []
        for raw in unique[: max_products * 2]:
            raw.fashion_attributes = self.intelligence.analyze(raw)
            item = self.trend.enrich(raw)

            taste = self.taste.evaluate(item, profile)
            item.fashion_score = taste.fashion_score
            item.taste_category = taste.taste_category
            item.generic_score = taste.generic_score
            item.taste_components = taste.components

            if self.taste.should_reject(item, taste) and profile.niche_level > 50:
                dropped["antigeneric"] += 1
                continue
            if float(item.confidence or 0) < 0.55:
                dropped["confidence"] += 1
                continue
            if profile.budget_max and item.price and item.price > profile.budget_max * 1.15:
                if item.fashion_score < 85:
                    dropped["budget"] += 1
                    continue

            item.item_type = "product"
            enriched.append(item)

        enriched.sort(key=lambda entry: (-(entry.fashion_score or 0), entry.id))
        products = enriched[:max_products]

        return DiscoveryResult(
            products=products,
            references=[],
            queries_used=queries,
            raw_items=len(raw_items),
            considered=len(unique),
            dropped=dropped,
        )
