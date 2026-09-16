"""Поиск и подбор вещей только на Авито.

Провайдер покрыт фикстурами HTML без единого HTTP-запроса: парсинг карточек,
запасные стратегии, перевод запроса, скоринг по ключевым словам/названию/
фото/описанию, кэш и «не ронять пайплайн». Сервисный слой — дип-линки Авито
и резервный режим без пустых выдач.
"""

from __future__ import annotations

import pytest

from app.config import settings
from app.engine.look_builder import LookRequest
from app.fashion_engine.search.provider import SearchContext
from app.fashion_engine.search.providers.avito_provider import (
    AvitoSearchProvider,
    avito_search_url,
    translate_query_to_ru,
)
from app.fashion_engine.types import UserStyleProfile
from app.services import catalog_service, fashion_engine_service

SERP_HTML = """
<html><body>
<div data-marker="item" data-item-id="1234567890">
  <a data-marker="item-title"
     href="/moskva/odezhda_obuv_aksessuary/palto_zhenskoe_sherst_1234567890"
     title="Пальто женское шерстяное">Пальто женское шерстяное</a>
  <meta itemprop="price" content="12500">
  <img src="https://00.img.avito.st/image/1/1_abc123.jpg" alt="Пальто">
  <div data-marker="item-specific-params">Размер M · Состояние отличное</div>
</div>
<div data-marker="item" data-item-id="2345678901">
  <a data-marker="item-title"
     href="/moskva/odezhda_obuv_aksessuary/kurtka_kozh_kosukha_2345678901">Куртка кожаная косуха</a>
  <meta itemprop="price" content="8900">
  <img data-src="https://30.img.avito.st/image/1/1_def456.jpg">
</div>
<div data-marker="item" data-item-id="3456789012">
  <a data-marker="item-title" href="/sankt-peterburg/odezhda_obuv_aksessuary/sumka_3456789012">Сумка</a>
  <meta itemprop="price" content="0">
  <img src="https://00.img.avito.st/image/1/1_no.jpg">
</div>
<div data-marker="item" data-item-id="4567890123">
  <a data-marker="item-title" href="/moskva/odezhda_obuv_aksessuary/dzhinsy_4567890123">Джинсы широкие</a>
  <p data-marker="item-price"><span>4 500 ₽</span></p>
</div>
</body></html>
"""

BIG_SERP_HTML = """
<html><body>
<div data-marker="item" data-item-id="1010101010">
  <a data-marker="item-title" href="/moskva/odezhda_obuv_aksessuary/palto_sherst_1010101010">Пальто шерстяное оверсайз Lime</a>
  <meta itemprop="price" content="11900">
  <img src="https://00.img.avito.st/image/1/1_coat.jpg">
  <div data-marker="item-specific-params">Размер M · чёрное · состояние отличное</div>
</div>
<div data-marker="item" data-item-id="2020202020">
  <a data-marker="item-title" href="/moskva/odezhda_obuv_aksessuary/sviter_kashemir_2020202020">Свитер кашемировый бежевый</a>
  <meta itemprop="price" content="6900">
  <img src="https://30.img.avito.st/image/1/1_sweater.jpg">
</div>
<div data-marker="item" data-item-id="3030303030">
  <a data-marker="item-title" href="/moskva/odezhda_obuv_aksessuary/rubashka_belaya_3030303030">Рубашка белая хлопок</a>
  <meta itemprop="price" content="2900">
  <img src="https://00.img.avito.st/image/1/1_shirt.jpg">
</div>
<div data-marker="item" data-item-id="4040404040">
  <a data-marker="item-title" href="/moskva/odezhda_obuv_aksessuary/dzhinsy_shirokie_4040404040">Джинсы широкие Levi's</a>
  <meta itemprop="price" content="5400">
  <img src="https://60.img.avito.st/image/1/1_jeans.jpg">
  <div data-marker="item-specific-params">Размер 27 · деним</div>
</div>
<div data-marker="item" data-item-id="5050505050">
  <a data-marker="item-title" href="/moskva/odezhda_obuv_aksessuary/botinki_kozhanye_5050505050">Ботинки кожаные челси</a>
  <meta itemprop="price" content="9900">
  <img src="https://00.img.avito.st/image/1/1_boots.jpg">
</div>
<div data-marker="item" data-item-id="6060606060">
  <a data-marker="item-title" href="/moskva/odezhda_obuv_aksessuary/sumka_kozh_6060606060">Сумка кожаная кросс-боди</a>
  <meta itemprop="price" content="7900">
  <img src="https://30.img.avito.st/image/1/1_bag.jpg">
</div>
<div data-marker="item" data-item-id="7070707070">
  <a data-marker="item-title" href="/moskva/odezhda_obuv_aksessuary/sharf_sherst_7070707070">Шарф шерстяной серый</a>
  <meta itemprop="price" content="1900">
  <img src="https://00.img.avito.st/image/1/1_scarf.jpg">
</div>
<div data-marker="item" data-item-id="8080808080">
  <a data-marker="item-title" href="/moskva/odezhda_obuv_aksessuary/platye_midi_8080808080">Платье миди трикотажное</a>
  <meta itemprop="price" content="5900">
  <img src="https://60.img.avito.st/image/1/1_dress.jpg">
</div>
</body></html>
"""

