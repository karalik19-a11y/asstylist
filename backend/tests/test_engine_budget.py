"""Tests for the budget optimiser."""

from __future__ import annotations

from app.engine.budget import build_look
from tests.test_engine_ranking import make_item

from app.engine.ranking import ScoredItem


def scored(sku: str, category: str, price: float, score: float) -> ScoredItem:
    return ScoredItem(item=make_item(sku=sku, category=category, price_rub=price), score=score, breakdown={})


SLOT_SPECS = {
    "top": {"weight": 0.3, "required": True, "order": 0},
    "bottom": {"weight": 0.3, "required": True, "order": 1},
    "shoes": {"weight": 0.3, "required": True, "order": 2},
    "bag": {"weight": 0.1, "required": False, "order": 3},
}


def test_stays_within_budget():
    candidates = {
        "top": [scored("T1", "top", 40_000, 0.9), scored("T2", "top", 5_000, 0.5)],
        "bottom": [scored("B1", "bottom", 40_000, 0.9), scored("B2", "bottom", 6_000, 0.5)],
        "shoes": [scored("S1", "shoes", 30_000, 0.9), scored("S2", "shoes", 7_000, 0.5)],
        "bag": [scored("G1", "bag", 20_000, 0.8)],
    }
    draft = build_look(candidates, SLOT_SPECS, budget_rub=25_000)
    assert draft.total_rub <= 25_000
    assert not draft.over_budget
    assert set(draft.picked) >= {"top", "bottom", "shoes"}


def test_spends_remainder_on_best_upgrade():
    candidates = {
        "top": [scored("T1", "top", 35_000, 0.95), scored("T2", "top", 3_000, 0.5)],
        "bottom": [scored("B1", "bottom", 5_000, 0.6)],
        "shoes": [scored("S1", "shoes", 5_000, 0.6)],
        "bag": [scored("G1", "bag", 4_000, 0.5)],
    }
    draft = build_look(candidates, SLOT_SPECS, budget_rub=50_000)
    assert draft.picked["top"].sku == "T1"
    assert draft.total_rub > 45_000
    assert draft.total_rub <= 50_000


def test_drops_optional_slot_when_required():
    candidates = {
        "top": [scored("T1", "top", 9_000, 0.9)],
        "bottom": [scored("B1", "bottom", 9_000, 0.9)],
        "shoes": [scored("S1", "shoes", 9_000, 0.9)],
        "bag": [scored("G1", "bag", 9_000, 0.9)],
    }
    draft = build_look(candidates, SLOT_SPECS, budget_rub=30_000)
    assert draft.total_rub <= 30_000
    assert "bag" not in draft.picked or draft.total_rub <= 30_000


def test_reports_over_budget_when_impossible():
    candidates = {
        "top": [scored("T1", "top", 50_000, 0.9)],
        "bottom": [scored("B1", "bottom", 50_000, 0.9)],
        "shoes": [scored("S1", "shoes", 50_000, 0.9)],
    }
    draft = build_look(candidates, SLOT_SPECS, budget_rub=10_000)
    assert draft.over_budget
    assert any("Бюджет превышен" in w for w in draft.warnings)


def test_deterministic():
    candidates = {
        "top": [scored("T1", "top", 8_000, 0.8), scored("T2", "top", 6_000, 0.8)],
        "bottom": [scored("B1", "bottom", 7_000, 0.7)],
        "shoes": [scored("S1", "shoes", 9_000, 0.75)],
        "bag": [scored("G1", "bag", 5_000, 0.6)],
    }
    first = build_look(candidates, SLOT_SPECS, 30_000)
    second = build_look(candidates, SLOT_SPECS, 30_000)
    assert first.total_rub == second.total_rub
    assert {k: v.sku for k, v in first.picked.items()} == {k: v.sku for k, v in second.picked.items()}


def test_missing_slot_is_reported():
    candidates = {"top": [scored("T1", "top", 5_000, 0.8)], "bottom": [scored("B1", "bottom", 5_000, 0.8)]}
    draft = build_look(candidates, SLOT_SPECS, 30_000)
    assert any("shoes" in w for w in draft.warnings)
