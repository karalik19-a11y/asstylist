"""Body profiling from height/weight (+ optional vision hints).

We are deliberately honest here: height and weight alone cannot determine a body
shape. The engine therefore produces a *silhouette guideline* with an explicit
confidence value, and upgrades it only when a photo adds real signal.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

FIT_ORDER = ("slim", "regular", "relaxed", "oversize")

SILHOUETTE_RULES: dict[str, dict[str, Any]] = {
    "lean": {
        "ru": "Стройный / прямой силуэт",
        "recommended_fits": ("slim", "regular", "oversize"),
        "avoid_fits": (),
        "recommended_lengths": ("cropped", "regular", "long"),
        "tips": (
            "Многослойность добавляет объём там, где его не хватает.",
            "Горизонтальные линии и плотные ткани держат форму силуэта.",
            "Оверсайз-верх работает в паре с зауженным низом.",
        ),
    },
    "balanced": {
        "ru": "Сбалансированный силуэт",
        "recommended_fits": ("regular", "slim", "relaxed"),
        "avoid_fits": (),
        "recommended_lengths": ("regular", "midi", "long"),
        "tips": (
            "Практически любой крой садится хорошо — можно играть с пропорциями.",
            "Один акцент на образ: либо объёмный верх, либо широкие брюки.",
            "Держите одну вертикаль цвета, чтобы образ выглядел собранно.",
        ),
    },
    "curved": {
        "ru": "Мягкий силуэт",
        "recommended_fits": ("regular", "relaxed"),
        "avoid_fits": ("slim",),
        "recommended_lengths": ("midi", "long", "regular"),
        "tips": (
            "Вертикальные линии и однобортные силуэты вытягивают рост.",
            "Плотная ткань без лишнего объёма в талии держит форму.",
            "Избегайте резких горизонтальных швов на самой широкой линии.",
        ),
    },
    "rounded": {
        "ru": "Округлый силуэт",
        "recommended_fits": ("relaxed", "regular"),
        "avoid_fits": ("slim", "oversize"),
        "recommended_lengths": ("long", "midi"),
        "tips": (
            "Длинные вертикали: расстёгнутый жакет, пальто, прямые брюки.",
            "Матовые плотные ткани держат форму лучше тонкого трикотажа.",
            "Тёмный монохром с одним светлым акцентом у лица работает лучше всего.",
        ),
    },
    "athletic": {
        "ru": "Атлетичный силуэт",
        "recommended_fits": ("regular", "slim", "relaxed"),
        "avoid_fits": (),
        "recommended_lengths": ("regular", "cropped", "long"),
        "tips": (
            "Смягчите линию плеч: реглан, спущенный рукав, мягкие ткани.",
            "Прямые и широкие брюки балансируют широкий верх.",
        ),
    },
}


@dataclass(frozen=True)
class BodyProfile:
    height_cm: float
    weight_kg: float
    bmi: float
    bmi_label: str
    height_class: str
    silhouette: str
    silhouette_ru: str
    confidence: float
    recommended_fits: tuple[str, ...]
    avoid_fits: tuple[str, ...]
    recommended_lengths: tuple[str, ...]
    tips: tuple[str, ...]
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["recommended_fits"] = list(self.recommended_fits)
        data["avoid_fits"] = list(self.avoid_fits)
        data["recommended_lengths"] = list(self.recommended_lengths)
        data["tips"] = list(self.tips)
        return data


def _height_class(height_cm: float) -> str:
    if height_cm < 160:
        return "petite"
    if height_cm <= 178:
        return "average"
    return "tall"


def _bmi_label(bmi: float) -> str:
    if bmi < 18.5:
        return "ниже нормы"
    if bmi < 25:
        return "норма"
    if bmi < 30:
        return "выше нормы"
    return "высокий"


def _silhouette_from_bmi(bmi: float) -> str:
    if bmi < 19.5:
        return "lean"
    if bmi < 25:
        return "balanced"
    if bmi < 30:
        return "curved"
    return "rounded"


def analyze_body(
    height_cm: float,
    weight_kg: float,
    presentation: str = "unisex",
    vision: dict[str, Any] | None = None,
) -> BodyProfile:
    """Build a silhouette profile. `vision` may add shoulder/hip hints from a photo."""
    height_cm = float(height_cm)
    weight_kg = float(weight_kg)
    meters = height_cm / 100.0
    bmi = round(weight_kg / (meters * meters), 1) if meters > 0 else 0.0

    silhouette = _silhouette_from_bmi(bmi)
    signals = ["Рост и вес → оценка ИМТ и базового силуэта"]
    confidence = 0.45

    if vision:
        ratio = vision.get("shoulder_hip_ratio")
        if isinstance(ratio, (int, float)) and ratio > 0:
            ratio = float(ratio)
            if ratio >= 1.15:
                silhouette = "athletic"
                confidence = max(confidence, 0.72)
                signals.append("Фото: плечи заметно шире бёдер → атлетичный силуэт")
            elif ratio <= 0.88:
                silhouette = "curved"
                confidence = max(confidence, 0.7)
                signals.append("Фото: бёдра шире плеч → мягкий силуэт")
            else:
                confidence = max(confidence, 0.62)
                signals.append("Фото: пропорции плечи/бёдра близки к балансу")
        if vision.get("person_detected"):
            confidence = min(0.9, confidence + 0.1)
            signals.append("Фото: кадр распознан как портрет")
        else:
            confidence = max(0.25, confidence - 0.1)
            signals.append("Фото: силуэт не распознан — оценка только по росту и весу")

    if _height_class(height_cm) == "petite":
        confidence = min(confidence, 0.8)
        signals.append("Невысокий рост → приоритет вертикалям и укороченным длинам")
    if _height_class(height_cm) == "tall":
        signals.append("Высокий рост → длинные силуэты и крупные аксессуары")

    rules = SILHOUETTE_RULES[silhouette]
    return BodyProfile(
        height_cm=height_cm,
        weight_kg=weight_kg,
        bmi=bmi,
        bmi_label=_bmi_label(bmi),
        height_class=_height_class(height_cm),
        silhouette=silhouette,
        silhouette_ru=rules["ru"],
        confidence=round(confidence, 2),
        recommended_fits=tuple(rules["recommended_fits"]),
        avoid_fits=tuple(rules["avoid_fits"]),
        recommended_lengths=tuple(rules["recommended_lengths"]),
        tips=tuple(rules["tips"]),
        signals=signals,
    )


def silhouette_fit_score(fit: str, silhouettes: list[str], profile: BodyProfile) -> float:
    """0..1 — how flattering this item is for the analysed silhouette."""
    fit = (fit or "regular").lower()
    if fit in profile.avoid_fits:
        base = 0.15
    elif fit in profile.recommended_fits:
        base = 1.0
    else:
        base = 0.6

    if silhouettes and profile.silhouette not in silhouettes and "all" not in silhouettes:
        base = min(base, 0.55)

    # petite frames lose points on very long/heavy pieces, tall frames gain
    if profile.height_class == "petite" and fit == "oversize":
        base = min(base, 0.7)
    return round(base, 3)


def body_from_dict(data: dict[str, Any]) -> BodyProfile:
    """Rebuild a profile from its serialised form (used when swapping items)."""
    return BodyProfile(
        height_cm=float(data.get("height_cm", 172)),
        weight_kg=float(data.get("weight_kg", 68)),
        bmi=float(data.get("bmi", 0.0)),
        bmi_label=str(data.get("bmi_label", "")),
        height_class=str(data.get("height_class", "average")),
        silhouette=str(data.get("silhouette", "balanced")),
        silhouette_ru=str(data.get("silhouette_ru", "")),
        confidence=float(data.get("confidence", 0.4)),
        recommended_fits=tuple(data.get("recommended_fits", ())),
        avoid_fits=tuple(data.get("avoid_fits", ())),
        recommended_lengths=tuple(data.get("recommended_lengths", ())),
        tips=tuple(data.get("tips", ())),
        signals=list(data.get("signals", [])),
    )
