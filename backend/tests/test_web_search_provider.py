"""Тесты живого WebSearchProvider: фид, SerpAPI, Google CSE — всё с моком сети."""

from __future__ import annotations

import pytest

from app.fashion_engine.search.provider import SearchContext
from app.fashion_engine.search.providers import web_search_provider as mod
from app.fashion_engine.search.providers.web_search_provider import (
    WebSearchProvider,
    _detect_currency,
    _parse_price,
)


@pytest.fixture()
def serpapi_payload():
    return {
        "shopping_results": [
            {
                "title": "Пальто шерстяное верблюжье",
                "source": "Lamoda",
                "price": "24 900 ₽",
                "extracted_price": 24900.0,
                "thumbnail": "https://cdn.example/img1.jpg",
                "product_link": "https://shop.example/coat-1",
            },
            {
                "title": "Пальто оверсайз серое",
                "source": "Wildberries",
                "price": "9 990 ₽",
                "extracted_price": 9990.0,
                "link": "https://shop.example/coat-2",
                "thumbnail": "https://cdn.example/img2.jpg",
            },
            {"title": "Позиция без цены", "link": "https://shop.example/nope"},
        ]
    }


def test_price_parsing():
    assert _parse_price("25 999 ₽") == 25999.0
    assert _parse_price("$1,290.50") == 1290.5
    assert _parse_price("1.290,50 €") == 1290.5
    assert _parse_price(12990) == 12990.0
    assert _parse_price(0) is None
    assert _parse_price(None) is None
    assert _parse_price("цена по запросу") is None


def test_currency_detection():
    assert _detect_currency("1 290,50 €") == "EUR"
    assert _detect_currency("$99") == "USD"
    assert _detect_currency("25 999 ₽") == "RUB"
    assert _detect_currency("1299 руб.") == "RUB"
    assert _detect_currency("1290") == "RUB"


def test_no_sources_returns_empty():
    provider = WebSearchProvider()
    assert provider.available() is False
    assert provider.search("пальто", SearchContext()) == []


def test_serpapi_search(monkeypatch, serpapi_payload):
    calls: list[dict] = []

    def fake_get(url, *, params, timeout):
        calls.append(params)
        if "serpapi.com" in url:
            return serpapi_payload
        return None

    monkeypatch.setattr(mod, "_http_get_json", fake_get)
    provider = WebSearchProvider(serpapi_key="test-key")
    items = provider.search("шерстяное пальто", SearchContext(limit=5))

    assert calls and calls[0]["engine"] == "google_shopping"
    assert calls[0]["q"] == "шерстяное пальто"
    assert len(items) == 2  # позиция без цены отброшена

    coat = items[0]
    assert coat.name == "Пальто шерстяное верблюжье"
    assert coat.price == 24900.0
    assert coat.currency == "RUB"
    assert coat.image == "https://cdn.example/img1.jpg"
    assert coat.source_url.startswith("https://")
    assert coat.provider == ""  # метку ставит MultiPassSearch
    assert coat.source_type == "web"
    assert coat.confidence >= 0.6
    # релевантная позиция («шерстяное пальто» в названии) идёт первой
    assert "пальто" in items[0].name.lower()


def test_network_failure_returns_empty(monkeypatch):
    def failing(*args, **kwargs):
        raise AssertionError("should not be called at all")  # см. ниже

    def none_get(url, *, params, timeout):
        return None

    monkeypatch.setattr(mod, "_http_get_json", none_get)
    provider = WebSearchProvider(serpapi_key="k", google_key="g", google_cx="cx", feed_url="https://feed.example/x.json")
    assert provider.available() is True
    assert provider.search("пальто", SearchContext()) == []
    del failing


def test_partner_feed(monkeypatch):
    feed = [
        {"name": "Куртка кожаная", "brand": "Partner", "price": 320, "currency": "EUR",
         "url": "https://partner.example/jacket", "image": "https://partner.example/j.jpg",
         "tags": ["leather", "black", "jacket"]},
        {"name": "Шарф шерстяной", "brand": "Partner", "price": 990, "currency": "RUB",
         "url": "https://partner.example/scarf", "image": ""},
    ]

    def fake_get(url, *, params, timeout):
        return feed

    monkeypatch.setattr(mod, "_http_get_json", fake_get)
    provider = WebSearchProvider(feed_url="https://partner.example/feed.json", fx_rates={"EUR": 100.0})
    items = provider.search("leather black jacket", SearchContext(limit=5))

    assert len(items) == 1
    jacket = items[0]
    assert jacket.price == 32000.0  # EUR → RUB
    assert jacket.currency == "RUB"
    assert jacket.meta["price_original"] == "320 EUR"
    assert jacket.confidence == 0.85


def test_google_cse(monkeypatch):
    payload = {
        "items": [
            {
                "title": "Ботинки челси коричневые купить",
                "link": "https://market.example/boots",
                "displayLink": "market.example",
                "pagemap": {
                    "offer": [{"price": "16990", "pricecurrency": "RUB"}],
                    "cse_image": [{"src": "https://market.example/boots.jpg"}],
                },
            }
        ]
    }
    monkeypatch.setattr(mod, "_http_get_json", lambda url, *, params, timeout: payload)
    provider = WebSearchProvider(google_key="k", google_cx="cx")
    items = provider.search("ботинки челси", SearchContext(limit=3))
    assert len(items) == 1
    assert items[0].price == 16990.0
    assert items[0].image.endswith("boots.jpg")


def test_validate_item():
    provider = WebSearchProvider()
    from app.fashion_engine.types import ProductItem

    bad = ProductItem(
        id="x", name="", brand="", category="top", price=0, currency="RUB",
        image="", source_url="", source_type="web", availability="", confidence=0.6,
    )
    assert provider.validate_item(bad).valid is False
