"""Юнит-тесты Python-порта ASSTYLIST Fashion Engine.

Порт живёт в ``app/fashion_engine`` и повторяет движок из репозитория
https://github.com/karalik19-a11y/- (каталог ``fashion-engine``). Здесь
проверяется поведение пайплайна на синтетических карточках: расширение
запроса, валидация, вкус/anti-generic, архитектура образа, оценка и критик.
"""

from __future__ import annotations

import pytest

from app.fashion_engine import (
    DEFAULT_USER_PROFILE,
    ENGINE_VERSION,
    TOOL_SCHEMA,
    CatalogSearchProvider,
    EngineOptions,
    FashionEngine,
    MockRealProductProvider,
    FashionAttributes,
    ProductItem,
    TASTE_CATEGORIES,
    UserStyleProfile,
    create_outfit,
)
from app.fashion_engine import keywords as kw
from app.fashion_engine import lexicon
from app.fashion_engine.intelligence.fashion_intelligence import FashionIntelligence
from app.fashion_engine.intelligence.taste_engine import TasteEngine
from app.fashion_engine.intelligence.trend_engine import TrendEngine
from app.fashion_engine.outfit.architect import OutfitArchitect
from app.fashion_engine.outfit.critic import FashionCritic
from app.fashion_engine.outfit.scorer import OutfitScorer
from app.fashion_engine.ranking import RankingEngine
from app.fashion_engine.search.providers.web_search_provider import WebSearchProvider
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
    color: str | None = None,
    source_type: str = "designer",
    confidence: float = 0.9,
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
        source_url=f"https://example.test/{sku}",
        source_type=source_type,
        availability="available",
        confidence=confidence,
        description=description,
        color=color,
        tags=list(tags),
    )


def analysed(item: ProductItem) -> ProductItem:
    """Прогнать вещь через Fashion Intelligence — как это делает движок."""
    item.fashion_attributes = FashionIntelligence().analyze(item)
    return TrendEngine().enrich(item)


SHEER_TOP = dict(
    name="Прозрачный топ из вискозы",
    brand="Ann Demeulemeester",
    category="top",
    description="sheer transparent black romantic archive top",
    tags=("sheer", "transparent", "black", "archive", "romantic"),
)

GENERIC_TEE = dict(
    name="Футболка базовая плотная",
    brand="Uniqlo",
    category="top",
    description="basic cotton t-shirt regular fit",
    tags=("basic", "cotton", "regular"),
)


def test_engine_version_and_tool_schema():
    assert ENGINE_VERSION == "1.0.0"
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
    assert profile.is_within_budget(50_000) is True
    assert profile.is_within_budget(120_000) is False
    # Значения по умолчанию совпадают с DEFAULT_USER_PROFILE
    assert UserStyleProfile.from_dict(DEFAULT_USER_PROFILE).niche_level == 60


def test_query_expander_produces_unique_expansions():
    queries = QueryExpander().expand(
        "грязный индустриальный образ с прозрачным верхом и кожаной курткой",
        {"nicheLevel": 80, "aesthetics": ["industrial", "archive"]},
    )
    assert 4 <= len(queries) <= 15
    assert len(queries) == len(set(queries))
    assert queries[0].startswith("грязный индустриальный")
    joined = " ".join(queries).lower()
    for token in ("archive", "sheer", "top"):
        assert token in joined


def test_lexicon_translates_russian_catalog_terms():
    assert "black" in lexicon.detect_colors("чёрное пальто и белые кроссовки")
    assert lexicon.engine_category("Ботинки челси") == "boots"
    assert lexicon.engine_category("Пальто оверсайз двубортное") == "coat"
    translated = lexicon.translate_text("кожаная косуха оверсайз", ("garment", "material", "silhouette"))
    assert "leather" in translated
    assert "oversized" in translated
    assert lexicon.role_label_ru("hero")
    assert lexicon.taste_label_ru("designer")


def test_item_validator_rejects_incomplete_products():
    validator = ItemValidator(0.6)
    valid = validator.validate(card("A-1", "Wool Coat", "Lemaire", "coat"))
    assert valid.valid is True

    no_brand = card("A-2", "Wool Coat", "", "coat")
    assert validator.validate(no_brand).valid is False

    no_url = card("A-3", "Wool Coat", "Lemaire", "coat")
    no_url.source_url = ""
    assert validator.validate(no_url).valid is False

    low_confidence = card("A-4", "Wool Coat", "Lemaire", "coat", confidence=0.2)
    assert validator.validate(low_confidence).valid is False

    kept = validator.filter_valid([card("A-1", "Wool Coat", "Lemaire", "coat"), no_brand, low_confidence])
    assert [item.id for item in kept] == ["A-1"]