JSON_LD_HTML = """
<html><body>
<script type="application/ld+json">
{"@type": "ItemList", "itemListElement": [
  {"item": {"@type": "Product", "name": "Свитер кашемировый",
            "url": "https://www.avito.ru/moskva/odezhda_obuv_aksessuary/sviter_1122334455",
            "image": "https://60.img.avito.st/p.jpg",
            "offers": {"price": "6900"}}}
]}
</script>
</body></html>
"""


@pytest.fixture()
def provider() -> AvitoSearchProvider:
    return AvitoSearchProvider(city="rossiya", timeout=2.0, max_results=10)


@pytest.fixture()
def context() -> SearchContext:
    return SearchContext(user_profile=UserStyleProfile(budget_max=60_000), limit=8)


# ─── перевод запроса ─────────────────────────────────────────────────────────


def test_translate_query_to_ru_drops_filler_and_translates_garments():
    translated = translate_query_to_ru("archive sheer designer top editorial fashion")
    assert "топ" in translated
    assert "полупрозрачный" in translated
    assert "archive" not in translated
    assert "fashion" not in translated


def test_translate_query_to_ru_keeps_russian_and_brands():
    translated = translate_query_to_ru("грязный индустриальный образ с прозрачным верхом zara")
    assert "индустриальный" in translated
    assert "прозрачным" in translated
    assert "zara" in translated
    assert "образ" in translated or "грязный" in translated


def test_translate_query_to_ru_bigram_and_fallback():
    assert translate_query_to_ru("quiet luxury coat") == "тихая роскошь пальто"
    assert translate_query_to_ru("!!!") == "одежда"
    assert translate_query_to_ru("") == "одежда"


def test_avito_search_url_is_real_link():
    url = avito_search_url("Пальто шерстяное")
    assert url.startswith("https://www.avito.ru/rossiya/odezhda_obuv_aksessuary?q=")
    assert "%D0%9F" in url  # кириллица («Пальто») закодирована
    assert avito_search_url("").endswith("?q=%D0%BE%D0%B4%D0%B5%D0%B6%D0%B4%D0%B0")


# ─── парсинг ─────────────────────────────────────────────────────────────────


def test_parse_cards_extracts_title_price_url_photo(provider):
    items = provider._parse_cards(SERP_HTML)
    # Объявление с нулевой ценой отбрасывается, остальные три — в разборе.
    assert {item["avito_id"] for item in items} == {"1234567890", "2345678901", "4567890123"}

    coat = next(item for item in items if item["avito_id"] == "1234567890")
    assert coat["title"] == "Пальто женское шерстяное"
    assert coat["price"] == 12500
    assert coat["url"] == (
        "https://www.avito.ru/moskva/odezhda_obuv_aksessuary/palto_zhenskoe_sherst_1234567890"
    )
    assert coat["image"].startswith("https://00.img.avito.st/")
    assert "Размер M" in coat["params"]

    jacket = next(item for item in items if item["avito_id"] == "2345678901")
    assert jacket["price"] == 8900
    assert jacket["image"].startswith("https://30.img.avito.st/")

    jeans = next(item for item in items if item["avito_id"] == "4567890123")
    assert jeans["price"] == 4500
    assert jeans["image"] == ""


