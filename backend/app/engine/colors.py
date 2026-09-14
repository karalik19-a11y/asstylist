"""Colour registry + colour-harmony scoring.

Each colour carries fashion attributes (temperature, depth, chroma, neutrality)
so the ranking engine can reason about palettes without any ML dependency.
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass


@dataclass(frozen=True)
class ColorSpec:
    id: str
    ru: str
    hex: str
    temperature: str  # warm | cool | neutral
    depth: str  # light | medium | deep
    chroma: str  # soft | clear
    neutral: bool = False


COLORS: dict[str, ColorSpec] = {
    c.id: c
    for c in [
        ColorSpec("black", "чёрный", "#111114", "neutral", "deep", "clear", True),
        ColorSpec("charcoal", "графит", "#3A3D42", "cool", "deep", "soft", True),
        ColorSpec("grey", "серый", "#8A8D91", "neutral", "medium", "soft", True),
        ColorSpec("light_grey", "светло-серый", "#C7C9CC", "cool", "light", "soft", True),
        ColorSpec("white", "белый", "#F6F6F4", "neutral", "light", "clear", True),
        ColorSpec("ivory", "айвори", "#F1E7D3", "warm", "light", "soft", True),
        ColorSpec("beige", "бежевый", "#D9C3A5", "warm", "light", "soft", True),
        ColorSpec("sand", "песочный", "#CBB291", "warm", "medium", "soft", True),
        ColorSpec("camel", "кэмел", "#B08050", "warm", "medium", "soft", True),
        ColorSpec("brown", "коричневый", "#6E4B33", "warm", "deep", "soft", True),
        ColorSpec("chocolate", "шоколад", "#4A2F23", "warm", "deep", "soft", True),
        ColorSpec("terracotta", "терракота", "#C1663F", "warm", "medium", "clear", False),
        ColorSpec("burgundy", "бордовый", "#6B1F2A", "cool", "deep", "clear", False),
        ColorSpec("red", "красный", "#C1272D", "warm", "medium", "clear", False),
        ColorSpec("coral", "коралловый", "#F07A63", "warm", "light", "clear", False),
        ColorSpec("pink", "розовый", "#E58FA5", "cool", "light", "clear", False),
        ColorSpec("blush", "пудровый", "#EFC6C4", "warm", "light", "soft", False),
        ColorSpec("lavender", "лавандовый", "#B7A7D6", "cool", "light", "soft", False),
        ColorSpec("violet", "фиолетовый", "#5F3D75", "cool", "deep", "clear", False),
        ColorSpec("blue", "синий", "#2E4FA3", "cool", "medium", "clear", False),
        ColorSpec("navy", "тёмно-синий", "#1E2A44", "cool", "deep", "clear", True),
        ColorSpec("sky", "голубой", "#9BC4DE", "cool", "light", "soft", False),
        ColorSpec("teal", "тил", "#2C7A78", "cool", "medium", "clear", False),
        ColorSpec("emerald", "изумруд", "#1F6F4A", "cool", "deep", "clear", False),
        ColorSpec("olive", "оливковый", "#6B7043", "warm", "medium", "soft", False),
        ColorSpec("khaki", "хаки", "#8C8159", "warm", "medium", "soft", False),
        ColorSpec("green", "зелёный", "#2F7D32", "cool", "medium", "clear", False),
        ColorSpec("mustard", "горчичный", "#C79A2B", "warm", "medium", "clear", False),
        ColorSpec("yellow", "жёлтый", "#F2C230", "warm", "light", "clear", False),
        ColorSpec("orange", "оранжевый", "#E2762B", "warm", "medium", "clear", False),
        ColorSpec("silver", "серебро", "#C9CCD1", "cool", "light", "clear", True),
        ColorSpec("gold", "золото", "#C9A227", "warm", "medium", "clear", False),
    ]
}

NEUTRAL_IDS = tuple(cid for cid, spec in COLORS.items() if spec.neutral)


def hex_for(color_id: str) -> str:
    spec = COLORS.get(color_id)
    return spec.hex if spec else "#999999"


def hexes_for(color_ids: list[str]) -> list[str]:
    return [hex_for(cid) for cid in color_ids]


def spec_for(color_id: str) -> ColorSpec | None:
    return COLORS.get(color_id)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return "#{:02X}{:02X}{:02X}".format(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def nearest_color_id(rgb: tuple[int, int, int]) -> str:
    """Map an arbitrary RGB triple to the closest palette colour (CIE-ish, cheap)."""
    r, g, b = rgb
    best_id = "grey"
    best_dist = float("inf")
    for cid, spec in COLORS.items():
        raw = spec.hex.lstrip("#")
        cr, cg, cb = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
        # weight red a little more heavily — closer to human perception
        dist = (0.30 * (r - cr) ** 2) + (0.59 * (g - cg) ** 2) + (0.11 * (b - cb) ** 2)
        if dist < best_dist:
            best_dist = dist
            best_id = cid
    return best_id


def luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (v / 255 for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def warmth(rgb: tuple[int, int, int]) -> float:
    """-1 (cool) .. +1 (warm) based on hue position and channel bias."""
    r, g, b = (v / 255 for v in rgb)
    h, _l, s = colorsys.rgb_to_hls(r, g, b)
    hue = h * 360
    if s < 0.12:
        return 0.0
    # 0-60 and 300-360 are warm, 120-270 are cool
    if hue <= 60:
        base = 1.0 - (hue / 60) * 0.4
    elif hue <= 180:
        base = -0.4 - ((hue - 60) / 120) * 0.6
    elif hue <= 300:
        base = -1.0 + ((hue - 180) / 120) * 0.6
    else:
        base = -0.4 + ((hue - 300) / 60) * 1.4
    return max(-1.0, min(1.0, base * (0.4 + 0.6 * s)))


def harmony_score(item_colors: list[str], palette_colors: list[str], avoid_colors: list[str]) -> float:
    """0..1 — how well an item's colours sit inside the recommended palette."""
    if not item_colors:
        return 0.4
    scores: list[float] = []
    for cid in item_colors:
        if cid in avoid_colors:
            scores.append(0.0)
            continue
        if cid in palette_colors:
            scores.append(1.0)
            continue
        spec = COLORS.get(cid)
        if spec is None:
            scores.append(0.4)
            continue
        if spec.neutral:
            # neutrals go with everything, slightly less "styled" than a hit
            scores.append(0.82)
            continue
        # same temperature + depth is a soft match
        match = 0.0
        for pal_id in palette_colors:
            pal = COLORS.get(pal_id)
            if pal is None:
                continue
            if pal.temperature == spec.temperature:
                match = max(match, 0.55)
            if pal.depth == spec.depth:
                match = max(match, 0.5)
            if pal.chroma == spec.chroma and pal.temperature == spec.temperature:
                match = max(match, 0.72)
        scores.append(match if match else 0.35)
    return max(scores)


def palette_color_list(temperature: str, depth: str, chroma: str) -> list[str]:
    """Build a recommended wardrobe palette from analysed attributes."""
    chosen: list[str] = []
    # always allow the core neutrals
    for cid in ("black", "white", "grey", "navy", "beige"):
        chosen.append(cid)
    for cid, spec in COLORS.items():
        if spec.neutral:
            continue
        temp_ok = spec.temperature == temperature or spec.temperature == "neutral"
        depth_ok = spec.depth == depth or (depth == "medium" and spec.depth in ("light", "deep"))
        chroma_ok = spec.chroma == chroma
        if temp_ok and (depth_ok or chroma_ok):
            chosen.append(cid)
    # deterministic, deduplicated, capped
    seen: set[str] = set()
    ordered: list[str] = []
    for cid in chosen:
        if cid not in seen:
            seen.add(cid)
            ordered.append(cid)
    return ordered[:16]
