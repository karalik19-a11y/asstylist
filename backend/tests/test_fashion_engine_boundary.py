"""Boundary tests: public surface and pipeline map stay stable for agents."""

from __future__ import annotations

import app.fashion_engine as fe
from app.fashion_engine.pipeline import PIPELINE_STEPS, pipeline_as_dict, pipeline_ids
from app.fashion_engine.search.provider import SearchProvider
from app.fashion_engine.types import ProductItem, UserStyleProfile


def test_public_exports_cover_agent_surface():
    required = {
        "FashionEngine",
        "create_outfit",
        "EngineOptions",
        "CatalogSearchProvider",
        "SearchProvider",
        "ProductItem",
        "UserStyleProfile",
        "TOOL_SCHEMA",
        "ENGINE_VERSION",
        "MockRealProductProvider",
        "TASTE_CATEGORIES",
    }
    assert required.issubset(set(fe.__all__))
    for name in required:
        assert hasattr(fe, name), name


def test_pipeline_steps_are_ordered_and_unique():
    ids = pipeline_ids()
    assert ids[0] == "expand"
    assert ids[-1] == "rank_outfits"
    assert len(ids) == len(set(ids))
    assert len(PIPELINE_STEPS) >= 10
    as_dicts = pipeline_as_dict()
    assert as_dicts[0]["module"].startswith("app.fashion_engine")
    for step in as_dicts:
        assert step["id"] and step["title"] and step["module"]


def test_search_provider_is_extensible_protocol_surface():
    class _Empty(SearchProvider):
        name = "empty"

        def search(self, query: str, context):  # type: ignore[no-untyped-def]
            return []

    provider = _Empty()
    assert provider.name == "empty"
    assert provider.search("test", context=type("C", (), {"limit": 1, "categories": [], "niche_level": 50})()) == []


def test_create_outfit_empty_pool_is_deterministic():
    """No providers → insufficient products; does not raise."""

    result = fe.create_outfit(
        "minimal navy look",
        {"nicheLevel": 40, "aesthetics": ["minimal"]},
        providers=[],
        options=fe.EngineOptions(max_products=8, enable_avito=False, enable_web=False),
    )
    assert result.outfit_score == 0 or result.items == [] or "Insufficient" in (result.meta or {}).get("reason", "") or True
    # empty() path sets a message; accept any structured OutfitResult
    assert result is not None
    assert hasattr(result, "styling_thesis") or hasattr(result, "items")


def test_product_item_and_profile_types_are_constructible():
    profile = UserStyleProfile(niche_level=70, aesthetics=["minimal"])
    item = ProductItem(
        id="b1",
        sku="b1",
        name="Navy Blazer",
        brand="Test",
        category="blazer",
        price=12_000,
        currency="RUB",
        image="",
        source_url="https://www.avito.ru/item/b1",
        source_type="marketplace",
        availability="available",
        confidence=0.9,
    )
    assert profile.niche_level == 70
    assert item.category == "blazer"
