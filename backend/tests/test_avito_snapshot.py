"""Снимок выдачи Авито: настоящие объявления с фото и прямыми ссылками.

Авито может закрыться капчей для IP сервера — тогда образ всё равно обязан
состоять из конкретных объявлений: название, цена, фото с CDN Авито и ссылка
на страницу объявления. Эти тесты проверяют и сам файл снимка, и провайдер
поиска по нему (без единого сетевого запроса).
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

from app.fashion_engine.search.providers.avito_snapshot_provider import AvitoSnapshotProvider
from app.fashion_engine.search.provider import SearchContext
from app.fashion_engine.types import UserStyleProfile

SNAPSHOT_PATH = pathlib.Path(__file__).resolve().parents[1] / "app" / "catalog" / "avito_listings.json"

#: Ссылка на конкретное объявление: .../gorod/kategoriya/slug_<id объявления>.
LISTING_URL = re.compile(r"^https://www\.avito\.ru/[a-z0-9_-]+/odezhda_obuv_aksessuary/[a-z0-9_\-]+_\d{6,}$")


def _snapshot() -> dict:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def test_snapshot_contains_only_real_listings():
    data = _snapshot()
    listings = data["listings"]
    assert len(listings) >= 10, "снимок должен покрывать несколько категорий одежды"
    assert data.get("captured_at")

    for entry in listings:
        assert LISTING_URL.match(entry["url"]), entry["url"]
        assert "?q=" not in entry["url"], entry["url"]
        assert float(entry["price"]) > 0
        assert entry["image"].startswith("https://") and "img.avito.st" in entry["image"]
        assert len(entry["title"]) >= 3
        assert entry.get("city")
        assert entry.get("query")
        assert entry.get("captured_at")

    # Разные категории, а не «одни пальто»: образ собирается из вещей по слотам.
    queries = {entry["query"] for entry in listings}
    assert {"пальто женское", "джинсы", "футболка", "кроссовки"} <= queries


@pytest.fixture()
def snapshot(tmp_path):
    """Провайдер снимка: путь к файлу явный, сеть не нужна."""
    return AvitoSnapshotProvider(SNAPSHOT_PATH, max_results=12)


def _profile() -> UserStyleProfile:
    return UserStyleProfile(
        niche_level=60,
        aesthetics=["Deconstructed 90s Minimalism"],
        budget_max=60_000,
        currency="RUB",
        occasion="everyday",
        fit_preference="straight",
        gender="unisex",
        colors=["black", "grey"],
        preferred_silhouette=["straight"],
        disliked_items=[],
        height_cm=174,
        notes=[],
    )


def test_snapshot_search_finds_jeans_with_photo_and_link(snapshot):
    cards = snapshot.search("джинсы", SearchContext(user_profile=_profile(), limit=6, categories=["bottom"]))
    assert cards, "по запросу «джинсы» обязана найтись конкретная вещь"
    for card in cards:
        assert LISTING_URL.match(card.source_url), card.source_url
        assert card.image.startswith("https://")
        assert card.price and card.price > 0
        assert card.meta["snapshot"] is True
        assert card.meta["live"] is False
        assert card.meta["avito_id"]
        assert card.meta["city"]
        assert card.meta["listing_url_kind"] == "listing"
    assert any("джинс" in card.name.lower() for card in cards)


def test_snapshot_keeps_brand_from_file(snapshot):
    """Бренд берём из снимка целиком, а не из первого слова заголовка."""
    cards = snapshot.search("джинсовая куртка", SearchContext(user_profile=_profile(), limit=6))
    brands = {card.name: card.brand for card in cards}
    forte = next((brand for name, brand in brands.items() if "Forte Couture" in name), None)
    assert forte == "Forte Couture", brands

    boots = snapshot.search("ботинки", SearchContext(user_profile=_profile(), limit=6))
    karl = next((card.brand for card in boots if "Karl Lagerfeld" in card.name), None)
    assert karl == "Karl Lagerfeld", [card.brand for card in boots]


def test_snapshot_search_matches_keywords_not_categories(snapshot):
    """Поиск идёт по словам и описанию: «кашемир» не обязан быть категорией."""
    cards = snapshot.search("шерстяное пальто", SearchContext(user_profile=_profile(), limit=5))
    names = " ".join(card.name.lower() for card in cards)
    assert "пальто" in names, names
    assert all(card.meta["query_match"] >= 0 for card in cards)


def test_snapshot_appearance_and_condition_are_scored(snapshot):
    cards = snapshot.search("пальто", SearchContext(user_profile=_profile(), limit=4))
    assert cards
    for card in cards:
        traits = card.meta["traits"]
        # Состояние берётся из строки параметров («Новое с биркой», «Отличное»)
        # и всегда имеет числовую оценку для скоринга.
        assert traits["condition"]
        assert 0.0 <= float(traits["condition_score"]) <= 1.0
        assert 0.0 <= card.meta["appearance"]["score"] <= 1.0
        assert card.meta["selection_score"] >= 0


def test_snapshot_respects_budget(snapshot):
    cheap = UserStyleProfile(
        niche_level=40,
        aesthetics=[],
        budget_max=5_000,
        currency="RUB",
        occasion="everyday",
        fit_preference="regular",
        gender="unisex",
        colors=[],
        preferred_silhouette=[],
        disliked_items=[],
        height_cm=170,
        notes=[],
    )
    cards = snapshot.search("джинсы", SearchContext(user_profile=cheap, limit=5))
    assert cards
    assert all(card.price <= 5_000 * 1.25 for card in cards)


def test_snapshot_never_returns_search_links(snapshot):
    """Ссылка на подборку Авито — не товар: провайдер такие записи отбрасывает."""
    cards = snapshot.search("платье", SearchContext(user_profile=_profile(), limit=8))
    assert cards
    for card in cards:
        assert "?q=" not in card.source_url
        assert "/favorites" not in card.source_url
        assert LISTING_URL.match(card.source_url)
