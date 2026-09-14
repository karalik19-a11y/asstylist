"""Tests for the offline photo analyser."""

from __future__ import annotations

import io

import pytest
from PIL import Image, ImageDraw

from app.vision.analyzer import VisionError, analyze_photo, empty_vision
from app.vision.ai import analyze


def make_image(mode: str = "warm", size: int = 160) -> bytes:
    image = Image.new("RGB", (size, size), (240, 235, 225) if mode == "warm" else (225, 232, 245))
    draw = ImageDraw.Draw(image)
    if mode == "warm":
        draw.rectangle([30, 30, 130, 130], fill=(190, 130, 70))
    elif mode == "cool":
        draw.rectangle([30, 30, 130, 130], fill=(40, 60, 140))
    elif mode == "person":
        draw.rectangle([0, 0, size, size], fill=(200, 205, 215))
        draw.ellipse([60, 25, 100, 70], fill=(226, 178, 148))  # head
        draw.polygon([(55, 75), (105, 75), (115, 140), (45, 140)], fill=(222, 170, 140))  # torso
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def test_warm_image_is_detected_as_warm():
    result = analyze_photo(make_image("warm"))
    assert result["ok"] is True
    assert result["temperature"] == "warm"
    assert result["dominant_colors"]
    assert 0 < result["palette_confidence"] <= 0.95
    assert len(result["sha256"]) == 64


def test_cool_image_is_detected_as_cool():
    result = analyze_photo(make_image("cool"))
    assert result["temperature"] == "cool"


def test_analysis_is_deterministic():
    data = make_image("person")
    assert analyze_photo(data) == analyze_photo(data)


def test_person_is_detected_with_skin_pixels():
    result = analyze_photo(make_image("person"))
    assert result["person_detected"] is True
    assert result["skin_ratio"] > 0.03


def test_invalid_bytes_raise_vision_error():
    with pytest.raises(VisionError):
        analyze_photo(b"not an image at all")
    with pytest.raises(VisionError):
        analyze_photo(b"")


def test_dimensions_and_format_are_reported():
    result = analyze_photo(make_image("warm", size=200))
    assert result["width"] == 200
    assert result["height"] == 200
    assert result["format"] == "jpeg"


def test_ai_analyze_falls_back_to_local_without_keys():
    result = analyze(make_image("warm"))
    assert result["ok"] is True
    assert result["source"] == "local"


def test_empty_vision_placeholder():
    placeholder = empty_vision("no photo")
    assert placeholder["ok"] is False
    assert placeholder["temperature"] == "neutral"
