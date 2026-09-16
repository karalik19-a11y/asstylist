"""MultiPassSearch v2 — query expansion + freshness/niche-aware discovery."""

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
    def dropped_total(self) -> int: return sum(self.dropped.values())

class MultiPassSearch:
    def __init__(self, providers: list[SearchProvider] | None = None) -> None:
        self.providers = list(providers or [])
        self.expander = QueryExpander()
        self.intelligence = FashionIntelligence()
        self.taste = TasteEngine()
        self.trend = TrendEngine()

    def enrich(self, items: list[ProductItem], profile: UserStyleProfile) -> list[ProductItem]:
        for item in items:
            if item.fashion_attributes is not None: continue
            item.fashion_attributes = self.intelligence.analyze(item)
            self.trend.enrich(item)
            taste = self.taste.evaluate(item, profile)
            item.fashion_score, item.taste_category, item.generic_score = taste.fashion_score, taste.taste_category, taste.generic_score
            item.taste_components = taste.components
            item.item_type = "product"
        return items

    def run(self, user_query: str, user_profile: UserStyleProfile | dict | None = None, options: dict | None = None) -> DiscoveryResult:
        options = options or {}
        profile = user_profile if isinstance(user_profile, UserStyleProfile) else UserStyleProfile.from_dict(user_profile or {})
        limit_per_query = max(1, int(options.get("limit_per_query", 8)))
        max_products = max(3, int(options.get("max_products", 48)))
        categories = list(options.get("categories") or [])
        max_queries = options.get("max_queries")
        niche_floor = int(options.get("niche_floor", 55))

        queries = self.expander.expand(user_query, profile)
        if max_queries is not None:
            try: queries = queries[:max(1, int(max_queries))]
            except (TypeError, ValueError): pass

        raw_items: list[ProductItem] = []
        for query in queries:
            for provider in self.providers:
                context = SearchContext(user_profile=profile, limit=limit_per_query, categories=categories)
                try: found = provider.search(query, context)
                except Exception: found = []
                for item in found:
                    item.provider = provider.name
                    item.original_query = query
                    raw_items.append(item)

        seen: set[str] = set(); unique: list[ProductItem] = []
        for item in raw_items:
            # Prefer stable listing IDs/URLs over brand+name: two sellers can list
            # the same garment and still have materially different condition/price.
            key = str(item.source_url or item.id or f"{item.brand}::{item.name}").lower()
            if key in seen: continue
            seen.add(key); unique.append(item)

        dropped = {"antigeneric": 0, "confidence": 0, "budget": 0, "stale": 0, "duplicates": max(0, len(raw_items) - len(unique))}
        enriched: list[ProductItem] = []
        for raw in unique[: max_products * 3]:
            raw.fashion_attributes = self.intelligence.analyze(raw)
            item = self.trend.enrich(raw)
            taste = self.taste.evaluate(item, profile)
            item.fashion_score, item.taste_category, item.generic_score = taste.fashion_score, taste.taste_category, taste.generic_score
            item.taste_components = taste.components

            # Niche mode is not "never show mass-market"; it is "mass-market
            # must earn its place through silhouette/material/current relevance".
            niche_score = float(getattr(item.fashion_attributes, "interesting_trend_score", 0.0) or 0.0) * 100
            if profile.niche_level >= niche_floor and self.taste.should_reject(item, taste):
                dropped["antigeneric"] += 1; continue
            if float(item.confidence or 0) < 0.55:
                dropped["confidence"] += 1; continue
            if profile.budget_max and item.price and item.price > profile.budget_max * 1.15 and item.fashion_score < 88:
                dropped["budget"] += 1; continue

            item.item_type = "product"
            item.meta = dict(item.meta or {})
            item.meta["trendRadar"] = self.trend.radar_version
            item.meta["nicheSignal"] = round(niche_score, 1)
            enriched.append(item)

        # Fashion score is primary; current/niche relevance breaks ties. This
        # prevents the most common keyword match from becoming the "fashion" answer.
        enriched.sort(key=lambda x: (-(x.fashion_score or 0), -(float(getattr(x.fashion_attributes, "interesting_trend_score", 0) or 0)), x.id))
        return DiscoveryResult(products=enriched[:max_products], references=[], queries_used=queries, raw_items=len(raw_items), considered=len(unique), dropped=dropped)
