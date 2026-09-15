"""Интеграция движка ASSTYLIST с приложением.

Проверяем главное требование: поиск и подбор вещей в asStylist выполняет движок
(``app.fashion_engine``) поверх проверенного каталога, а приложение удерживает
бюджет, обязательные слоты и слой верификации.
"""

from __future__ import annotations

import json

import pytest

from app.config import settings
from app.engine.look_builder import LookGenerationError, LookRequest, generate_look
from app.fashion_engine.search.multi_pass_search import DiscoveryResult
from app.fashion_engine.types import OutfitResult, UserStyleProfile
from app.services import catalog_service, fashion_engine_service
from app.services.look_service import build_look_result, to_engine_request

STYLES = ["minimal", "grunge", "old_money", "streetwear", "romantic"]


@pytest.fixture()
def items(session):
    rows = catalog_service.eligible_items(session)
    assert rows, "seed catalog should produce eligible products"
    return rows


def look_request(**overrides) -> LookRequest:
    params = {"style": "grunge", "mood": "bold", "height_cm": 174, "weight_kg": 64, "budget_rub": 60_000}
    params.update(overrides)
    return LookRequest(**params)


@pytest.mark.parametrize("style", STYLES)
def test_look_is_built_by_the_fashion_engine(items, style):
    request = look_request(style=style)
    result = fashion_engine_service.generate_look(items, request)

    engine = result.diagnostics["engine"]
    assert engine["pipeline"] == fashion_engine_service.PIPELINE
    assert engine["engine_version"]
    assert engine["styling_thesis"]
    assert engine["styling_thesis_ru"]
    assert engine["outfit_score"] > 0
    assert engine["critic_decision"] in {"APPROVE", "REBUILD"}
    assert engine["queries_total"] >= 1
    assert 1 <= len(engine["queries_used"]) <= engine["queries_total"]
    assert engine["profile"]["nicheLevel"] == result.diagnostics["engine"]["niche_level"]

    assert len(result.items) >= 3
    slots = [item["slot"] for item in result.items]
    assert len(slots) == len(set(slots))
    for item in result.items:
        meta = item["engine"]
        assert meta["role"] in {"hero", "base", "layer", "footwear", "accessory"}
        assert meta["role_label"]
        assert meta["taste_category"]
        assert 0 <= meta["fashion_score"] <= 100
        assert item["breakdown"]["engine"] == round(meta["fashion_score"] / 100, 3)
        assert item["reasons"][0].startswith("Разбор:")


@pytest.mark.parametrize("budget", [15_000, 25_000, 50_000, 100_000])
def test_engine_respects_the_budget(items, budget):
    result = fashion_engine_service.generate_look(items, look_request(budget_rub=budget))
    assert result.total_rub <= budget
    assert result.diagnostics["budget"]["total_rub"] == result.total_rub
    assert result.diagnostics["budget"]["budget_rub"] == budget
    assert len(result.items) >= 3
    catalog_skus = {item.sku for item in items}
    assert all(item["sku"] in catalog_skus for item in result.items)


def test_free_text_query_reaches_the_engine(items):
    request = look_request(query="прозрачный верх и кожаная куртка")
    result = fashion_engine_service.generate_look(items, request)
    engine = result.diagnostics["engine"]

    first_query = engine["queries_used"][0]
    assert "прозрачный верх и кожаная куртка" in first_query
    # Русский запрос переводится в словарь движка: sheer/leather из лексикона.
    assert any(token in first_query for token in ("sheer", "leather"))
    assert engine["candidates"]["validated"] > 0
    assert engine["candidates"]["raw_items"] > engine["candidates"]["validated"]


def test_engine_generation_is_deterministic(items):
    request = look_request(style="old_money", mood="elegant", budget_rub=80_000)
    first = fashion_engine_service.generate_look(items, request)
    second = fashion_engine_service.generate_look(items, request)
    assert [item["sku"] for item in first.items] == [item["sku"] for item in second.items]
    assert first.total_rub == second.total_rub
    assert first.score == second.score
    assert first.diagnostics["engine"]["styling_thesis"] == second.diagnostics["engine"]["styling_thesis"]


def test_score_is_a_blend_of_app_and_engine(items):
    result = fashion_engine_service.generate_look(items, look_request())
    engine = result.diagnostics["engine"]
    weight = settings.fashion_engine_score_weight
    expected = round((1 - weight) * engine["app_score"] + weight * engine["outfit_score"], 1)
    assert result.score == pytest.approx(expected, abs=0.11)
    assert engine["final_score"] == result.score


def test_app_guard_adds_missing_required_slots(items):
    """Слоты, которые движок не закрыл сам, добирает бюджетный оптимизатор."""
    result = fashion_engine_service.generate_look(items, look_request(budget_rub=100_000))
    slots = {item["slot"] for item in result.items}
    assert {"top", "bottom", "shoes"} <= slots
    budget = result.diagnostics["budget"]
    assert budget["engine_outfit_kept"] <= budget["engine_outfit_items"]
    if result.diagnostics["engine"]["repair"]:
        assert result.diagnostics["engine"]["repair"] == "budget-optimiser"


def test_to_engine_request_passes_query_and_niche_from_payload():
    request = to_engine_request({"query": "  индустриальный образ  ", "niche_level": "82"}, None)
    assert request.query == "индустриальный образ"
    assert request.niche_level == 82
    assert to_engine_request({"niche_level": ""}, None).niche_level is None
    assert to_engine_request({}, None).query is None


def test_look_service_uses_the_engine_and_records_it(items):
    result = build_look_result(items, look_request())
    engine = result.diagnostics["engine"]
    assert engine["pipeline"] == fashion_engine_service.PIPELINE
    assert engine["enabled"] is True
    assert engine["fallback"] is None


