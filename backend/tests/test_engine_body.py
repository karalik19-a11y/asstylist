"""Tests for body profiling."""

from __future__ import annotations

from app.engine.body import analyze_body, silhouette_fit_score


def test_bmi_and_silhouette_mapping():
    lean = analyze_body(175, 55)
    balanced = analyze_body(175, 70)
    curved = analyze_body(175, 85)
    rounded = analyze_body(175, 100)

    assert lean.bmi == 18.0
    assert lean.silhouette == "lean"
    assert balanced.silhouette == "balanced"
    assert curved.silhouette == "curved"
    assert rounded.silhouette == "rounded"


def test_height_classes():
    assert analyze_body(155, 55).height_class == "petite"
    assert analyze_body(170, 65).height_class == "average"
    assert analyze_body(190, 80).height_class == "tall"


def test_avoid_fits_block_slim_for_rounded():
    profile = analyze_body(175, 100)
    assert "slim" in profile.avoid_fits
    assert silhouette_fit_score("slim", ["all"], profile) < 0.3
    assert silhouette_fit_score("relaxed", ["all"], profile) > 0.9


def test_vision_hints_raise_confidence_and_change_shape():
    base = analyze_body(175, 70)
    athletic = analyze_body(175, 70, vision={"person_detected": True, "shoulder_hip_ratio": 1.3})
    assert athletic.silhouette == "athletic"
    assert athletic.confidence > base.confidence


def test_unrecognised_photo_lowers_confidence():
    base = analyze_body(175, 70)
    noisy = analyze_body(175, 70, vision={"person_detected": False, "shoulder_hip_ratio": None})
    assert noisy.confidence < base.confidence


def test_profile_is_serialisable_and_rebuildable():
    from app.engine.body import body_from_dict

    profile = analyze_body(175, 70)
    rebuilt = body_from_dict(profile.to_dict())
    assert rebuilt.silhouette == profile.silhouette
    assert rebuilt.recommended_fits == profile.recommended_fits