def test_image_matcher_flags_contradictions():
    """Название обещает прозрачность, а материал вещи — плотный."""
    matcher = ImageMatcher()
    consistent = card("S-1", "Sheer Mesh Top", "Rick Owens", "top", tags=("sheer", "mesh", "black"))
    consistent.fashion_attributes = FashionAttributes(material="sheer", color="black")

    contradictory = card("S-2", "Sheer Mesh Top", "Rick Owens", "top", tags=("wool", "heavy"))
    contradictory.fashion_attributes = FashionAttributes(material="heavy", color="black")

    assert 0.0 <= matcher.check_consistency(contradictory) <= 1.0
    assert matcher.check_consistency(consistent) > matcher.check_consistency(contradictory)
    assert matcher.check_consistency(contradictory) <= 0.5
    assert matcher.should_reject(contradictory, threshold=0.55) is True
    assert matcher.should_reject(consistent) is False


def test_identity_resolver_keeps_distinct_russian_items():
    """Раньше регулярка резала кириллицу и вещи одного бренда схлопывались."""
    resolver = ProductIdentityResolver()
    items = [
        card("KN-1", "Свитер с высоким воротом", "12 STOREEZ", "sweater"),
        card("OW-1", "Пальто оверсайз двубортное", "12 STOREEZ", "coat"),
        card("BT-1", "Брюки широкие", "Street Lab", "trousers"),
        card("SH-1", "Кроссовки белые", "Street Lab", "sneakers"),
    ]
    kept = {item.id for item in resolver.resolve(items)}
    assert kept == {"KN-1", "OW-1", "BT-1", "SH-1"}

    duplicate = card("OW-2", "Пальто оверсайз двубортное", "12 STOREEZ", "coat", confidence=0.95)
    resolved = resolver.resolve([items[1], duplicate])
    assert len(resolved) == 1
    assert resolved[0].id == "OW-2"  # выше confidence — побеждает


def test_taste_engine_prefers_niche_over_mass_market():
    engine = TasteEngine()
    profile = UserStyleProfile(niche_level=85, aesthetics=["industrial"])
    designer = analysed(card("D-1", "Deconstructed Asymmetric Wool Coat", "Yohji Yamamoto", "coat", **{"tags": ("deconstructed", "asymmetric", "archive", "wool", "black")}))
    mass = analysed(card("M-1", GENERIC_TEE["name"], GENERIC_TEE["brand"], "top", description=GENERIC_TEE["description"], tags=GENERIC_TEE["tags"]))

    designer_taste = engine.evaluate(designer, profile)
    mass_taste = engine.evaluate(mass, profile)

    assert designer_taste.fashion_score > mass_taste.fashion_score
    assert designer_taste.taste_category in TASTE_CATEGORIES
    assert mass_taste.taste_category in TASTE_CATEGORIES
    assert engine.should_reject(mass, mass_taste) is True
    assert engine.should_reject(designer, designer_taste) is False
    assert designer_taste.generic_score < mass_taste.generic_score


def test_trend_engine_enriches_and_suggests_theses():
    top = analysed(card("T-1", "Прозрачный топ", "Rick Owens", "top", tags=("sheer", "mesh")))
    coat = analysed(card("C-1", "Кожаная куртка", "Helmut Lang", "jacket", tags=("leather", "black", "90s")))
    theses = TrendEngine().suggest_theses([top, coat], "индустриальный образ с прозрачным верхом")

    assert "Industrial Romanticism" in theses
    assert top.fashion_attributes.trend_relevance > 0
    assert 0.0 <= top.fashion_attributes.interesting_trend_score <= 1.0


def test_architect_builds_roles_and_requires_three_items():
    products = [
        analysed(card("OW-1", "Кожаная куртка косуха", "Helmut Lang", "jacket", tags=("leather", "black", "biker"))),
        analysed(card("TP-1", "Прозрачный топ", "Rick Owens", "top", tags=("sheer", "mesh", "black"))),
        analysed(card("BT-1", "Широкие брюки", "Lemaire", "trousers", tags=("wool", "wide leg", "minimal"))),
        analysed(card("SH-1", "Ботинки челси", "Ann Demeulemeester", "boots", tags=("leather", "black", "boots"))),
    ]
    candidates = OutfitArchitect().build(products, "industrial look", UserStyleProfile(niche_level=80))
    assert candidates, "архитектор должен собрать образ из четырёх вещей"
    best = candidates[0]
    assert best.item_count() >= 3
    assert best.styling_thesis
    assert set(best.roles) <= {"hero", "base", "layer", "footwear", "accessory"}
    assert "hero" in best.roles

    thin = OutfitArchitect().build(products[:2], "industrial look", UserStyleProfile())
    assert thin == []