def test_parse_json_ld_fallback(provider):
    items = provider._parse(JSON_LD_HTML)
    assert len(items) == 1
    item = items[0]
    assert item["title"] == "Свитер кашемировый"
    assert item["price"] == 6900
    assert item["url"].startswith("https://www.avito.ru/")
    assert item["avito_id"] == "1122334455"


def test_parse_garbage_returns_empty_list(provider):
    assert provider._parse("") == []
    assert provider._parse("<html><body>капча</body></html>") == []


# ─── скоринг: ключевые слова, название, фото, описание ───────────────────────


def _product(provider, raw, ru_query, extra_query=""):
    tokens = __import__("app.fashion_engine.lexicon", fromlist=["tokenize"]).tokenize(
        f"{extra_query} {ru_query}"
    )
    return provider._to_product(raw, ru_query, [t for t in tokens if len(t) >= 3], 60_000)


def test_scoring_prefers_title_hits_over_description(provider):
    coat = {"avito_id": "1", "title": "Пальто шерстяное", "price": 9000,
            "url": "https://www.avito.ru/x_1", "image": "", "params": ""}
    bag = {"avito_id": "2", "title": "Сумка кожаная", "price": 9000,
           "url": "https://www.avito.ru/x_2", "image": "", "params": "пальто шерстяное в подарок"}
    coat_score = _product(provider, coat, "пальто шерстяное").meta["query_match"]
    bag_score = _product(provider, bag, "пальто шерстяное").meta["query_match"]
    assert coat_score > bag_score


def test_scoring_rewards_photo_and_rich_description(provider):
    base = {"avito_id": "1", "title": "Куртка", "price": 5000,
            "url": "https://www.avito.ru/x_1", "image": "", "params": ""}
    plain = _product(provider, dict(base), "куртка")
    rich = _product(
        provider,
        {**base, "avito_id": "2", "url": "https://www.avito.ru/x_2",
         "image": "https://00.img.avito.st/image/1/640x480_pic.jpg",
         "params": "Размер M · кожа · чёрная · состояние отличное"},
        "куртка",
    )
    assert rich is not None and plain is not None
    assert rich.meta["photo_score"] > 0
    assert rich.meta["description_score"] > plain.meta["description_score"]
    assert rich.meta["query_match"] > plain.meta["query_match"]


def test_to_product_detects_category_brand_color(provider):
    card = _product(
        provider,
        {"avito_id": "9", "title": "Пальто женское чёрное Zara", "price": 7000,
         "url": "https://www.avito.ru/x_9",
         "image": "https://00.img.avito.st/a.jpg", "params": ""},
        "пальто",
    )
    assert card is not None
    assert card.category == "coat"
    assert card.brand == "Zara"
    assert card.color == "black"
    assert card.currency == "RUB"
    assert card.sku == "avito_9"
    assert 0.55 <= card.confidence <= 0.97


def test_to_product_rejects_broken_rows(provider):
    assert provider._to_product(
        {"avito_id": "1", "title": "ok", "price": 100, "url": "https://www.avito.ru/x", "image": "", "params": ""},
        "ok", ["ok"], 0) is None
    assert provider._to_product(
        {"avito_id": "1", "title": "Пальто", "price": 0, "url": "https://www.avito.ru/x", "image": "", "params": ""},
        "пальто", ["пальт"], 0) is None


# ─── search(): кэш, лимиты, fail-open, «не ронять пайплайн» ──────────────────


def test_search_returns_ranked_products_and_caches(provider, context, monkeypatch):
    calls = {"n": 0}

    def fake_fetch(ru_query):
        calls["n"] += 1
        return SERP_HTML

    monkeypatch.setattr(provider, "_fetch_html", fake_fetch)
    first = provider.search("шерстяное пальто", context)
    second = provider.search("шерстяное пальто", context)
    assert calls["n"] == 1  # второй вызов обслужен из кэша
    assert first and second
    assert all(item.source_url.startswith("https://www.avito.ru/") for item in first)
    # Все позиции с фото идут раньше объявлений без фото.
    assert first[0].image
    # Релевантность запросу: пальто выше косухи.
    names = [item.name for item in first]
    assert names.index("Пальто женское шерстяное") < names.index("Куртка кожаная косуха")
    assert len(first) <= context.limit


