"""Tests for palette analysis and colour harmony."""

from __future__ import annotations

from app.engine.colors import harmony_score, nearest_color_id, palette_color_list, warmth
from app.engine.palette import analyze_palette, palette_from_dict


def test_default_palette_without_photo():
    palette = analyze_palette()
    assert palette.source == "defaults"
    assert palette.confidence <= 0.3
    assert "black" in palette.recommended
    assert palette.dominant_colors == ()


def test_photo_drives_temperature_and_depth():
    vision = {
        "dominant_colors": ["camel", "sand"],
        "temperature": "warm",
        "depth": "light",
        "chroma": "soft",
        "palette_confidence": 0.7,
        "source": "local",
    }
    palette = analyze_palette(vision)
    assert palette.temperature == "warm"
    assert palette.depth == "light"
    assert palette.confidence >= 0.7
    # cool-only colours must be avoided for a warm type
    assert "silver" in palette.avoid


def test_preferred_colors_win_over_avoid():
    vision = {"dominant_colors": ["camel"], "temperature": "warm", "depth": "light", "chroma": "soft"}
    palette = analyze_palette(vision, preferred_colors=["silver"])
    assert palette.recommended[0] == "silver"
    assert "silver" not in palette.avoid


def test_palette_round_trip():
    palette = analyze_palette()
    rebuilt = palette_from_dict(palette.to_dict())
    assert rebuilt.recommended == palette.recommended
    assert rebuilt.avoid == palette.avoid


def test_harmony_prefers_palette_hits_and_neutrals():
    palette = palette_color_list("cool", "deep", "clear")
    assert harmony_score(["navy"], palette, []) == 1.0
    assert harmony_score(["black"], palette, []) > 0.7
    assert harmony_score(["mustard"], palette, []) < harmony_score(["navy"], palette, [])
    assert harmony_score(["mustard"], palette, ["mustard"]) == 0.0


def test_nearest_color_id_round_trip():
    assert nearest_color_id((17, 17, 20)) == "black"
    assert nearest_color_id((246, 246, 244)) == "white"


def test_warmth_direction():
    assert warmth((200, 120, 60)) > 0
    assert warmth((60, 120, 200)) < 0
