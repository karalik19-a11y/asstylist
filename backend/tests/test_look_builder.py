"""End-to-end tests of the look generator against the real seed catalog."""

from __future__ import annotations

import pytest

from app.engine.look_builder import LookGenerationError, LookRequest, generate_look
from app.engine.options import STYLE_OPTIONS, MOOD_OPTIONS
from app.services import catalog_service


@pytest.fixture()
def items(session):
    rows = catalog_service.eligible_items(session)
    assert rows, "seed catalog should produce eligible products"
    return rows


@pytest.mark.parametrize("budget", [12_000, 25_000, 50_000, 100_000])
def test_look_fits_the_budget(items, budget):
    request = LookRequest(style="minimal", mood="calm", height_cm=175, weight_kg=70, budget_rub=budget)
    result = generate_look(items, request)

    assert result.total_rub <= budget
    assert len(result.items) >= 3
    slots = [item["slot"] for item in result.items]
    assert len(slots) == len(set(slots)), "each slot must appear at most once"
    assert 0 < result.score <= 100
    assert result.verdict["grade"] in {"A", "B", "C", "D"}
    assert result.summary
    assert result.tips


@pytest.mark.parametrize("style", [option["id"] for option in STYLE_OPTIONS])
def test_every_style_produces_a_look(items, style):
    request = LookRequest(style=style, mood="calm", height_cm=170, weight_kg=65, budget_rub=60_000)
    result = generate_look(items, request)
    assert len(result.items) >= 3
    assert result.diagnostics["candidates_total"] > 0


@pytest.mark.parametrize("mood", [option["id"] for option in MOOD_OPTIONS])
def test_every_mood_produces_a_look(items, mood):
    request = LookRequest(style="streetwear", mood=mood, height_cm=180, weight_kg=80, budget_rub=40_000)
    result = generate_look(items, request)
    assert len(result.items) >= 3


def test_generation_is_deterministic(items):
    request = LookRequest(style="old_money", mood="elegant", height_cm=178, weight_kg=74, budget_rub=80_000)
    first = generate_look(items, request)
    second = generate_look(items, request)
    assert [i["sku"] for i in first.items] == [i["sku"] for i in second.items]
    assert first.total_rub == second.total_rub
    assert first.score == second.score


def test_items_carry_reasons_and_breakdown(items):
    request = LookRequest(style="minimal", mood="confident", height_cm=175, weight_kg=70, budget_rub=50_000)
    result = generate_look(items, request)
    for item in result.items:
        assert item["reasons"], "every item must be explained"
        assert item["breakdown"], "every item must expose its score breakdown"
        assert item["verification_status"] in {"verified", "warning"}
        assert item["price_rub"] > 0
        assert item["url"].startswith("https://")


def test_exclude_skus_changes_the_look(items):
    base_request = LookRequest(style="minimal", mood="calm", height_cm=175, weight_kg=70, budget_rub=50_000)
    base = generate_look(items, base_request)
    hero_sku = base.items[0]["sku"]

    changed = generate_look(items, LookRequest(**{**base_request.__dict__, "exclude_skus": [hero_sku]}))
    assert hero_sku not in [item["sku"] for item in changed.items]


def test_winter_picks_a_layered_plan(items):
    request = LookRequest(style="minimal", mood="calm", season="winter", height_cm=175, weight_kg=70, budget_rub=60_000)
    result = generate_look(items, request)
    assert result.plan == "layered"
    assert any(item["slot"] == "outerwear" for item in result.items)


def test_summer_can_pick_a_dress_plan(items):
    request = LookRequest(
        style="romantic", mood="playful", occasion="date", season="summer", height_cm=168, weight_kg=58, budget_rub=45_000
    )
    result = generate_look(items, request)
    assert result.plan in {"dress", "light"}


def test_photo_analysis_shifts_the_palette(items):
    vision = {
        "ok": True,
        "person_detected": True,
        "shoulder_hip_ratio": 1.25,
        "dominant_colors": ["camel", "sand"],
        "temperature": "warm",
        "depth": "light",
        "chroma": "soft",
        "palette_confidence": 0.8,
        "source": "local",
    }
    with_photo = generate_look(
        items, LookRequest(style="old_money", mood="calm", height_cm=175, weight_kg=70, budget_rub=70_000, vision=vision)
    )
    assert with_photo.palette.temperature == "warm"
    assert with_photo.body.silhouette == "athletic"
    assert with_photo.body.confidence > 0.5


def test_empty_catalog_raises():
    with pytest.raises(LookGenerationError):
        generate_look([], LookRequest(style="minimal", mood="calm", height_cm=175, weight_kg=70, budget_rub=50_000))


def test_all_items_excluded_raises(items):
    every_sku = [item.sku for item in items]
    with pytest.raises(LookGenerationError):
        generate_look(
            items,
            LookRequest(style="minimal", mood="calm", height_cm=175, weight_kg=70, budget_rub=50_000, exclude_skus=every_sku),
        )


def test_broken_products_never_reach_a_look(items):
    bad_skus = {"BAD-001", "BAD-002", "BAD-003", "BAD-004"}
    request = LookRequest(style="minimal", mood="calm", height_cm=175, weight_kg=70, budget_rub=100_000)
    result = generate_look(items, request)
    assert not bad_skus & {item["sku"] for item in result.items}
    assert all(item["sku"] not in bad_skus for item in result.items)


def test_items_are_actually_scored(items):
    """Regression: an empty weight map made every item score 0.0, which turned
    the optimiser into "cheapest item per slot" and left 80% of the budget."""
    request = LookRequest(style="old_money", mood="elegant", height_cm=182, weight_kg=78, budget_rub=75_000)
    result = generate_look(items, request)

    assert all(item["score"] > 0 for item in result.items), result.items
    assert result.total_rub > request.budget_rub * 0.5
    assert result.budget_rub >= result.total_rub


def test_default_weights_are_used_when_none_given(items):
    request = LookRequest(style="minimal", mood="calm", height_cm=175, weight_kg=70, budget_rub=50_000)
    assert request.weights is None
    result = generate_look(items, request)
    weights = result.diagnostics["weights"]
    assert weights
    assert abs(sum(weights.values()) - 1.0) < 1e-6


def test_best_scoring_items_beat_the_cheapest_ones(items):
    """At a comfortable budget the engine must not simply pick the cheapest row."""
    request = LookRequest(style="old_money", mood="elegant", height_cm=182, weight_kg=78, budget_rub=90_000)
    result = generate_look(items, request)
    prices = [item["price_rub"] for item in result.items]
    assert max(prices) > 8_000


def test_masculine_look_has_no_skirts_or_dresses(items):
    request = LookRequest(
        style="business_casual",
        mood="confident",
        presentation="masculine",
        occasion="work",
        season="winter",
        height_cm=185,
        weight_kg=85,
        budget_rub=80_000,
    )
    result = generate_look(items, request)
    categories = {item["category"] for item in result.items}
    assert "dress" not in categories
    feminine = {"BT-005", "BT-006", "BT-012", "SH-006", "SH-008", "SH-012", "TP-006", "TP-008"}
    assert not feminine & {item["sku"] for item in result.items}
