"""Fashion taxonomy v2: current, niche-first styles and stable compatibility aliases."""

from __future__ import annotations
from typing import Any

STYLE_OPTIONS: list[dict[str, Any]] = [
    {"id": "modern_craftsman", "label": "Современный workwear", "emoji": "🧵", "description": "Workwear, field jacket, выцветший деним, фактуры и один сильный аксессуар.", "palette_hint": ["brown", "olive", "navy", "cream", "mustard"]},
    {"id": "leather_weather", "label": "Кожаный гардероб", "emoji": "🧥", "description": "Состаренная кожа, мото-архетипы и мягкий контраст с трикотажем или строгим кроем.", "palette_hint": ["black", "brown", "burgundy", "cream", "olive"]},
    {"id": "broken_down_prep", "label": "Casual prep", "emoji": "🏄", "description": "Ivy/prep, намеренно расслабленный крой и surf-детали вместо стерильной классики.", "palette_hint": ["navy", "cream", "red", "brown", "washed_blue"]},
    {"id": "romantic_menswear", "label": "Мягкий тейлоринг", "emoji": "🌹", "description": "Драпировка, полупрозрачные слои, мягкий tailoring и намеренно чувственная пропорция.", "palette_hint": ["black", "ivory", "burgundy", "dusty_pink", "brown"]},
    {"id": "military_romance", "label": "Милитари-эстетика", "emoji": "🎖️", "description": "Военная конструкция + викторианская/флоральная деталь; строгая база и один декоративный сбой.", "palette_hint": ["olive", "black", "burgundy", "cream", "khaki"]},
    {"id": "archive_reconstruction", "label": "Архивная мода", "emoji": "🧩", "description": "Архивные вещи, deadstock и reworked-конструкция вместо буквального копирования с подиума.", "palette_hint": ["black", "grey", "denim", "brown", "white"]},
    {"id": "technical_romantic", "label": "Технический крой", "emoji": "🛰️", "description": "Технические ткани и utility-силуэты с мягким слоем или неожиданной фактурой.", "palette_hint": ["black", "charcoal", "olive", "silver", "ivory"]},
    {"id": "americana_90s", "label": "Американа", "emoji": "🇺🇸", "description": "90s sportswear, straight denim, plaid, frontier knit и винтажная простота.", "palette_hint": ["blue", "brown", "cream", "red", "green"]},
    {"id": "accessory_first", "label": "Аксессуарный акцент", "emoji": "⛓️", "description": "Сначала характерный аксессуар, затем одежда строится вокруг него.", "palette_hint": ["black", "silver", "brown", "white", "pink"]},
    {"id": "pink_accent", "label": "Розовый акцент", "emoji": "🌸", "description": "Пыльно-розовый как точечный акцент на строгой, рабочей или кожаной базе.", "palette_hint": ["dusty_pink", "black", "brown", "navy", "cream"]},
    {"id": "sport_couture", "label": "Спортивный кутюр", "emoji": "⚽", "description": "Спортивная форма + tailoring: ретро-спорт, трековые вещи и точный низ.", "palette_hint": ["navy", "red", "cream", "black", "green"]},
    {"id": "neo_gothic_editorial", "label": "Неоготика", "emoji": "🖤", "description": "Тёмный силуэт, кожа, длинные линии и editorial-подача.", "palette_hint": ["black", "charcoal", "burgundy", "silver", "ivory"]},
    {"id": "post_punk_archive", "label": "Постпанк-архив", "emoji": "🎛️", "description": "Пост-панк, архивные пропорции, потёртые материалы и намеренная шероховатость.", "palette_hint": ["black", "grey", "burgundy", "olive", "white"]},
    {"id": "minimal_precision", "label": "Точный минимализм", "emoji": "◻️", "description": "Минимализм через пропорции, материал и точный крой.", "palette_hint": ["black", "white", "grey", "navy", "brown"]},
]

STYLE_ALIASES: dict[str, str] = {
    "minimal": "minimal_precision",
    "streetwear": "americana_90s",
    "techwear": "technical_romantic",
    "old_money": "minimal_precision",
    "romantic": "romantic_menswear",
    "grunge": "post_punk_archive",
    "avantgarde": "archive_reconstruction",
    "workwear": "modern_craftsman",
    "gothic": "neo_gothic_editorial",
    "balletcore": "romantic_menswear",
}