def test_scorer_and_critic_bounds():
    products = [
        analysed(card("OW-1", "Кожаная куртка косуха", "Helmut Lang", "jacket", tags=("leather", "black", "biker"))),
        analysed(card("TP-1", "Прозрачный топ", "Rick Owens", "top", tags=("sheer", "mesh", "black"))),
        analysed(card("BT-1", "Широкие брюки", "Lemaire", "trousers", tags=("wool", "wide leg", "minimal"))),
        analysed(card("SH-1", "Ботинки челси", "Ann Demeulemeester", "boots", tags=("leather", "black", "boots"))),
    ]
    candidate = OutfitArchitect().build(products, "industrial look", UserStyleProfile())[0]
    scored = OutfitScorer().score(candidate, UserStyleProfile())
    assert 0 <= scored.outfit_score <= 100
    for key in ("silhouetteCompatibility", "colorHarmony", "proportionBalance", "layeringLogic", "cohesion"):
        assert key in scored.breakdown

    verdict = FashionCritic().critique(candidate, scored.breakdown)
    assert verdict.decision in {"APPROVE", "REBUILD"}
    assert verdict.score_adjustment in {5.0, 0.0, -8.0, -15.0}

    weak = OutfitArchitect().build(products, "industrial look", UserStyleProfile())[0]
    weak.items = weak.items[:3]
    weak.items[0].role = "accessory"
    weak_verdict = FashionCritic().critique(weak, {"originality": 0.1, "hierarchy": 0.1})
    assert weak_verdict.decision in {"APPROVE", "REBUILD"}
    assert weak_verdict.feedback


def test_ranking_engine_orders_by_fashion_strength():
    ranker = RankingEngine()
    strong = analysed(card("STRONG", "Deconstructed Archive Coat", "Yohji Yamamoto", "coat", tags=("deconstructed", "archive", "black")))
    weak = analysed(card("WEAK", GENERIC_TEE["name"], "Uniqlo", "top", description=GENERIC_TEE["description"], tags=GENERIC_TEE["tags"]))
    strong.fashion_score, weak.fashion_score = 88, 31
    strong.confidence, weak.confidence = 0.92, 0.62
    assert [item.id for item in ranker.rank_items([weak, strong])] == ["STRONG", "WEAK"]


def test_catalog_provider_searches_the_app_catalog():
    sheer = card("RU-1", "Прозрачная блуза", "Silk Route", "blouse", **{"description": "sheer transparent organza blouse romantic"})
    shearling = card("RU-2", "Дублёнка", "Cozy Line", "coat", **{"description": "shearling heavy wool coat winter"})
    from app.fashion_engine.search.provider import SearchContext

    provider = CatalogSearchProvider([sheer, shearling])
    context = SearchContext(limit=5)
    found = provider.search("прозрачный верх sheer transparent", context)
    assert found, "провайдер должен вернуть хотя бы одну вещь"
    assert found[0].id == "RU-1"
    assert provider.source_type == "app-catalog"
    assert context.limit == 5


def test_web_provider_is_an_empty_placeholder():
    assert WebSearchProvider().search("anything", None) == []


def test_engine_end_to_end_on_mock_catalog_is_deterministic():
    profile = {
        "nicheLevel": 80,
        "aesthetics": ["industrial", "romantic"],
        "budget": {"max": 6_000, "currency": "EUR"},
        "occasion": "editorial",
        "fitPreference": "oversized",
    }
    first = create_outfit("industrial romantic look with sheer top", profile, providers=[MockRealProductProvider()])
    second = create_outfit("industrial romantic look with sheer top", profile, providers=[MockRealProductProvider()])

    assert len(first.items) >= 3
    assert first.outfit_score > 0
    assert first.styling_thesis
    assert first.critic_decision in {"APPROVE", "REBUILD"}
    assert [item.id for item in first.items] == [item.id for item in second.items]
    assert first.outfit_score == second.outfit_score

    payload = first.to_dict()
    assert set(payload) >= {"aesthetic", "stylingThesis", "outfitScore", "items", "stylingLogic", "meta"}
    assert payload["items"][0]["sourceUrl"].startswith("https://")
    assert payload["items"][0]["fashionScore"] >= 0


def test_engine_returns_empty_response_for_thin_catalog():
    provider = CatalogSearchProvider([card("ONLY-1", "Wool Coat", "Lemaire", "coat")])
    engine = FashionEngine(providers=[provider], options=EngineOptions(max_products=5))
    result = engine.create_outfit("minimal wool coat", UserStyleProfile())
    assert result.items == []
    assert result.meta["error"] is True
    assert result.styling_thesis == "unable to form thesis"


def test_thresholds_use_provider_confidence():
    items = [
        card("OK", "Wool Coat", "Lemaire", "coat", confidence=0.8),
        card("LOW", "Wool Coat", "Lemaire", "coat", confidence=0.3),
    ]
    provider = CatalogSearchProvider(items)
    assert provider.validate_item(items[1]).confidence == pytest.approx(0.3)
    assert ItemValidator(0.6).filter_valid(items) == [items[0]]


def test_thesis_labels_have_russian_variants():
    assert kw.thesis_label_ru("Industrial Romanticism") == "Индустриальная романтика"
    assert kw.thesis_label_ru("") == ""
