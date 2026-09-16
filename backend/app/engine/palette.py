"""Colour/palette profiling: turns a photo analysis (or defaults) into a
recommended wardrobe palette."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .colors import palette_color_list

SEASON_LABELS = {
    ("warm", "light"): "Тёплая весна",
    ("warm", "deep"): "Тёплая осень",
    ("cool", "light"): "Холодное лето",
    ("cool", "deep"): "Холодная зима",
    ("neutral", "light"): "Мягкое лето",
    ("neutral", "medium"): "Мягкий переходный тип",
    ("neutral", "deep"): "Глубокая нейтральная зима",
}

CONTRAST_RU = {
    "low": "низкий",
    "medium": "средний",
    "high": "высокий",
}

METAL_RU = {
    "gold": "золото",
    "silver": "серебро",
    "both": "золото и серебро",
}

UNDERTONE_RU = {
    "warm": "тёплый",
    "cool": "холодный",
    "neutral": "нейтральный",
}

#: Советы по сочетаниям для уровня контраста внешности.
CONTRAST_TIPS = {
    "low": "Внешность неконтрастная: собирайте образ тон в тон и избегайте резких чёрно-белых переходов у лица.",
    "medium": "Контраст средний: держите 1–2 акцента и мягкие переходы оттенков.",
    "high": "Внешность контрастная: вам идут чистые цвета и чёткие контрастные сочетания.",
}


@dataclass(frozen=True)
class PaletteProfile:
    temperature: str
    depth: str
    chroma: str
    season_label: str
    recommended: tuple[str, ...]
    avoid: tuple[str, ...]
    confidence: float
    source: str
    dominant_colors: tuple[str, ...] = field(default_factory=tuple)
    signals: list[str] = field(default_factory=list)
    #: Расширенный разбор внешности (по фото): цветотип, подтон, контраст,
    #: «свой» металл. Без фото — нейтральные значения и низкая уверенность.
    color_type: str = "neutral_medium"
    undertone: str = "neutral"
    contrast: str = "medium"
    metal: str = "both"
    hair_depth: str | None = None
    skin_hex: str | None = None
    hair_hex: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["recommended"] = list(self.recommended)
        data["avoid"] = list(self.avoid)
        data["dominant_colors"] = list(self.dominant_colors)
        data["signals"] = list(self.signals)
        data["color_type_ru"] = self.season_label
        data["undertone_ru"] = UNDERTONE_RU.get(self.undertone, self.undertone)
        data["contrast_ru"] = CONTRAST_RU.get(self.contrast, self.contrast)
        data["metal_ru"] = METAL_RU.get(self.metal, self.metal)
        return data


def _avoid_colors(temperature: str, depth: str, chroma: str) -> list[str]:
    """Colours that fight the analysed type."""
    avoid: list[str] = []
    if temperature == "cool":
        avoid += ["mustard", "orange", "terracotta", "camel"]
    if temperature == "warm":
        avoid += ["silver", "lavender", "sky", "violet"]
    if depth == "light":
        avoid += ["black", "chocolate"]
    if depth == "deep" and chroma == "clear":
        avoid += ["ivory", "blush", "light_grey"]
    return list(dict.fromkeys(avoid))


def analyze_palette(
    vision: dict[str, Any] | None = None,
    preferred_colors: list[str] | None = None,
    style_hint_colors: list[str] | None = None,
) -> PaletteProfile:
    preferred_colors = preferred_colors or []
    style_hint_colors = style_hint_colors or []
    signals: list[str] = []

    if vision and vision.get("dominant_colors"):
        temperature = vision.get("temperature", "neutral")
        depth = vision.get("depth", "medium")
        chroma = vision.get("chroma", "soft")
        confidence = float(vision.get("palette_confidence", 0.6))
        source = vision.get("source", "photo")
        dominant = tuple(vision.get("dominant_colors", []))
        appearance_used = bool(vision.get("appearance_used"))
        if appearance_used:
            signals.append("Фото: анализ внешности — подтон кожи, глубина волос, контраст")
            undertone = str(vision.get("undertone") or temperature)
            hair = {"light": "светлые", "medium": "русые/средние", "deep": "тёмные"}.get(
                str(vision.get("hair_depth") or ""), None
            )
            signals.append(
                f"Подтон кожи — {UNDERTONE_RU.get(undertone, undertone)}"
                + (f", волосы — {hair}" if hair else "")
                + f", контраст — {CONTRAST_RU.get(str(vision.get('contrast') or 'medium'), 'средний')}"
            )
        else:
            signals.append(f"Фото: доминирующие оттенки — {', '.join(dominant[:4])}")
            signals.append(f"Определён подтон: {temperature}, глубина: {depth}, насыщенность: {chroma}")
    else:
        temperature, depth, chroma = "neutral", "medium", "soft"
        confidence = 0.25
        source = "defaults"
        dominant = ()
        signals.append("Фото нет или не распознано — использована нейтральная база")

    recommended = palette_color_list(temperature, depth, chroma)

    # user preference always wins: it goes first and is never in "avoid"
    for cid in preferred_colors:
        if cid not in recommended:
            recommended.insert(0, cid)
    if preferred_colors:
        signals.append("Учтены любимые цвета пользователя")

    avoid = [cid for cid in _avoid_colors(temperature, depth, chroma) if cid not in preferred_colors]

    # style hint colours are added (they define the requested aesthetic)
    for cid in style_hint_colors:
        if cid not in recommended:
            recommended.append(cid)
    if style_hint_colors:
        signals.append("Добавлены фирменные оттенки выбранного стиля")

    label = SEASON_LABELS.get((temperature, depth), SEASON_LABELS.get((temperature, "medium"), "Универсальная палитра"))

    contrast = str((vision or {}).get("contrast") or ("high" if chroma == "clear" else "medium"))
    metal = str((vision or {}).get("metal") or ("gold" if temperature == "warm" else "silver" if temperature == "cool" else "both"))
    if vision and vision.get("appearance_used") and CONTRAST_TIPS.get(contrast):
        signals.append(CONTRAST_TIPS[contrast])
        signals.append(f"Украшения и фурнитура: ваш металл — {METAL_RU.get(metal, metal)}")

    return PaletteProfile(
        temperature=temperature,
        depth=depth,
        chroma=chroma,
        season_label=label,
        recommended=tuple(dict.fromkeys(recommended))[:16],
        avoid=tuple(avoid)[:8],
        confidence=round(confidence, 2),
        source=source,
        dominant_colors=dominant[:6],
        signals=signals,
        color_type=f"{temperature}_{depth}",
        undertone=str((vision or {}).get("undertone") or temperature),
        contrast=contrast,
        metal=metal,
        hair_depth=(vision or {}).get("hair_depth"),
        skin_hex=(vision or {}).get("skin_hex"),
        hair_hex=(vision or {}).get("hair_hex"),
    )


def palette_from_dict(data: dict[str, Any]) -> PaletteProfile:
    """Rebuild a palette profile from its serialised form."""
    return PaletteProfile(
        temperature=str(data.get("temperature", "neutral")),
        depth=str(data.get("depth", "medium")),
        chroma=str(data.get("chroma", "soft")),
        season_label=str(data.get("season_label", "")),
        recommended=tuple(data.get("recommended", ())),
        avoid=tuple(data.get("avoid", ())),
        confidence=float(data.get("confidence", 0.3)),
        source=str(data.get("source", "defaults")),
        dominant_colors=tuple(data.get("dominant_colors", ())),
        signals=list(data.get("signals", [])),
        color_type=str(data.get("color_type", "neutral_medium")),
        undertone=str(data.get("undertone", "neutral")),
        contrast=str(data.get("contrast", "medium")),
        metal=str(data.get("metal", "both")),
        hair_depth=data.get("hair_depth"),
        skin_hex=data.get("skin_hex"),
        hair_hex=data.get("hair_hex"),
    )