def test_look_service_falls_back_when_the_engine_breaks(items, monkeypatch):
    def boom(*_args, **_kwargs):
        raise LookGenerationError("движок недоступен")

    monkeypatch.setattr(fashion_engine_service, "generate_look", boom)
    result = build_look_result(items, look_request())
    engine = result.diagnostics["engine"]
    assert engine["pipeline"] == "legacy-ranker"
    assert engine["fallback"] == "fashion-engine-error"
    assert "движок недоступен" in engine["fallback_reason"]
    assert any("резервным ранжировщиком" in warning for warning in result.diagnostics["warnings"])
    assert len(result.items) >= 3


def test_strict_engine_mode_raises_instead_of_falling_back(items, monkeypatch):
    def boom(*_args, **_kwargs):
        raise LookGenerationError("движок недоступен")

    monkeypatch.setattr(fashion_engine_service, "generate_look", boom)
    monkeypatch.setattr(settings, "fashion_engine_mode", "engine")
    with pytest.raises(LookGenerationError):
        build_look_result(items, look_request())


def test_legacy_mode_skips_the_engine(items, monkeypatch):
    monkeypatch.setattr(settings, "fashion_engine_mode", "legacy")
    result = build_look_result(items, look_request())
    engine = result.diagnostics["engine"]
    assert engine["pipeline"] == "legacy-ranker"
    assert engine["enabled"] is False
    assert len(result.items) >= 3
    legacy = generate_look(items, look_request())
    assert [item["sku"] for item in result.items] == [item["sku"] for item in legacy.items]


def test_rerank_for_slot_puts_the_engine_pick_first(items, session):
    """Замена вещи идёт по движку: его вещь слота — первая, остальное — альтернативы."""
    request = look_request(style="techwear", season="winter")
    prepared = __import__("app.engine.look_builder", fromlist=["prepare_pool"]).prepare_pool(items, request)
    run = fashion_engine_service.run_engine(prepared, request)

    engine_skus = {card.sku for card in run.outfit.items}
    engine_shoes = {sku for sku in engine_skus if sku and sku.startswith("SH-")}
    assert engine_shoes, "движок должен выбрать обувь в образ"

    class FakeLook:
        style = request.style
        mood = request.mood
        occasion = request.occasion
        season = request.season
        presentation = request.presentation
        height_cm = request.height_cm
        weight_kg = request.weight_kg
        budget_rub = request.budget_rub
        ranking_json = json.dumps({"engine": {"roles": {sku: "footwear" for sku in engine_skus}}})

    pool = prepared.candidates_by_slot["shoes"]
    reranked = fashion_engine_service.rerank_for_slot(pool, "shoes", look=FakeLook(), ctx=prepared.ctx)

    assert reranked[0].sku in engine_shoes
    assert reranked[0].breakdown.get("engine") is not None
    assert reranked[0].breakdown.get("engineOutfit") is True
    picked = [entry for entry in reranked if entry.breakdown.get("engineOutfit")]
    assert [entry.sku for entry in picked] == [entry.sku for entry in sorted(picked, key=lambda e: -e.score)]

    # Без сохранённого образа движка порядок остаётся по гибридной оценке.
    class BareLook(FakeLook):
        ranking_json = "{}"

    fallback = fashion_engine_service.rerank_for_slot(pool, "shoes", look=BareLook(), ctx=prepared.ctx)
    assert [entry.sku for entry in fallback] == [entry.sku for entry in sorted(fallback, key=lambda e: -e.score)]
    assert all(entry.breakdown.get("engine") is not None for entry in fallback)


def test_search_returns_engine_payload(items):
    payload = fashion_engine_service.search(
        {
            "query": "индустриальный образ с прозрачным верхом",
            "style": "grunge",
            "budget_rub": 60_000,
            "presentation": "feminine",
            "season": "autumn",
        },
        items,
        limit=6,
    )
    engine = payload["engine"]
    assert engine["pipeline"] == fashion_engine_service.PIPELINE
    assert engine["styling_thesis"]
    assert engine["styling_thesis_ru"]
    assert engine["outfit_score"] > 0
    assert engine["queries_used"]
    assert engine["candidates"]["validated"] > 0
    assert payload["thesis_options"]

    assert payload["items"], "поиск должен вернуть вещи каталога"
    assert len(payload["items"]) <= 6
    skus = {item.sku for item in items}
    for entry in payload["items"]:
        assert entry["sku"] in skus
        assert entry["score"] > 0
        assert entry["engine"]["taste_category"]
        assert entry["reasons"]
    assert payload["suggested_request"]["niche_level"] == engine["niche_level"]


def test_search_rejects_a_too_short_query(items):
    with pytest.raises(LookGenerationError):
        fashion_engine_service.search({"query": "я"}, items)


def test_search_falls_back_to_the_app_order_when_engine_is_empty(items, monkeypatch):
    """Если движок не нашёл ни одной вещи, поиск отдаёт порядок приложения."""
    empty_run = fashion_engine_service.EngineRun(
        query="индустриальный образ",
        profile=UserStyleProfile(),
        discovery=DiscoveryResult(
            products=[],
            references=[],
            queries_used=["индустриальный образ"],
            raw_items=0,
            considered=0,
            dropped={},
        ),
        outfit=OutfitResult.empty("индустриальный образ", "no products"),
        cards={},
    )
    monkeypatch.setattr(fashion_engine_service, "run_engine", lambda *_args, **_kwargs: empty_run)

    payload = fashion_engine_service.search({"query": "индустриальный образ"}, items, limit=4)
    assert payload["engine"]["fallback"] == "engine-empty"
    assert payload["items"], "должен сработать резервный порядок каталога"
    assert all(item["engine"] == {} for item in payload["items"])
