"""Fashion taxonomy v2: current, niche-first styles and stable compatibility aliases."""

from __future__ import annotations
from typing import Any

# UI taxonomy is intentionally curated rather than a dump of internet micro-trends.
# Legacy IDs remain accepted by style_by_id() so saved profiles do not break, but
# they are no longer presented as primary choices.
STYLE_OPTIONS: list[dict[str, Any]] = [
    {"id": "modern_craftsman", "label": "Современный ремесленник", "emoji": "🧵", "description": "Современный ремесленник: workwear, field jacket, выцветший деним, фактуры и один сильный аксессуар.", "palette_hint": ["brown", "olive", "navy", "cream", "mustard"]},
    {"id": "leather_weather", "label": "В коже", "emoji": "🧥", "description": "Состаренная кожа, мото-архетипы и мягкий контраст с трикотажем или строгим кроем.", "palette_hint": ["black", "brown", "burgundy", "cream", "olive"]},
    {"id": "broken_down_prep", "label": "Небрежный prep", "emoji": "🏄", "description": "Ivy/prep, намеренно расслабленный крой и surf-детали вместо стерильной классики.", "palette_hint": ["navy", "cream", "red", "brown", "washed_blue"]},
    {"id": "romantic_menswear", "label": "Романтичный костюм", "emoji": "🌹", "description": "Драпировка, полупрозрачные слои, мягкий tailoring и намеренно чувственная пропорция.", "palette_hint": ["black", "ivory", "burgundy", "dusty_pink", "brown"]},
    {"id": "military_romance", "label": "Военная романтика", "emoji": "🎖️", "description": "Военная конструкция + викторианская/флоральная деталь; строгая база и один декоративный сбой.", "palette_hint": ["olive", "black", "burgundy", "cream", "khaki"]},
    {"id": "archive_reconstruction", "label": "Архивная пересборка", "emoji": "🧩", "description": "Архивные вещи, deadstock и reworked-конструкция вместо буквального копирования образа с подиума.", "palette_hint": ["black", "grey", "denim", "brown", "white"]},
    {"id": "technical_romantic", "label": "Техно-романтика", "emoji": "🛰️", "description": "Технические ткани и utility-силуэты, но с мягким слоем, драпировкой или неожиданной фактурой.", "palette_hint": ["black", "charcoal", "olive", "silver", "ivory"]},
    {"id": "americana_90s", "label": "Американа 90-х", "emoji": "🇺🇸", "description": "90s sportswear, straight denim, plaid, frontier knit и винтажная простота без костюмности.", "palette_hint": ["blue", "brown", "cream", "red", "green"]},
    {"id": "accessory_first", "label": "Акцент на аксессуарах", "emoji": "⛓️", "description": "Сначала характерный аксессуар, затем одежда строится вокруг него — цепь, cuff, charm, ремень.", "palette_hint": ["black", "silver", "brown", "white", "pink"]},
    {"id": "pink_accent", "label": "Пыльно-розовый акцент", "emoji": "🌸", "description": "Пыльно-розовый как точечный мужской акцент на строгой, рабочей или кожаной базе.", "palette_hint": ["dusty_pink", "black", "brown", "navy", "cream"]},
    {"id": "sport_couture", "label": "Спортивный кутюр", "emoji": "⚽", "description": "Спортивная форма мышления + tailoring: ретро-спорт, трековые вещи и точный низ.", "palette_hint": ["navy", "red", "cream", "black", "green"]},
    {"id": "neo_gothic_editorial", "label": "Неоготика", "emoji": "🖤", "description": "Тёмный силуэт, кожа, длинные линии и editorial-подача без костюмного Halloween-goth.", "palette_hint": ["black", "charcoal", "burgundy", "silver", "ivory"]},
    {"id": "post_punk_archive", "label": "Постпанк-архив", "emoji": "🎛️", "description": "Пост-панк, архивные пропорции, потёртые материалы и намеренная шероховатость.", "palette_hint": ["black", "grey", "burgundy", "olive", "white"]},
    {"id": "minimal_precision", "label": "Точный минимализм", "emoji": "◻️", "description": "Минимализм через пропорции, материал и точный крой — без old-money шаблона.", "palette_hint": ["black", "white", "grey", "navy", "brown"]},
]