MOOD_OPTIONS: list[dict[str, Any]] = [
    {"id": "confident", "label": "Уверенность", "emoji": "🦁", "description": "Держу комнату, когда вхожу."},
    {"id": "calm", "label": "Спокойствие", "emoji": "🍃", "description": "Мягко, ровно, без напряжения."},
    {"id": "playful", "label": "Игривость", "emoji": "🎈", "description": "Хочется цвета и лёгкости."},
    {"id": "bold", "label": "Дерзость", "emoji": "⚡", "description": "Заметный образ, который обсуждают."},
    {"id": "cozy", "label": "Уют", "emoji": "☕", "description": "Тепло, мягко, обнимающе."},
    {"id": "elegant", "label": "Элегантность", "emoji": "🥂", "description": "Сдержанно и дорого."},
    {"id": "energetic", "label": "Энергия", "emoji": "🔥", "description": "Движение и скорость в образе."},
    {"id": "mysterious", "label": "Загадочность", "emoji": "🌙", "description": "Тёмная палитра и недосказанность."},
]

OCCASION_OPTIONS: list[dict[str, Any]] = [
    {"id": "everyday", "label": "Каждый день", "formality": 1},
    {"id": "work", "label": "Работа", "formality": 3},
    {"id": "date", "label": "Свидание", "formality": 2},
    {"id": "party", "label": "Вечеринка", "formality": 3},
    {"id": "travel", "label": "Путешествие", "formality": 1},
    {"id": "event", "label": "Событие", "formality": 4},
]

SEASON_OPTIONS: list[dict[str, Any]] = [
    {"id": "all", "label": "Любой сезон"},
    {"id": "spring", "label": "Весна"},
    {"id": "summer", "label": "Лето"},
    {"id": "autumn", "label": "Осень"},
    {"id": "winter", "label": "Зима"},
]

PRESENTATION_OPTIONS: list[dict[str, Any]] = [
    {"id": "unisex", "label": "Унисекс"},
    {"id": "feminine", "label": "Женственный"},
    {"id": "masculine", "label": "Мужественный"},
]

CATEGORY_LABELS: dict[str, str] = {
    "outerwear": "Верх",
    "top": "Верхняя часть",
    "bottom": "Низ",
    "footwear": "Обувь",
    "accessory": "Аксессуар",
}

SLOT_LABELS: dict[str, str] = {
    "outer": "Верхняя одежда",
    "top": "Верх",
    "bottom": "Низ",
    "shoes": "Обувь",
    "accessory": "Аксессуар",
}

OUTFIT_PLANS: dict[str, dict[str, Any]] = {
    "layered": {"description": "Многослойный образ с верхней одеждой", "slots": {"outer": True, "top": True, "bottom": True, "shoes": True, "accessory": True}},
    "dress": {"description": "Образ на основе платья", "slots": {"outer": False, "top": True, "bottom": False, "shoes": True, "accessory": True}},
    "light": {"description": "Лёгкий образ без верхней одежды", "slots": {"outer": False, "top": True, "bottom": True, "shoes": True, "accessory": True}},
}

def style_by_id(requested: str) -> dict[str, Any]:
    key = STYLE_ALIASES.get(requested, requested)
    return next((option for option in STYLE_OPTIONS if option["id"] == key), STYLE_OPTIONS[0])

def mood_by_id(mood_id: str) -> dict[str, Any]:
    return next((option for option in MOOD_OPTIONS if option["id"] == mood_id), MOOD_OPTIONS[0])

def occasion_formality(occasion: str) -> int:
    return next((int(option["formality"]) for option in OCCASION_OPTIONS if option["id"] == occasion), 1)

def meta_payload() -> dict[str, Any]:
    return {
        "styles": STYLE_OPTIONS,
        "moods": MOOD_OPTIONS,
        "occasions": OCCASION_OPTIONS,
        "seasons": SEASON_OPTIONS,
        "presentations": PRESENTATION_OPTIONS,
        "categories": [{"id": key, "label": value} for key, value in CATEGORY_LABELS.items()],
        "slots": [{"id": key, "label": value} for key, value in SLOT_LABELS.items()],
    }
