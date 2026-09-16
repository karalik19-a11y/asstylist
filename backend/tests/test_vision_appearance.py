"""Разбор внешности по фото: подтон, контраст, цветотип + влияние на подбор."""

from __future__ import annotations

import io

from PIL import Image, ImageDraw

from app.engine.palette import analyze_palette
from app.services.look_service import _weights_for_vision, to_engine_request
from app.vision.analyzer import analyze_photo


def _portrait(skin=(224, 186, 158), hair=(60, 45, 35), cloth=(30, 30, 32)) -> bytes:
    img = Image.new("RGB", (200, 260), (90, 110, 140))
    d = ImageDraw.Draw(img)
    d.ellipse((70, 30, 130, 100), fill=skin)      # лицо
    d.rectangle((60, 100, 140, 170), fill=skin)   # шея
    d.ellipse((64, 18, 136, 60), fill=hair)       # волосы
    d.rectangle((60, 170, 140, 260), fill=cloth)  # одежда
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_warm_appearance_detected():
    result = analyze_photo(_portrait())
    assert result["person_detected"] is True
    assert result["appearance_used"] is True
    assert result["undertone"] == "warm"
    assert result["metal"] == "gold"
    assert result["skin_hex"]
    assert result["contrast"] in ("low", "medium", "high")
    # температура берётся из внешности, а не из фона
    assert result["temperature"] == "warm"


def test_cool_appearance_detected():
    result = analyze_photo(_portrait(skin=(228, 182, 172), hair=(30, 28, 30)))
    assert result["undertone"] == "cool"
    assert result["metal"] == "silver"
    assert result["hair_depth"] == "deep"


def test_no_person_keeps_defaults():
    img = Image.new("RGB", (200, 200), (90, 110, 140))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = analyze_photo(buf.getvalue())
    assert result["person_detected"] is False
    assert result["appearance_used"] is False
    assert "undertone" not in result or result.get("undertone") != "warm"


def test_palette_carries_color_type():
    palette = analyze_palette(analyze_photo(_portrait()))
    assert palette.source != "defaults"
    assert palette.color_type
    assert palette.contrast in ("low", "medium", "high")
    assert palette.metal in ("gold", "silver", "both")
    data = palette.to_dict()
    assert data["color_type_ru"] == palette.season_label
    assert "contrast_ru" in data and "metal_ru" in data and "undertone_ru" in data
    assert any("Подтон кожи" in signal for signal in data["signals"])


def test_palette_from_dict_roundtrip():
    palette = analyze_palette(analyze_photo(_portrait()))
    from app.engine.palette import palette_from_dict

    restored = palette_from_dict(palette.to_dict())
    assert restored.color_type == palette.color_type
    assert restored.contrast == palette.contrast
    assert restored.metal == palette.metal


def test_photo_boosts_color_and_silhouette_weights():
    plain = _weights_for_vision(None)
    vision = {"person_detected": True, "appearance_used": True}
    boosted = _weights_for_vision(vision)
    assert boosted["color"] > plain["color"]
    assert boosted["silhouette"] > plain["silhouette"]
    assert boosted["style"] < plain["style"]
    assert abs(sum(boosted.values()) - 1.0) < 1e-6
    no_person = _weights_for_vision({"person_detected": False})
    assert no_person == plain


def test_to_engine_request_uses_boosted_weights():
    request = to_engine_request({"budget_rub": 30_000}, {"person_detected": True, "appearance_used": False})
    neutral = to_engine_request({"budget_rub": 30_000}, None)
    assert request.weights["color"] > neutral.weights["color"]