# Persisted profiles from v1 may contain these IDs. They are compatibility aliases,
# not UI recommendations.
LEGACY_STYLE_ALIASES: dict[str, str] = {
    "minimal": "minimal_precision", "old_money": "broken_down_prep", "streetwear": "sport_couture",
    "business_casual": "minimal_precision", "techwear": "technical_romantic", "romantic": "romantic_menswear",
    "athleisure": "sport_couture", "grunge": "post_punk_archive", "boho": "modern_craftsman",
    "avantgarde": "archive_reconstruction", "office_siren": "minimal_precision", "gorpcore": "technical_romantic",
    "y2k": "sport_couture", "indie_sleaze": "post_punk_archive", "dark_academia": "archive_reconstruction",
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
    {"id": "everyday", "label": "Каждый день", "formality": 1}, {"id": "work", "label": "Работа", "formality": 3},
    {"id": "date", "label": "Свидание", "formality": 2}, {"id": "party", "label": "Вечеринка", "formality": 3},
    {"id": "travel", "label": "Путешествие", "formality": 1}, {"id": "event", "label": "Событие", "formality": 4},
]
SEASON_OPTIONS: list[dict[str, Any]] = [
    {"id": "all", "label": "Любой сезон"}, {"id": "spring", "label": "Весна"}, {"id": "summer", "label": "Лето"},
    {"id": "autumn", "label": "Осень"}, {"id": "winter", "label": "Зима"},
]
PRESENTATION_OPTIONS: list[dict[str, Any]] = [
    {"id": "unisex", "label": "Унисекс"}, {"id": "feminine", "label": "Женственный"}, {"id": "masculine", "label": "Мужественный"},
]
CATEGORY_LABELS: dict[str, str] = {
    "outerwear": "Верхняя одежда", "top": "Верх", "knitwear": "Трикотаж", "bottom": "Низ",
    "dress": "Платье", "shoes": "Обувь", "bag": "Сумка", "accessory": "Аксессуар",
}
SLOTS: tuple[str, ...] = ("outerwear", "top", "knitwear", "bottom", "dress", "shoes", "bag", "accessory")
SLOT_LABELS: dict[str, str] = {key: value for key, value in CATEGORY_LABELS.items()}
SLOT_CATEGORIES: dict[str, tuple[str, ...]] = {
    "outerwear": ("outerwear",), "top": ("top", "knitwear"), "bottom": ("bottom",), "dress": ("dress",),
    "shoes": ("shoes",), "bag": ("bag",), "accessory": ("accessory",),
}
SLOT_PLANS: dict[str, dict[str, Any]] = {
    "layered": {"description": "Многослойный образ с верхней одеждой", "slots": {
        "outerwear": {"weight": .30, "required": True, "order": 0}, "top": {"weight": .14, "required": True, "order": 1},
        "bottom": {"weight": .16, "required": True, "order": 3}, "shoes": {"weight": .20, "required": True, "order": 4},
        "bag": {"weight": .14, "required": False, "order": 5}, "accessory": {"weight": .06, "required": False, "order": 6},}},
    "dress": {"description": "Образ на основе платья", "slots": {
        "outerwear": {"weight": .26, "required": False, "order": 0}, "dress": {"weight": .32, "required": True, "order": 2},
        "shoes": {"weight": .22, "required": True, "order": 4}, "bag": {"weight": .14, "required": False, "order": 5},
        "accessory": {"weight": .06, "required": False, "order": 6},}},
    "light": {"description": "Лёгкий образ без верхней одежды", "slots": {
        "top": {"weight": .22, "required": True, "order": 1}, "bottom": {"weight": .26, "required": True, "order": 3},
        "shoes": {"weight": .26, "required": True, "order": 4}, "bag": {"weight": .18, "required": False, "order": 5},
        "accessory": {"weight": .08, "required": False, "order": 6},}},
}


def plan_for_season(season: str, occasion: str) -> str:
    if season in ("winter", "autumn"): return "layered"
    if occasion in ("event", "party", "date") and season in ("summer", "all", "spring"): return "dress"
    if season == "summer": return "light"
    return "layered"


def style_by_id(style_id: str) -> dict[str, Any]:
    requested = LEGACY_STYLE_ALIASES.get(style_id, style_id)
    return next((option for option in STYLE_OPTIONS if option["id"] == requested), STYLE_OPTIONS[0])


def mood_by_id(mood_id: str) -> dict[str, Any]:
    return next((option for option in MOOD_OPTIONS if option["id"] == mood_id), MOOD_OPTIONS[0])


def formality_for_occasion(occasion: str) -> int:
    return next((int(option["formality"]) for option in OCCASION_OPTIONS if option["id"] == occasion), 1)


def all_options() -> dict[str, Any]:
    return {"styles": STYLE_OPTIONS, "moods": MOOD_OPTIONS, "occasions": OCCASION_OPTIONS,
            "seasons": SEASON_OPTIONS, "presentations": PRESENTATION_OPTIONS,
            "categories": [{"id": key, "label": value} for key, value in CATEGORY_LABELS.items()],
            "slots": [{"id": key, "label": value} for key, value in SLOT_LABELS.items()]}
