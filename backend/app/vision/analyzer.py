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
        # Диапазоны охватывают и очень светлую прохладную кожу (высокие g и b),
        # и глубокие оттенки; отсекают фон/одежду через порядок каналов r>g≥b
        # и разумную границу насыщенности.
        is_skin = (
            0.25 < rn <= 1.0
            and 0.15 < gn < 0.92
            and 0.08 < bn < 0.88
            and r > g
            and g >= b - 6
            and (r - b) > 10
            and (max(r, g, b) - min(r, g, b)) > 12
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


def _skin_rows(mask: list[bool], size: int) -> dict[int, list[int]]:
    rows: dict[int, list[int]] = {}
    for index, is_skin in enumerate(mask):
        if is_skin:
            rows.setdefault(index // size, []).append(index % size)
    return rows


def _mean_rgb(points: list[tuple[int, int, int]]) -> tuple[int, int, int] | None:
    if not points:
        return None
    n = len(points)
    return (
        round(sum(p[0] for p in points) / n),
        round(sum(p[1] for p in points) / n),
        round(sum(p[2] for p in points) / n),
    )


def _luma(rgb: tuple[int, int, int]) -> float:
    return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255


def _person_features(
    pixels: list[tuple[int, int, int]],
    mask: list[bool],
    size: int,
) -> dict[str, Any]:
    """Внешность по фото: подтон кожи, глубина волос, контраст, металл.

    Локальные эвристики без модели: лицо — верхний кластер открытой кожи,
    волосы — полоса прямо над ним. Каждая метрика снабжена уверенностью;
    если человек не найден, возвращаются нейтральные значения и низкий
    confidence — дальше пайплайн работает на параметрах пользователя.
    """
    rows = _skin_rows(mask, size)
    if len(rows) < 6:
        return {}
    top_row, bottom_row = min(rows), max(rows)
    span = bottom_row - top_row
    if span < 6:
        return {}

    # Зона лица: верхняя часть кожного кластера (лицо/шея), а не всё фото —
    # иначе в «кожу» попадали фон и одежда тёплых оттенков.
    face_limit = top_row + max(3, int(span * 0.45))
    face_pixels = [
        pixels[y * size + x]
        for y, xs in rows.items()
        if top_row <= y <= face_limit
        for x in xs
    ]
    skin = _mean_rgb(face_pixels)
    if skin is None:
        return {}

    # Полоса волос: прямо над кожным кластером, по его же горизонтали.
    face_xs = [x for y, xs in rows.items() if top_row <= y <= face_limit for x in xs]
    cx = sum(face_xs) / max(1, len(face_xs))
    half_w = max(4.0, (max(face_xs) - min(face_xs)) / 2 * 1.2) if face_xs else size / 4
    hair_band: list[tuple[int, int, int]] = []
    for y in range(max(0, top_row - int(span * 0.35) - 4), top_row):
        for x in range(max(0, int(cx - half_w)), min(size, int(cx + half_w))):
            if not mask[y * size + x]:
                hair_band.append(pixels[y * size + x])

    hair = None
    if len(hair_band) >= 12:
        hair_band_sorted = sorted(hair_band, key=_luma)
        hair = _mean_rgb(hair_band_sorted[: max(1, len(hair_band_sorted) // 2)])

    skin_luma = _luma(skin)
    r, g, b = skin[0] / 255, skin[1] / 255, skin[2] / 255
    # Подтон: «золотистая» кожа (g заметно выше b при тёплом r) — тёплая;
    # «розовая» (близкие g/b при красноватом r) — холодная.
    warm_span = r - b
    golden = g - b
    if warm_span > 0.13 and golden > 0.06:
        undertone = "warm"
    elif golden < 0.045 or warm_span < 0.10:
        undertone = "cool"
    else:
        undertone = "neutral"
    undertone_score = round((warm_span + 0.6 * max(0.0, golden)) / 1.6, 3)

    hair_luma = _luma(hair) if hair else None
    hair_depth = None
    if hair_luma is not None:
        hair_depth = "light" if hair_luma > 0.52 else "deep" if hair_luma < 0.22 else "medium"

    if hair_luma is not None:
        delta = skin_luma - hair_luma
    else:
        # нет надёжной полосы волос → контраст по разбросу кожных оттенков
        lumas = sorted(_luma(p) for p in face_pixels)
        if len(lumas) >= 8:
            delta = lumas[int(len(lumas) * 0.85)] - lumas[int(len(lumas) * 0.15)]
        else:
            delta = 0.25
    contrast = "high" if delta > 0.42 else "low" if delta < 0.22 else "medium"

    # Глубина цветотипа: прежде всего тон кожи; тёмные волосы усиливают
    # глубину только при нешумной (не самой светлой) коже.
    if skin_luma < 0.4:
        depth = "deep"
    elif skin_luma > 0.68:
        depth = "light" if hair_depth in (None, "light", "medium") else "medium"
    elif hair_depth == "deep" and contrast == "high":
        depth = "deep"
    elif skin_luma < 0.5:
        depth = "medium"
    else:
        depth = "medium"
    chroma = "clear" if contrast == "high" else "soft"

    metal = "gold" if undertone == "warm" else "silver" if undertone == "cool" else "both"

    return {
        "skin_hex": rgb_to_hex(*skin),
        "skin_luma": round(skin_luma, 3),
        "undertone": undertone,
        "undertone_score": undertone_score,
        "hair_hex": rgb_to_hex(*hair) if hair else None,
        "hair_depth": hair_depth,
        "contrast": contrast,
        "contrast_delta": round(float(delta), 3),
        "metal": metal,
        # Поля совместимости со старым пайплайном палитры — теперь они
        # выводятся из внешности, а не из доминирующих цветов всего кадра.
        "appearance_temperature": undertone,
        "appearance_depth": depth,
        "appearance_chroma": chroma,
    }


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

    # Температура/глубина/насыщенность по всему кадру — запасной вариант.
    temperature = _temperature_label(weighted_warmth)
    depth = _depth_label(weighted_luma)
    chroma = _chroma_label(mean_sat)

    person: dict[str, Any] = _person_features(pixels, mask, size) if person_detected else {}
    appearance_used = False
    if person:
        # Главное изменение: цветотип определяем по коже и волосам человека,
        # а не по фону и одежде в кадре.
        temperature = person.get("appearance_temperature", temperature)
        depth = person.get("appearance_depth", depth)
        chroma = person.get("appearance_chroma", chroma)
        confidence = min(0.94, confidence + 0.08)
        appearance_used = True

    return {
        "source": provider_label,
        "ok": True,
        "person_detected": person_detected,
        "appearance_used": appearance_used,
        "skin_ratio": round(skin_ratio, 4),
        "shoulder_hip_ratio": ratio,
        "dominant_colors": color_ids,
        "dominant_hexes": [rgb_to_hex(*rgb) for rgb, _ in kept],
        "temperature": temperature,
        "depth": depth,
        "chroma": chroma,
        "palette_confidence": round(min(0.94, confidence), 2),
        "brightness": round(mean_luma, 3),
        "saturation": round(mean_sat, 3),
        "warmth": round(weighted_warmth, 3),
        "sha256": digest,
        "width": image.size[0],
        "height": image.size[1],
        "format": (image.format or "unknown").lower(),
        **person,
    }


def empty_vision(reason: str) -> dict[str, Any]:
    return {
        "source": "none",
        "ok": False,
        "reason": reason,
        "person_detected": False,
        "appearance_used": False,
        "dominant_colors": [],
        "dominant_hexes": [],
        "temperature": "neutral",
        "depth": "medium",
        "chroma": "soft",
        "undertone": "neutral",
        "contrast": "medium",
        "metal": "both",
        "hair_depth": None,
        "palette_confidence": 0.2,
    }
