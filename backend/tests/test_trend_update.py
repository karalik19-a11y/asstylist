"""Regression tests for the current Fashion Engine v2 trend layer."""

from __future__ import annotations

from app.catalog.products import valid_products
from app.engine.options import LEGACY_STYLE_ALIASES, STYLE_OPTIONS, style_by_id
from app.fashion_engine.intelligence.trend_radar_v2 import CURRENT_SIGNALS, RADAR_VERSION, radar_for

CURRENT_STYLE_IDS = {option["id"] for option in STYLE_OPTIONS}


def test_current_taxonomy_replaces_stale_primary_styles():
    expected = {
        "modern_craftsman", "leather_weather", "broken_down_prep", "romantic_menswear",
        "military_romance", "archive_reconstruction", "technical_romantic", "americana_90s",
        "accessory_first", "pink_accent", "sport_couture", "neo_gothic_editorial",
        "post_punk_archive", "minimal_precision",
    }
    assert expected <= CURRENT_STYLE_IDS
    assert not {"old_money", "streetwear", "office_siren", "gorpcore", "y2k", "indie_sleaze"} & CURRENT_STYLE_IDS


def test_legacy_style_ids_resolve_without_being_primary_options():
    assert LEGACY_STYLE_ALIASES["office_siren"] == "minimal_precision"
    assert style_by_id("office_siren")["id"] == "minimal_precision"
    assert style_by_id("old_money")["id"] == "broken_down_prep"
    assert style_by_id("techwear")["id"] == "technical_romantic"


def test_radar_has_freshness_version_and_niche_signals():
    assert RADAR_VERSION == "2026-09-16"
    labels = {signal.label for signal in CURRENT_SIGNALS}
    assert {"Modern Craftsman", "Leather Weather", "Archive Reconstruction", "Romantic Menswear"} <= labels
    rows = radar_for("reworked M-65 leather field jacket archive workwear", niche_level=90)
    assert rows
    assert rows[0]["score"] > 0.7
    assert any(row["label"] == "Archive Reconstruction" for row in rows)


def test_radar_separates_generic_quiet_luxury_from_niche_signals():
    rows = radar_for("old money quiet luxury camel loafer", niche_level=90)
    assert rows
    quiet = next(row for row in rows if row["label"] == "Quiet Luxury")
    assert quiet["avoidAsGeneric"] is True
    assert quiet["score"] < 0.8


def test_catalog_items_keep_live_image_contract():
    for row in valid_products():
        assert row["image_url"] == "", row["sku"]
