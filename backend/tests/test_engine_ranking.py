"""Tests for the Fashion Ranking Engine scoring layer."""

from __future__ import annotations

from app.engine.body import analyze_body
from app.engine.palette import analyze_palette
from app.engine.ranking import (
    CatalogItem,
    RankingContext,
    hard_exclusions,
    look_cohesion,
    look_score,
    rank_candidates,
    score_item,
    style_verdict,
)


def make_item(**kwargs) -> CatalogItem:
    base = dict(
        product_id=1,
        sku="T-001",
        category="top",
        name="Тестовая футболка",
        brand="Test",
        price_rub=5000.0,
        url="https://www.lamoda.ru/p/t-001",
        image_url="",
        colors=["black"],
        color_hexes=["#111114"],
        styles=["minimal"],
        moods=["calm"],
        silhouettes=["all"],
        gendered=[],
        seasons=["all"],
        sizes=["S", "M", "L"],
        fit="regular",
        formality=1,
        rating=4.5,
        reviews_count=120,
        verification_status="verified",
        verification_score=0.95,
        source="lamoda",
    )
    base.update(kwargs)
    return CatalogItem(**base)


def make_context(**kwargs) -> RankingContext:
    defaults = dict(
        style="minimal",
        mood="calm",
        occasion="everyday",
        season="all",
        presentation="unisex",
        palette=analyze_palette(),
        body=analyze_body(175, 70),
        weights={
            "style": 0.28,
            "mood": 0.15,
            "silhouette": 0.16,
            "color": 0.15,
            "formality": 0.08,
            "season": 0.05,
            "value": 0.08,
            "verification": 0.05,
        },
    )
    defaults.update(kwargs)
    return RankingContext.build(**defaults)


def test_exact_style_beats_affinity_and_alien():
    ctx = make_context()
    exact = score_item(make_item(styles=["minimal"]), ctx)
    affinity = score_item(make_item(sku="T-002", styles=["business_casual"]), ctx)
    alien = score_item(make_item(sku="T-003", styles=["boho"]), ctx)
    assert exact.score > affinity.score > alien.score
    assert exact.breakdown["style"] == 1.0
    assert 0.4 < affinity.breakdown["style"] < 0.7
    assert alien.breakdown["style"] < 0.2


def test_hard_exclusions():
    ctx = make_context()
    assert "over_budget" in hard_exclusions(make_item(price_rub=999_999), ctx, budget_rub=50_000)
    assert "not_verified" in hard_exclusions(make_item(verification_status="failed"), ctx, budget_rub=50_000)
    assert "avoided_colors" in hard_exclusions(make_item(colors=["mustard"]), make_context(avoid_colors=["mustard"]), budget_rub=50_000)
    assert "size_unavailable" in hard_exclusions(make_item(sizes=["XL"]), make_context(size="S"), budget_rub=50_000)
    assert hard_exclusions(make_item(), ctx, budget_rub=50_000) == []


def test_ranking_is_deterministic_and_sorted():
    ctx = make_context()
    items = [
        make_item(sku="A", styles=["minimal"], price_rub=4000),
        make_item(sku="B", styles=["boho"], price_rub=3000),
        make_item(sku="C", styles=["minimal"], price_rub=9000),
    ]
    first, _ = rank_candidates(items, ctx, 50_000)
    second, _ = rank_candidates(list(reversed(items)), ctx, 50_000)
    assert [s.sku for s in first] == [s.sku for s in second]
    scores = [s.score for s in first]
    assert scores == sorted(scores, reverse=True)


def test_rejected_items_are_reported_not_scored():
    ctx = make_context()
    ranked, rejected = rank_candidates([make_item(), make_item(sku="X", price_rub=999_999)], ctx, 50_000)
    assert [s.sku for s in ranked] == ["T-001"]
    assert rejected[0]["sku"] == "X"
    assert "over_budget" in rejected[0]["reasons"]


def test_cohesion_rewards_matching_items():
    ctx = make_context()
    matched = [
        score_item(make_item(sku="A", styles=["minimal"], colors=["black"]), ctx),
        score_item(make_item(sku="B", category="bottom", styles=["minimal"], colors=["charcoal"]), ctx),
    ]
    mixed = [
        score_item(make_item(sku="A", styles=["minimal"], colors=["black"]), ctx),
        score_item(make_item(sku="B", category="bottom", styles=["boho"], colors=["orange"]), ctx),
    ]
    assert look_cohesion(matched, ctx)["overall"] > look_cohesion(mixed, ctx)["overall"]
    assert look_score(matched, look_cohesion(matched, ctx)) > look_score(mixed, look_cohesion(mixed, ctx))


def test_score_breakdown_covers_all_weights():
    ctx = make_context()
    breakdown = score_item(make_item(), ctx).breakdown
    assert set(breakdown) == set(ctx.weights)
    assert all(0.0 <= value <= 1.0 for value in breakdown.values())


def test_verdict_bands():
    assert style_verdict(95)["grade"] == "A"
    assert style_verdict(80)["grade"] == "B"
    assert style_verdict(70)["grade"] == "C"
    assert style_verdict(40)["grade"] == "D"


def test_masculine_presentation_excludes_feminine_items():
    ctx = make_context(presentation="masculine")
    skirt = make_item(sku="SK-1", category="bottom", gendered=["feminine"])
    shirt = make_item(sku="SH-1", category="top")
    dress = make_item(sku="DR-1", category="dress")

    assert "presentation_mismatch" in hard_exclusions(skirt, ctx, 50_000)
    assert "presentation_mismatch" in hard_exclusions(dress, ctx, 50_000)
    assert hard_exclusions(shirt, ctx, 50_000) == []

    # unisex and feminine keep everything
    assert hard_exclusions(skirt, make_context(presentation="unisex"), 50_000) == []
    assert hard_exclusions(skirt, make_context(presentation="feminine"), 50_000) == []
