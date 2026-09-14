"""Fashion taxonomy: styles, moods, occasions, slots and slot budget weights.

Everything the UI needs for its selectors is served from here, so the client and
the ranking engine can never drift apart.
"""

from __future__ import annotations

from typing import Any

STYLE_OPTIONS: list[dict[str, Any]] = [
    {
        "id": "minimal",
        "label": "Минимализм",
        "emoji": "◻️",
        "description": "Чистые линии, монохром, качественные ткани, ничего лишнего.",
        "palette_hint": ["black", "white", "grey", "beige", "navy"],
    },
    {
        "id": "old_money",
        "label": "Old money",
        "emoji": "🐎",
        "description": "Тихая роскошь: кашемир, лоферы, сдержанная палитра и идеальная посадка.",
        "palette_hint": ["camel", "navy", "ivory", "chocolate", "emerald"],
    },
    {
        "id": "streetwear",
        "label": "Стритвир",
        "emoji": "🛹",
        "description": "Оверсайз, кроссовки, лого-культура и смелые силуэты.",
        "palette_hint": ["black", "grey", "olive", "orange", "white"],
    },
    {
        "id": "business_casual",
        "label": "Бизнес-кэжуал",
        "emoji": "💼",
        "description": "Пиджак вместо галстука: собранно, но не формально.",
        "palette_hint": ["navy", "grey", "white", "camel", "burgundy"],
    },
    {
        "id": "techwear",
        "label": "Теквир",
        "emoji": "🛰️",
        "description": "Функциональные ткани, чёрный тотал, карманы и ремни.",
        "palette_hint": ["black", "charcoal", "olive", "grey"],
    },
    {
        "id": "romantic",
        "label": "Романтика",
        "emoji": "🌸",
        "description": "Мягкие ткани, светлая палитра, летящие силуэты.",
        "palette_hint": ["blush", "ivory", "lavender", "beige", "pink"],
    },
    {
        "id": "athleisure",
        "label": "Спорт-шик",
        "emoji": "🏃",
        "description": "Спортивный комфорт, который уместен и в городе.",
        "palette_hint": ["black", "grey", "white", "navy", "teal"],
    },
    {
        "id": "grunge",
        "label": "Гранж",
        "emoji": "🎸",
        "description": "Деним, кожа, потёртости и небрежная многослойность.",
        "palette_hint": ["black", "charcoal", "brown", "olive", "burgundy"],
    },
    {
        "id": "boho",
        "label": "Бохо",
        "emoji": "🌾",
        "description": "Свободные силуэты, природные оттенки, этнические мотивы.",
        "palette_hint": ["terracotta", "sand", "olive", "brown", "mustard"],
    },
    {
        "id": "avantgarde",
        "label": "Авангард",
        "emoji": "🖤",
        "description": "Архитектурный крой, асимметрия, чёрный как главный цвет.",
        "palette_hint": ["black", "charcoal", "white", "silver"],
    },
]

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
    "outerwear": "Верхняя одежда",
    "top": "Верх",
    "knitwear": "Трикотаж",
    "bottom": "Низ",
    "dress": "Платье",
    "shoes": "Обувь",
    "bag": "Сумка",
    "accessory": "Аксессуар",
}

#: Slots that build a complete look, in rendering order.
SLOTS: tuple[str, ...] = ("outerwear", "top", "knitwear", "bottom", "dress", "shoes", "bag", "accessory")

SLOT_LABELS: dict[str, str] = {
    "outerwear": "Верхняя одежда",
    "top": "Верх",
    "knitwear": "Трикотаж",
    "bottom": "Низ",
    "dress": "Платье",
    "shoes": "Обувь",
    "bag": "Сумка",
    "accessory": "Аксессуар",
}

#: Which categories can fill which slot.
SLOT_CATEGORIES: dict[str, tuple[str, ...]] = {
    "outerwear": ("outerwear",),
    "top": ("top", "knitwear"),
    "bottom": ("bottom",),
    "dress": ("dress",),
    "shoes": ("shoes",),
    "bag": ("bag",),
    "accessory": ("accessory",),
}

#: Share of the budget each slot may claim, plus whether it can be dropped.
SLOT_PLANS: dict[str, dict[str, Any]] = {
    "layered": {
        "description": "Многослойный образ с верхней одеждой",
        "slots": {
            "outerwear": {"weight": 0.30, "required": True, "order": 0},
            "top": {"weight": 0.14, "required": True, "order": 1},
            "bottom": {"weight": 0.16, "required": True, "order": 3},
            "shoes": {"weight": 0.20, "required": True, "order": 4},
            "bag": {"weight": 0.14, "required": False, "order": 5},
            "accessory": {"weight": 0.06, "required": False, "order": 6},
        },
    },
    "dress": {
        "description": "Образ на основе платья",
        "slots": {
            "outerwear": {"weight": 0.26, "required": False, "order": 0},
            "dress": {"weight": 0.32, "required": True, "order": 2},
            "shoes": {"weight": 0.22, "required": True, "order": 4},
            "bag": {"weight": 0.14, "required": False, "order": 5},
            "accessory": {"weight": 0.06, "required": False, "order": 6},
        },
    },
    "light": {
        "description": "Лёгкий образ без верхней одежды",
        "slots": {
            "top": {"weight": 0.22, "required": True, "order": 1},
            "bottom": {"weight": 0.26, "required": True, "order": 3},
            "shoes": {"weight": 0.26, "required": True, "order": 4},
            "bag": {"weight": 0.18, "required": False, "order": 5},
            "accessory": {"weight": 0.08, "required": False, "order": 6},
        },
    },
}


def plan_for_season(season: str, occasion: str) -> str:
    """Pick a look plan: dresses for warm weather/events, layers for cold."""
    if season in ("winter", "autumn"):
        return "layered"
    if occasion in ("event", "party", "date") and season in ("summer", "all", "spring"):
        return "dress"
    if season == "summer":
        return "light"
    return "layered"


def style_by_id(style_id: str) -> dict[str, Any]:
    for option in STYLE_OPTIONS:
        if option["id"] == style_id:
            return option
    return STYLE_OPTIONS[0]


def mood_by_id(mood_id: str) -> dict[str, Any]:
    for option in MOOD_OPTIONS:
        if option["id"] == mood_id:
            return option
    return MOOD_OPTIONS[0]


def formality_for_occasion(occasion: str) -> int:
    for option in OCCASION_OPTIONS:
        if option["id"] == occasion:
            return int(option["formality"])
    return 1


def all_options() -> dict[str, Any]:
    return {
        "styles": STYLE_OPTIONS,
        "moods": MOOD_OPTIONS,
        "occasions": OCCASION_OPTIONS,
        "seasons": SEASON_OPTIONS,
        "presentations": PRESENTATION_OPTIONS,
        "categories": [{"id": key, "label": value} for key, value in CATEGORY_LABELS.items()],
        "slots": [{"id": key, "label": value} for key, value in SLOT_LABELS.items()],
    }
