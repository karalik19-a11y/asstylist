"""Explicit pipeline boundary for the Fashion Engine.

This module is the **extension map** for AI agents and humans.
It does not change runtime behaviour; it documents and exposes the ordered
steps that ``FashionEngine.create_outfit`` already runs.

Agents should:

* implement or replace a single step behind its Protocol when possible;
* keep ``SearchProvider`` as the only way to inject product sources;
* avoid importing application services (``app.services``, ``app.api``) from
  inside this package — adapters live outside (see ``fashion_engine_service``).

Physical path stays ``backend/app/fashion_engine/`` so existing imports and
the live site remain stable. A future extract to a standalone installable
package can re-export this same public surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .types import OutfitCandidate, OutfitResult, ProductItem, UserStyleProfile


@runtime_checkable
class QueryExpandStep(Protocol):
    def expand(self, query: str, profile: UserStyleProfile | dict[str, Any]) -> list[str]: ...


@runtime_checkable
class SearchStep(Protocol):
    def run(self, user_query: str, profile: UserStyleProfile, options: dict[str, Any]) -> Any: ...

    def enrich(self, items: list[ProductItem], profile: UserStyleProfile) -> list[ProductItem]: ...


@runtime_checkable
class ValidateStep(Protocol):
    def filter_valid(self, items: list[ProductItem]) -> list[ProductItem]: ...


@runtime_checkable
class ImageMatchStep(Protocol):
    def should_reject(self, item: ProductItem, threshold: float = 0.55) -> bool: ...


@runtime_checkable
class IdentityStep(Protocol):
    def resolve(self, items: list[ProductItem]) -> list[ProductItem]: ...


@runtime_checkable
class RankItemsStep(Protocol):
    def rank_items(self, items: list[ProductItem]) -> list[ProductItem]: ...


@runtime_checkable
class ArchitectStep(Protocol):
    def build(
        self,
        products: list[ProductItem],
        user_query: str,
        profile: UserStyleProfile,
        options: dict[str, Any] | None = None,
    ) -> list[OutfitCandidate]: ...


@runtime_checkable
class ScoreStep(Protocol):
    def score(self, candidate: OutfitCandidate, profile: UserStyleProfile) -> Any: ...


@runtime_checkable
class CriticStep(Protocol):
    def critique(self, candidate: OutfitCandidate, breakdown: Any) -> Any: ...


@runtime_checkable
class RankOutfitsStep(Protocol):
    def rank_outfits(self, candidates: list[OutfitCandidate]) -> list[OutfitCandidate]: ...


@dataclass(frozen=True)
class PipelineStep:
    """One named stage agents can target independently."""

    id: str
    title: str
    module: str
    description: str
    safe_to_extend: bool = True


#: Ordered map of the create_outfit pipeline. Order matches FashionEngine.
PIPELINE_STEPS: tuple[PipelineStep, ...] = (
    PipelineStep(
        id="expand",
        title="Query expansion",
        module="app.fashion_engine.search.query_expander",
        description="Expand user intent into multiple search queries (RU/EN).",
    ),
    PipelineStep(
        id="search",
        title="Multi-pass search",
        module="app.fashion_engine.search.multi_pass_search",
        description="Run SearchProvider implementations and merge product pools.",
    ),
    PipelineStep(
        id="intelligence",
        title="Fashion intelligence",
        module="app.fashion_engine.intelligence",
        description="Attributes, trends, taste / anti-generic scoring.",
    ),
    PipelineStep(
        id="validate",
        title="Item validation",
        module="app.fashion_engine.validation.item_validator",
        description="Drop low-confidence or incomplete listings.",
    ),
    PipelineStep(
        id="image_match",
        title="Image / text consistency",
        module="app.fashion_engine.validation.image_matcher",
        description="Reject contradictory title vs attributes signals.",
    ),
    PipelineStep(
        id="identity",
        title="Identity resolve",
        module="app.fashion_engine.validation.identity_resolver",
        description="Deduplicate brand::name style collisions.",
    ),
    PipelineStep(
        id="rank_items",
        title="Item ranking",
        module="app.fashion_engine.ranking",
        description="Order products before architecture.",
    ),
    PipelineStep(
        id="architect",
        title="Outfit architecture",
        module="app.fashion_engine.outfit.architect",
        description="Assign roles (hero/base/layer/footwear/accessory).",
    ),
    PipelineStep(
        id="score",
        title="Outfit scoring",
        module="app.fashion_engine.outfit.scorer",
        description="Numeric outfit score and breakdown.",
    ),
    PipelineStep(
        id="critic",
        title="Fashion critic",
        module="app.fashion_engine.outfit.critic",
        description="APPROVE / REVISE / REBUILD with score adjustment.",
    ),
    PipelineStep(
        id="rank_outfits",
        title="Outfit ranking",
        module="app.fashion_engine.ranking",
        description="Pick best candidate and alternatives.",
    ),
)


def pipeline_ids() -> list[str]:
    return [step.id for step in PIPELINE_STEPS]


def pipeline_as_dict() -> list[dict[str, Any]]:
    return [
        {
            "id": step.id,
            "title": step.title,
            "module": step.module,
            "description": step.description,
            "safe_to_extend": step.safe_to_extend,
        }
        for step in PIPELINE_STEPS
    ]


# Re-export result type for agents that only need the boundary surface.
__all__ = [
    "ArchitectStep",
    "CriticStep",
    "IdentityStep",
    "ImageMatchStep",
    "OutfitResult",
    "PIPELINE_STEPS",
    "PipelineStep",
    "QueryExpandStep",
    "RankItemsStep",
    "RankOutfitsStep",
    "ScoreStep",
    "SearchStep",
    "ValidateStep",
    "pipeline_as_dict",
    "pipeline_ids",
]
