"""Focused regression tests for ASSTYLIST Fashion Engine v2."""

from __future__ import annotations

from app.fashion_engine import (
    DEFAULT_USER_PROFILE,
    ENGINE_VERSION,
    TOOL_SCHEMA,
    FashionAttributes,
    ProductItem,
    TASTE_CATEGORIES,
    UserStyleProfile,
)
from app.fashion_engine.intelligence.fashion_intelligence import FashionIntelligence
from app.fashion_engine.intelligence.taste_engine import TasteEngine
from app.fashion_engine.intelligence.trend_engine import TrendEngine
from app.fashion_engine.outfit.critic import FashionCritic
from app.fashion_engine.search.query_expander import QueryExpander
from app.fashion_engine.validation.identity_resolver import ProductIdentityResolver
from app.fashion_engine.validation.image_matcher import ImageMatcher
from app.fashion_engine.validation.item_validator import ItemValidator


def card(
    sku: str,
    name: str,
    brand: str,
    category: str,
    *,
    price: float = 10_000,
    tags: tuple[str, ...] = (),
    description: str = "",
    confidence: float = 0.9,
    source_type: str = "marketplace",
) -> ProductItem:
    return ProductItem(
        id=sku,
        sku=sku,
        name=name,
        brand=brand,
        category=category,
        price=price,
        currency="RUB",
        image="",
        source_url=f"https://www.avito.ru/item/{sku}",
        source_type=source_type,
        availability="available",
        confidence=confidence,
        description=description,
        tags=list(tags),
    )


def test_engine_v2_contract_and_tool_schema():
    assert ENGINE_VERSION == "2.0.0"
    assert TOOL_SCHEMA["name"] == "asystylist_create_outfit"
    properties = TOOL_SCHEMA["parameters"]["properties"]
    for key in ("query", "nicheLevel", "aesthetics", "budgetMax", "currency", "occasion", "fitPreference"):
        assert key in properties
    assert TOOL_SCHEMA["parameters"]["required"] == ["query"]


def test_profile_accepts_camel_case_payload():
    profile = UserStyleProfile.from_dict(
        {
            "nicheLevel": 88,
            "aesthetics": ["industrial"],
            "budget": {"max": 90_000, "currency": "RUB"},
            "fitPreference": "oversized",
            "occasion": "party",
        }
    )
    assert profile.niche_level == 88
    assert profile.budget_max == 90_000
    assert profile.currency == "RUB"
    assert profile.fit_preference == "oversized"
    assert profile.prefers_niche() is True
    assert profile.is_within_budget(50_000)
    assert not profile.is_within_budget(120_000)
    assert UserStyleProfile.from_dict(DEFAULT_USER_PROFILE).niche_level == 60


def test_query_expander_is_unique_and_niche_first():
    queries = QueryExpander().expand(
        "грязный индустриальный образ с прозрачным верхом и кожаной курткой",
        {"nicheLevel": 88, "aesthetics": ["industrial", "archive"]},
    )
    assert 4 <= len(queries) <= 14
    assert len(queries) == len(set(queries))
    joined = " ".join(queries).lower()
    for token in ("archive", "sheer", "top", "niche brand"):
        assert token in joined


def test_validator_rejects_unusable_marketplace_items():
    validator = ItemValidator(0.6)
    assert validator.validate(card("A-1", "Wool Coat", "Lemaire", "coat")).valid

    no_brand = card("A-2", "Wool Coat", "", "coat")
    no_brand_result = validator.validate(no_brand)
    assert not no_brand_result.valid

    low_confidence = card("A-3", "Wool Coat", "Lemaire", "coat", confidence=0.2)
    assert not validator.validate(low_confidence).valid


def test_identity_resolver_keeps_distinct_avito_listings():
    resolver = ProductIdentityResolver()
    first = card("AV-1", "Свитер с высоким воротом", "12 STOREEZ", "sweater")
    second = card("AV-2", "Пальто оверсайз двубортное", "12 STOREEZ", "coat")
    third = card("AV-3", "Брюки широкие", "Street Lab", "trousers")
    assert {item.id for item in resolver.resolve([first, second, third])} == {"AV-1", "AV-2", "AV-3"}

    duplicate = card("AV-4", "Пальто оверсайз двубортное", "12 STOREEZ", "coat", confidence=0.95)
    resolved = resolver.resolve([second, duplicate])
    assert len(resolved) == 1


def test_image_matcher_flags_contradictory_listing():
    matcher = ImageMatcher()
    consistent = card("S-1", "Sheer Mesh Top", "Rick Owens", "top", tags=("sheer", "mesh", "black"))
    consistent.fashion_attributes = FashionAttributes(material="sheer", color="black")
    contradictory = card("S-2", "Sheer Mesh Top", "Rick Owens", "top", tags=("wool", "heavy"))
    contradictory.fashion_attributes = FashionAttributes(material="heavy", color="black")
    assert matcher.check_consistency(consistent) > matcher.check_consistency(contradictory)
    assert matcher.should_reject(contradictory, threshold=0.55)


def test_trend_engine_marks_current_niche_signal():
    item = card(
        "T-1",
        "Reworked M-65 leather field jacket",
        "Archive Studio",
        "jacket",
        tags=("archive", "reworked", "m-65", "leather", "workwear"),
        description="deconstructed vintage workwear jacket",
    )
    item.fashion_attributes = FashionIntelligence().analyze(item)
    enriched = TrendEngine().enrich(item)
    assert enriched.fashion_attributes.trend_relevance > 0.30
    assert enriched.fashion_attributes.interesting_trend_score > 0.30
    assert TrendEngine().radar_version == "2026-09-16"


def test_taste_engine_penalises_generic_mass_market_for_niche_profile():
    engine = TasteEngine()
    niche = UserStyleProfile(niche_level=90, aesthetics=["archive"])
    generic = card(
        "G-1",
        "Basic regular fit cotton t-shirt",
        "Uniqlo",
        "top",
        tags=("basic", "regular", "cotton"),
        description="classic everyday basic",
    )
    generic.fashion_attributes = FashionAttributes(aesthetic="minimal", rarity=0.05)
    result = engine.score(generic, niche)
    assert result.generic_score > 50
    assert engine.should_reject(generic, niche)


def test_taste_engine_preserves_distinctive_archive_piece():
    engine = TasteEngine()
    niche = UserStyleProfile(niche_level=90, aesthetics=["archive"])
    item = card(
        "A-ARCHIVE",
        "Deconstructed deadstock wool jacket",
        "Lemaire",
        "jacket",
        tags=("archive", "deadstock", "deconstructed", "rare"),
        description="reworked asymmetric wool construction",
    )
    item.fashion_attributes = FashionAttributes(
        aesthetic="archive",
        rarity=0.9,
        construction="deconstructed",
        silhouette="asymmetric",
    )
    result = engine.score(item, niche)
    assert result.fashion_score > result.generic_score
    assert result.taste_category in TASTE_CATEGORIES


def test_critic_returns_structured_verdict():
    critic = FashionCritic()
    item = card("C-1", "Leather jacket", "Archive Studio", "jacket", tags=("leather", "archive"))
    item.fashion_attributes = FashionAttributes(aesthetic="archive", rarity=0.8)
    result = critic.critique([item], UserStyleProfile(niche_level=85, aesthetics=["archive"]))
    assert result
    assert hasattr(result, "score")