def test_search_respects_limit_and_category_filter(provider, monkeypatch):
    monkeypatch.setattr(provider, "_fetch_html", lambda ru_query: SERP_HTML)
    context = SearchContext(user_profile=UserStyleProfile(), limit=1)
    assert len(provider.search("пальто", context)) == 1

    # Фильтр категории, выкосивший всё, не даёт пустую выдачу (fail-open).
    strict = SearchContext(user_profile=UserStyleProfile(), limit=8, categories=["dress"])
    assert provider.search("пальто", strict)


def test_search_never_raises(provider, context, monkeypatch):
    monkeypatch.setattr(provider, "_fetch_html", lambda ru_query: 1 / 0)
    assert provider.search("пальто", context) == []


def test_validate_item_accepts_only_avito_links(provider):
    card = _product(
        provider,
        {"avito_id": "1", "title": "Пальто", "price": 5000,
         "url": "https://www.avito.ru/x_1", "image": "", "params": ""},
        "пальто",
    )
    assert provider.validate_item(card).valid
    card.source_url = "https://example.com/x"
    assert not provider.validate_item(card).valid
    card.source_url = "https://www.avito.ru/x_1"
    card.price = 0
    assert not provider.validate_item(card).valid


# ─── сервисный слой: запросы, конверсия, страховка ссылок ───────────────────


def test_ru_slot_query_is_short_and_russian():
    request = LookRequest(style="grunge", mood="bold", height_cm=174, weight_kg=64,
                          budget_rub=60_000, presentation="feminine", season="winter",
                          query="грязный индустриальный образ")
    query = fashion_engine_service.ru_slot_query(request, "outerwear")
    assert "пальто" in query
    assert "женский" in query
    assert len(query.split()) <= 6
    assert all(not word.isascii() or word in ("zara",) for word in query.split())


def test_extract_brand_reads_title_and_never_returns_avito():
    """Бренд берётся из заголовка объявления; «Авито» брендом не считается."""
    from app.fashion_engine.search.providers.avito_provider import _extract_brand

    assert _extract_brand("Кроссовки Nike Air Force 1 черные") == "Nike"
    assert _extract_brand("Джинсы Zara bootcut клеш") == "Zara"
    assert _extract_brand("Кроп пальто LGB archive") == "LGB"
    assert _extract_brand("Свитер мужской без горла") == ""


def test_avito_card_without_brand_becomes_bez_brenda():
    """Пустой бренд не роняет сборку образа (регрессия NameError)."""
    from app.fashion_engine.types import ProductItem
    from app.engine.look_builder import LookRequest

    card = ProductItem(
        id="avito_1",
        sku="avito_1",
        name="Пальто женское шерстяное",
        brand="",
        category="outerwear",
        price=12500.0,
        currency="RUB",
        image="https://10.img.avito.st/image/1/1.example",
        source_url="https://www.avito.ru/moskva/odezhda_obuv_aksessuary/palto_1234567890",
        source_type="avito",
        availability="in_stock",
        confidence=0.9,
    )
    request = LookRequest(style="minimal", mood="calm", height_cm=174, weight_kg=64, budget_rub=60_000)
    item = fashion_engine_service.avito_card_to_catalog_item(card, request)
    assert item.brand and item.brand != "Авито"


def test_avito_card_to_catalog_item_keeps_link_photo_price():
    provider = AvitoSearchProvider()
    card = _product(
        provider,
        {"avito_id": "77", "title": "Пальто шерстяное чёрное", "price": 9900,
         "url": "https://www.avito.ru/mos_77", "image": "https://00.img.avito.st/a.jpg",
         "params": "Размер M"},
        "пальто",
    )
    request = LookRequest(style="minimal", mood="calm", height_cm=172, weight_kg=68,
                          budget_rub=50_000, avoid_colors=["white"])
    item = fashion_engine_service.avito_card_to_catalog_item(card, request)
    assert item.sku == "avito_77"
    assert item.url == "https://www.avito.ru/mos_77"
    assert item.image_url == "https://00.img.avito.st/a.jpg"
    assert item.price_rub == 9900
    assert item.category == "outerwear"
    assert item.source == "avito"
    assert item.verification_status == "verified"
    assert item.colors and "white" not in item.colors  # запасной цвет не из исключённых
    assert "M" in item.sizes
    assert item.color_hexes


