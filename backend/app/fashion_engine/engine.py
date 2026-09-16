"""FashionEngine — оркестратор пайплайна (порт ``src/core/FashionEngine.js``).

    USER INTENT → AESTHETIC DNA → FASHION RESEARCH → ITEM DISCOVERY →
    ITEM VALIDATION → OUTFIT ARCHITECTURE → COMPATIBILITY SCORING → FINAL LOOK
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .intelligence import TrendEngine
from .outfit import FashionCritic, OutfitArchitect, OutfitScorer
from .ranking import RankingEngine
from .search.multi_pass_search import DiscoveryResult, MultiPassSearch
from .search.providers.mock_real_product_provider import MockRealProductProvider
from .search.providers.web_search_provider import WebSearchProvider
from .types import OutfitCandidate, OutfitResult, ProductItem, UserStyleProfile
from .validation import ImageMatcher, ItemValidator, ProductIdentityResolver

ENGINE_VERSION = "1.0.0"


@dataclass
class EngineOptions:
    """Настройки пайплайна (в оригинале — второй/третий аргумент функций)."""

    max_products: int = 40
    limit_per_query: int = 6
    min_confidence: float = 0.6
    max_outfits: int = 4
    categories: list[str] = field(default_factory=list)
    #: Ограничение числа расширенных запросов (для живых провайдеров, где
    #: каждый запрос — HTTP). None — без ограничения, как в оригинале.
    max_queries: int | None = None

    @classmethod
    def from_value(cls, value: "EngineOptions | dict | None") -> "EngineOptions":
        if isinstance(value, EngineOptions):
            return value
        if isinstance(value, dict):
            known = {key: value[key] for key in value if key in cls.__dataclass_fields__}
            return cls(**known)
        return cls()


class FashionEngine:
    def __init__(self, providers: list | None = None, options: EngineOptions | dict | None = None) -> None:
        self.options = EngineOptions.from_value(options)
        # Дефолт из оригинала; asStylist подставляет CatalogSearchProvider.
        self.providers = list(providers) if providers is not None else [MockRealProductProvider(), WebSearchProvider()]
        self.search = MultiPassSearch(self.providers)
        self.validator = ItemValidator(self.options.min_confidence)
        self.image_matcher = ImageMatcher()
        self.identity = ProductIdentityResolver()
        self.architect = OutfitArchitect()
        self.scorer = OutfitScorer()
        self.critic = FashionCritic()
        self.ranker = RankingEngine()
        self.trend = TrendEngine()

    # ─── PASS 1–3: поиск и обогащение ─────────────────────────────────
    def discover(
        self,
        user_query: str,
        raw_profile: UserStyleProfile | dict | None = None,
    ) -> DiscoveryResult:
        profile = self._profile(raw_profile)
        return self.search.run(
            user_query,
            profile,
            {
                "max_products": self.options.max_products,
                "limit_per_query": self.options.limit_per_query,
                "categories": self.options.categories,
                "max_queries": self.options.max_queries,
            },
        )

    def enrich(
        self,
        items: list,
        raw_profile: UserStyleProfile | dict | None = None,
    ) -> list:
        """Обогатить вещи вне поисковых запросов (см. ``MultiPassSearch.enrich``)."""
        return self.search.enrich(list(items), self._profile(raw_profile))

    # ─── PASS 4–6: сборка и оценка образа ─────────────────────────────
    def create_outfit(
        self,
        user_query: str,
        raw_profile: UserStyleProfile | dict | None = None,
        options: EngineOptions | dict | None = None,
        preloaded: DiscoveryResult | None = None,
    ) -> OutfitResult:
        settings = EngineOptions.from_value(options) if options is not None else self.options
        profile = self._profile(raw_profile)

        discovery = preloaded or self.discover(user_query, profile)

        validator = ItemValidator(settings.min_confidence)
        products: list[ProductItem] = validator.filter_valid(discovery.products)
        products = [item for item in products if not self.image_matcher.should_reject(item)]
        products = self.identity.resolve(products)
        products = self.ranker.rank_items(products)

        if len(products) < 3:
            return OutfitResult.empty(
                user_query,
                "Insufficient high-quality real products found after validation.",
            )

        candidates = self.architect.build(
            products,
            user_query,
            profile,
            {"max_outfits": settings.max_outfits},
        )

        evaluated: list[OutfitCandidate] = []
        for candidate in candidates:
            score_result = self.scorer.score(candidate, profile)
            critique = self.critic.critique(candidate, score_result.breakdown)
            candidate.outfit_score = max(0.0, min(100.0, score_result.outfit_score + critique.score_adjustment))
            candidate.score_breakdown = score_result.breakdown
            candidate.critic_decision = critique.decision
            candidate.critic_feedback = critique.feedback
            candidate.critic_score_adjustment = critique.score_adjustment
            candidate.styling_logic = self._build_styling_logic(candidate)
            evaluated.append(candidate)

        approved = [
            candidate
            for candidate in evaluated
            if candidate.critic_decision == "APPROVE" or candidate.outfit_score >= 70
        ]
        ranked = self.ranker.rank_outfits(approved or evaluated)
        best = ranked[0] if ranked else None
        if best is None:
            return OutfitResult.empty(user_query, "Could not assemble a coherent outfit.")

        return OutfitResult(
            aesthetic=best.aesthetic,
            styling_thesis=best.styling_thesis,
            outfit_score=best.outfit_score,
            items=best.items,
            styling_logic=best.styling_logic,
            references=[],
            alternatives=[
                {
                    "stylingThesis": alternative.styling_thesis,
                    "outfitScore": alternative.outfit_score,
                    "itemCount": alternative.item_count(),
                    "criticDecision": alternative.critic_decision,
                    "roles": alternative.roles,
                }
                for alternative in ranked[1:3]
            ],
            critic_feedback=best.critic_feedback,
            critic_decision=best.critic_decision,
            meta={
                "queriesUsed": discovery.queries_used[:8],
                "queriesTotal": len(discovery.queries_used),
                "rawItems": discovery.raw_items,
                "totalCandidatesConsidered": len(discovery.products),
                "validatedProducts": len(products),
                "candidatesBuilt": len(candidates),
                "nicheLevel": profile.niche_level,
                "engineVersion": ENGINE_VERSION,
                "dropped": dict(discovery.dropped),
                "theses": [candidate.styling_thesis for candidate in ranked],
                "scoreBreakdown": best.score_breakdown,
            },
        )

    # ─── вспомогательное ──────────────────────────────────────────────
    @staticmethod
    def _profile(raw_profile: UserStyleProfile | dict | None) -> UserStyleProfile:
        if isinstance(raw_profile, UserStyleProfile):
            return raw_profile
        return UserStyleProfile.from_dict(raw_profile or {})

    @staticmethod
    def _build_styling_logic(candidate: OutfitCandidate) -> dict[str, Any]:
        items = candidate.items or []

        def unique(values: list[str]) -> list[str]:
            return list(dict.fromkeys(value for value in values if value))

        silhouettes = unique(
            [entry for item in items for entry in (getattr(item.fashion_attributes, "silhouette", []) or [])]
        )
        colors = unique(
            [
                getattr(item.fashion_attributes, "color", "")
                for item in items
                if item.fashion_attributes and getattr(item.fashion_attributes, "color", "")
            ]
        )
        textures = unique(
            [
                getattr(item.fashion_attributes, "texture", "")
                or getattr(item.fashion_attributes, "material", "")
                for item in items
                if item.fashion_attributes
            ]
        )
        hero = next((item for item in items if item.role == "hero"), items[0] if items else None)
        return {
            "silhouette": " + ".join(silhouettes) or "balanced",
            "color": " / ".join(colors) or "monochrome",
            "layering": "intentional layering present"
            if any(getattr(item.fashion_attributes, "layering_potential", "") == "high" for item in items)
            else "minimal layering",
            "textures": " + ".join(textures) or "mixed",
            "focalPoint": hero.name if hero else "undefined",
            "roles": [item.role for item in items],
        }


def create_outfit(
    query: str,
    profile: UserStyleProfile | dict | None = None,
    options: EngineOptions | dict | None = None,
    providers: list | None = None,
) -> OutfitResult:
    """Удобная обёртка (в оригинале — ``createOutfit``)."""
    engine = FashionEngine(providers=providers, options=options)
    return engine.create_outfit(query, profile)


def create_outfit_dict(
    query: str,
    profile: UserStyleProfile | dict | None = None,
    options: EngineOptions | dict | None = None,
    providers: list | None = None,
) -> dict[str, Any]:
    """Тот же вызов, но сразу JSON-совместимый ответ контракта движка."""
    return create_outfit(query, profile, options, providers).to_dict()
