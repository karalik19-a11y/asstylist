"""Offline photo analysis.

Uses Pillow only: no model download, no API key, works in demo/local mode.
The output feeds the palette and body engines, and always carries a confidence
value plus the signals it was derived from, so nothing is presented as magic.
"""

from __future__ import annotations

import hashlib
import io
from typing import Any

from PIL import Image, ImageFile, UnidentifiedImageError

from ..engine.colors import nearest_color_id, rgb_to_hex

Image.MAX_IMAGE_PIXELS = 40_000_000
ImageFile.LOAD_TRUNCATED_IMAGES = False

ANALYSIS_SIZE = 96
MAX_DOMINANT_COLORS = 6


class VisionError(RuntimeError):
    pass


def _skin_mask_pixels(pixels: list[tuple[int, int, int]], size: int) -> list[bool]:
    mask: list[bool] = []
    for r, g, b in pixels:
        rn, gn, bn = r / 255, g / 255, b / 255
        is_skin = (
            0.32 < rn < 0.98
            and 0.22 < gn < 0.80
            and 0.12 < bn < 0.62
            and r > g > b
            and (max(r, g, b) - min(r, g, b)) > 15
        )
        mask.append(is_skin)
    return mask


def _dominant_colors(image: Image.Image) -> list[tuple[tuple[int, int, int], float]]:
    small = image.convert("RGB").resize((ANALYSIS_SIZE, ANALYSIS_SIZE), Image.LANCZOS)
    quantized = small.quantize(colors=8, method=Image.MEDIANCUT)
    palette = quantized.getpalette() or []
    counts = quantized.getcolors() or []
    total = sum(count for count, _ in counts) or 1
    result: list[tuple[tuple[int, int, int], float]] = []
    for count, index in sorted(counts, key=lambda pair: -pair[0]):
        rgb = (palette[index * 3], palette[index * 3 + 1], palette[index * 3 + 2])
        result.append((rgb, count / total))
    return result


def _temperature_label(warmth_value: float) -> str:
    if warmth_value > 0.08:
        return "warm"
    if warmth_value < -0.08:
        return "cool"
    return "neutral"


def _depth_label(luma: float) -> str:
    if luma > 0.62:
        return "light"
    if luma < 0.34:
        return "deep"
    return "medium"


def _chroma_label(saturation: float) -> str:
    return "clear" if saturation > 0.38 else "soft"


def _shoulder_hip_ratio(image: Image.Image, mask: list[bool], size: int) -> float | None:
    """Crude but deterministic: widest skin row in the upper band vs the lower band."""
    width = size
    rows: dict[int, list[int]] = {}
    for index, is_skin in enumerate(mask):
        if not is_skin:
            continue
        y = index // width
        rows.setdefault(y, []).append(index % width)
    if len(rows) < 6:
        return None
    top = min(rows)
    bottom = max(rows)
    span = max(1, bottom - top)
    upper_limit = top + int(span * 0.4)
    lower_start = top + int(span * 0.55)

    def widest(lo: int, hi: int) -> int:
        best = 0
        for y, xs in rows.items():
            if lo <= y <= hi:
                best = max(best, max(xs) - min(xs) + 1)
        return best

    shoulders = widest(top, upper_limit)
    hips = widest(lower_start, bottom)
    if shoulders < 4 or hips < 4:
        return None
    return round(shoulders / hips, 3)


def analyze_photo(data: bytes, provider_label: str = "local") -> dict[str, Any]:
    """Analyse raw image bytes. Raises VisionError for unreadable input."""
    if not data:
        raise VisionError("Пустой файл изображения")

    digest = hashlib.sha256(data).hexdigest()
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise VisionError("Не удалось прочитать изображение") from exc

    rgb = image.convert("RGB")
    if max(rgb.size) > ANALYSIS_SIZE:
        rgb_small = rgb.resize((ANALYSIS_SIZE, ANALYSIS_SIZE), Image.LANCZOS)
    else:
        rgb_small = rgb

    pixels = list(rgb_small.getdata())
    size = rgb_small.size[0]

    from ..engine.colors import luminance, warmth

    luma_values = [luminance(p) for p in pixels]
    warmth_values = [warmth(p) for p in pixels]
    saturations = []
    for r, g, b in pixels:
        mx, mn = max(r, g, b), min(r, g, b)
        saturations.append(0.0 if mx == 0 else (mx - mn) / mx)

    mean_luma = sum(luma_values) / len(luma_values)
    mean_warmth = sum(warmth_values) / len(warmth_values)
    mean_sat = sum(saturations) / len(saturations)

    dominant = _dominant_colors(rgb_small)
    kept = [(rgb, share) for rgb, share in dominant if share >= 0.04][:MAX_DOMINANT_COLORS]
    if not kept and dominant:
        kept = dominant[:3]

    color_ids: list[str] = []
    for rgb, _share in kept:
        cid = nearest_color_id(rgb)
        if cid not in color_ids:
            color_ids.append(cid)

    weighted_warmth = sum(warmth(rgb) * share for rgb, share in kept) / (sum(s for _, s in kept) or 1)
    weighted_luma = sum(luminance(rgb) * share for rgb, share in kept) / (sum(s for _, s in kept) or 1)

    mask = _skin_mask_pixels(pixels, size)
    skin_ratio = sum(1 for v in mask if v) / max(1, len(mask))
    person_detected = skin_ratio >= 0.03
    ratio = _shoulder_hip_ratio(rgb_small, mask, size) if person_detected else None

    confidence = 0.45 + (0.25 if person_detected else 0.0) + min(0.2, len(color_ids) * 0.04)
    if skin_ratio > 0.25:
        confidence += 0.05

    return {
        "source": provider_label,
        "ok": True,
        "person_detected": person_detected,
        "skin_ratio": round(skin_ratio, 4),
        "shoulder_hip_ratio": ratio,
        "dominant_colors": color_ids,
        "dominant_hexes": [rgb_to_hex(*rgb) for rgb, _ in kept],
        "temperature": _temperature_label(weighted_warmth),
        "depth": _depth_label(weighted_luma),
        "chroma": _chroma_label(mean_sat),
        "palette_confidence": round(min(0.92, confidence), 2),
        "brightness": round(mean_luma, 3),
        "saturation": round(mean_sat, 3),
        "warmth": round(weighted_warmth, 3),
        "sha256": digest,
        "width": image.size[0],
        "height": image.size[1],
        "format": (image.format or "unknown").lower(),
    }


def empty_vision(reason: str) -> dict[str, Any]:
    return {
        "source": "none",
        "ok": False,
        "reason": reason,
        "person_detected": False,
        "dominant_colors": [],
        "dominant_hexes": [],
        "temperature": "neutral",
        "depth": "medium",
        "chroma": "soft",
        "palette_confidence": 0.2,
    }