def test_is_avito_url_and_ensure_links():
    assert fashion_engine_service.is_avito_url("https://www.avito.ru/moskva/x_1")
    assert fashion_engine_service.is_avito_url("https://m.avito.ru/x")
    assert not fashion_engine_service.is_avito_url("https://www.lamoda.ru/p/x")
    assert not fashion_engine_service.is_avito_url("not a url")


@pytest.fixture()
def items(session):
    rows = catalog_service.eligible_items(session)
    assert rows
    return rows


def _look_request(**overrides):
    params = {"style": "grunge", "mood": "bold", "height_cm": 174, "weight_kg": 64,
              "budget_rub": 60_000}
    params.update(overrides)
    return LookRequest(**params)


def test_search_avito_unreachable_uses_snapshot_listings(items, monkeypatch):
    """Живой Авито не отвечает → берём конкретные объявления из снимка выдачи.

    Каждая вещь обязана остаться настоящим объявлением: прямая ссылка, фото,
    город — поэтому резервный режим «по каталогу» здесь не включается.
    """
    monkeypatch.setattr(settings, "avito_enabled", True)
    fashion_engine_service.reset_avito_provider()
    monkeypatch.setattr(
        AvitoSearchProvider, "_fetch_html", lambda self, ru_query: ""
    )
    try:
        result = fashion_engine_service.search({"query": "кожаная куртка"}, items, limit=5)
    finally:
        fashion_engine_service.reset_avito_provider()
    assert result["items"], "резервный режим не должен давать пустую выдачу"
    assert result["engine"]["fallback"] is None
    assert result["engine"]["providers"] == ["avito"]
    assert result["engine"]["feeds"]["snapshot"] > 0
    feeds = set()
    for item in result["items"]:
        assert fashion_engine_service.is_avito_url(item["url"]), item["url"]
        assert item["source"] == "avito"
        # Ссылка ведёт на конкретное объявление, а не на поиск по словам.
        assert item["link_kind"] == "listing", item["url"]
        assert fashion_engine_service.looks_like_listing_url(item["url"]), item["url"]
        listing = item["listing"]
        assert listing and listing["kind"] == "listing"
        feeds.add(item["feed"])
    assert feeds == {"snapshot"}, feeds


def test_search_avito_last_resort_marks_search_links(items, monkeypatch):
    """Ни живой выдачи, ни снимка → подбор по каталогу с честной пометкой."""
    monkeypatch.setattr(settings, "avito_enabled", True)
    monkeypatch.setattr(settings, "avito_snapshot_enabled", False)
    fashion_engine_service.reset_avito_provider()
    monkeypatch.setattr(
        AvitoSearchProvider, "_fetch_html", lambda self, ru_query: ""
    )
    try:
        result = fashion_engine_service.search({"query": "кожаная куртка"}, items, limit=5)
    finally:
        fashion_engine_service.reset_avito_provider()
    assert result["items"], "резервный режим не должен давать пустую выдачу"
    assert result["engine"]["fallback"] == "avito-unreachable"
    assert result["engine"]["providers"] == ["avito"]
    for item in result["items"]:
        assert fashion_engine_service.is_avito_url(item["url"]), item["url"]
        assert item["source"] == "avito"
        # Это последний резерв: ссылка — подборка Авито, и это прямо помечено.
        assert item["link_kind"] == "search"
        assert item["feed"] == "search"
        assert item["listing"]["kind"] == "search"


def test_search_avito_live_path(items, monkeypatch):
    """Живой путь: объявления провайдера проходят движок целиком."""
    monkeypatch.setattr(settings, "avito_enabled", True)
    fashion_engine_service.reset_avito_provider()
    monkeypatch.setattr(AvitoSearchProvider, "_fetch_html", lambda self, ru_query: BIG_SERP_HTML)
    try:
        result = fashion_engine_service.search(
            {"query": "шерстяное пальто", "budget_rub": 60_000}, items, limit=4
        )
    finally:
        fashion_engine_service.reset_avito_provider()
    assert result["items"]
    assert result["engine"]["fallback"] is None
    assert result["engine"]["providers"] == ["avito"]
    for item in result["items"]:
        assert item["url"].startswith("https://www.avito.ru/")
        assert item["verification_status"] == "verified"
        assert item["engine"].get("fashion_score", 0) >= 0
    # Хотя бы одно объявление — с настоящим фото.
    assert any(item["image_url"] for item in result["items"])


def test_generate_look_snapshot_items_are_concrete_listings(items, monkeypatch):
    """Образ при недоступном живом Авито собирается из объявлений снимка."""
    monkeypatch.setattr(settings, "avito_enabled", True)
    fashion_engine_service.reset_avito_provider()
    monkeypatch.setattr(AvitoSearchProvider, "_fetch_html", lambda self, ru_query: "")
    try:
        result = fashion_engine_service.generate_look(items, _look_request())
    finally:
        fashion_engine_service.reset_avito_provider()
    assert len(result.items) >= 3
    assert result.total_rub <= 60_000
    engine = result.diagnostics["engine"]
    assert engine["fallback"] is None
    assert engine["feeds"]["snapshot"] >= len(result.items)
    for item in result.items:
        assert fashion_engine_service.is_avito_url(item["url"]), item["url"]
        # Пользователь открывает конкретное объявление, а не поиск по словам.
        assert item["link_kind"] == "listing", item["url"]
        assert fashion_engine_service.looks_like_listing_url(item["url"]), item["url"]
        assert item["feed"] == "snapshot"
        assert item["image_url"], "у объявления из снимка обязано быть фото"
        listing = item["listing"]
        assert listing and listing["kind"] == "listing"
        assert listing["avito_id"]
        assert listing["captured_at"]


def test_generate_look_last_resort_catalog_marks_search_links(items, monkeypatch):
    """Совсем без объявлений: подбор по каталогу, но с честной пометкой ссылок."""
    monkeypatch.setattr(settings, "avito_enabled", True)
    monkeypatch.setattr(settings, "avito_snapshot_enabled", False)
    fashion_engine_service.reset_avito_provider()
    monkeypatch.setattr(AvitoSearchProvider, "_fetch_html", lambda self, ru_query: "")
    try:
        result = fashion_engine_service.generate_look(items, _look_request())
    finally:
        fashion_engine_service.reset_avito_provider()
    assert len(result.items) >= 3
    assert result.total_rub <= 60_000
    engine = result.diagnostics["engine"]
    assert engine["fallback"] == "avito-unreachable"
    for item in result.items:
        assert fashion_engine_service.is_avito_url(item["url"]), item["url"]
        assert item["link_kind"] == "search"
        assert item["feed"] == "search"


def test_generate_look_avito_live_builds_outfit(items, monkeypatch):
    monkeypatch.setattr(settings, "avito_enabled", True)
    monkeypatch.setattr(settings, "avito_timeout_sec", 2.0)
    fashion_engine_service.reset_avito_provider()
    monkeypatch.setattr(AvitoSearchProvider, "_fetch_html", lambda self, ru_query: BIG_SERP_HTML)
    try:
        result = fashion_engine_service.generate_look(items, _look_request(budget_rub=60_000))
    finally:
        fashion_engine_service.reset_avito_provider()
    assert len(result.items) >= 3
    slots = [item["slot"] for item in result.items]
    assert len(slots) == len(set(slots))
    assert result.total_rub <= 60_000
    assert all(item["url"].startswith("https://www.avito.ru/") for item in result.items)
    engine = result.diagnostics["engine"]
    assert engine["providers"] == ["avito"]
    assert engine.get("fallback") is None
    assert engine["styling_thesis_ru"]
    # Хотя бы одна вещь — с настоящим фото объявления.
    assert any(item["image_url"].startswith("https://") for item in result.items)
