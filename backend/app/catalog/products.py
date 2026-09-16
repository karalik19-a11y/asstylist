"""Seed catalog.

Real-shaped product data with prices in RUB, spread across the whole 0–100 000 ₽
budget range so the optimiser has something to work with. A few rows are
deliberately broken to demonstrate the verification layer.
"""

from __future__ import annotations

from typing import Any

CLOTHING_SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
SHOE_SIZES = ["36", "37", "38", "39", "40", "41", "42", "43", "44", "45"]
ONE_SIZE = ["one size"]

CATEGORY_SIZES = {
    "outerwear": CLOTHING_SIZES,
    "top": CLOTHING_SIZES,
    "knitwear": CLOTHING_SIZES,
    "bottom": CLOTHING_SIZES,
    "dress": CLOTHING_SIZES,
    "shoes": SHOE_SIZES,
    "bag": ONE_SIZE,
    "accessory": ONE_SIZE,
}

#: Items that read as feminine. A "masculine" presentation never receives them;
#: "unisex" and "feminine" both can.
FEMININE_ITEMS = {
    "BT-005", "BT-006", "BT-012",          # skirts
    "DR-001", "DR-002", "DR-003", "DR-004", "DR-005", "DR-006", "DR-007", "DR-008", "DR-010",
    "SH-006", "SH-008", "SH-012",          # ballet flats, heeled boots, pumps
    "TP-006", "TP-008",                    # bustier top, ruffle blouse
    "KN-008",
    # трендовые позиции 2026
    "BT-016", "BT-021",                    # pencil skirt, tulle midi
    "TP-018", "TP-019",                    # pussy-bow blouse, baby tee
    "SH-016", "SH-020",                    # slingbacks, ribbon ballet flats
    "BG-013",                              # baguette bag
    "AC-014", "AC-016",                    # fishnet tights, leg warmers
    "KN-013",                              # wrap cardigan
}

BRAND_SOURCES: dict[str, tuple[str, str]] = {
    "12 STOREEZ": ("12storeez", "https://12storeez.com"),
    "Uniqlo": ("uniqlo", "https://www.uniqlo.com"),
    "Uniqlo Sport": ("uniqlo", "https://www.uniqlo.com"),
    "SOKOLOV": ("sokolov", "https://sokolov.ru"),
}
FALLBACK_SOURCE = ("lamoda", "https://www.lamoda.ru")

# (sku, category, name, brand, price, colors, styles, moods, formality, fit, seasons, rating, reviews)
_ROWS: list[tuple] = [
    # --- outerwear -----------------------------------------------------
    ("OW-001", "outerwear", "Пальто шерстяное прямое", "12 STOREEZ", 24900, ["camel"], ["minimal", "old_money", "business_casual"], ["elegant", "calm", "confident"], 3, "regular", ["autumn", "winter"], 4.7, 412),
    ("OW-002", "outerwear", "Пальто оверсайз двубортное", "12 STOREEZ", 29900, ["charcoal"], ["minimal", "avantgarde"], ["mysterious", "confident"], 3, "oversize", ["autumn", "winter"], 4.6, 288),
    ("OW-003", "outerwear", "Тренч классический", "Uniqlo", 12990, ["beige"], ["minimal", "business_casual", "old_money"], ["elegant", "calm"], 3, "regular", ["spring", "autumn"], 4.5, 630),
    ("OW-004", "outerwear", "Куртка кожаная косуха", "Lamoda Select", 19990, ["black"], ["grunge", "streetwear", "avantgarde"], ["bold", "confident"], 2, "slim", ["all"], 4.4, 521),
    ("OW-005", "outerwear", "Пуховик стёганый удлинённый", "Uniqlo", 15990, ["navy"], ["minimal", "athleisure"], ["cozy", "calm"], 1, "relaxed", ["winter"], 4.3, 890),
    ("OW-006", "outerwear", "Бомбер нейлоновый", "Street Lab", 8990, ["olive"], ["streetwear", "athleisure", "techwear"], ["energetic", "playful"], 1, "relaxed", ["all"], 4.2, 344),
    ("OW-007", "outerwear", "Жакет однобортный", "12 STOREEZ", 16900, ["grey"], ["business_casual", "minimal", "old_money"], ["confident", "elegant"], 3, "regular", ["all"], 4.6, 275),
    ("OW-008", "outerwear", "Парка технологичная", "Techform", 21900, ["black"], ["techwear", "streetwear"], ["confident", "mysterious"], 2, "relaxed", ["winter", "autumn"], 4.4, 190),
    ("OW-009", "outerwear", "Кардиган длинный вязаный", "Cozy Line", 9990, ["ivory"], ["romantic", "boho", "minimal"], ["cozy", "calm"], 1, "relaxed", ["all"], 4.5, 410),
    ("OW-010", "outerwear", "Жилет стёганый", "Uniqlo", 6990, ["khaki"], ["athleisure", "streetwear"], ["energetic", "cozy"], 1, "relaxed", ["autumn", "spring"], 4.1, 233),
    ("OW-011", "outerwear", "Пальто-халат кашемир", "Cashmere Lab", 39900, ["chocolate"], ["old_money", "minimal"], ["elegant", "calm", "confident"], 3, "relaxed", ["winter"], 4.8, 96),
    ("OW-012", "outerwear", "Куртка джинсовая оверсайз", "Street Lab", 7990, ["blue"], ["grunge", "streetwear", "boho"], ["playful", "energetic"], 1, "oversize", ["spring", "autumn"], 4.3, 512),
    ("OW-013", "outerwear", "Куртка стёганая лёгкая", "Uniqlo", 3990, ["black"], ["minimal", "athleisure", "streetwear"], ["cozy", "energetic"], 1, "relaxed", ["spring", "autumn"], 4.2, 540),
    # --- tops ----------------------------------------------------------
    ("TP-001", "top", "Футболка базовая плотная", "Uniqlo", 1990, ["white", "black"], ["minimal", "streetwear", "athleisure"], ["calm", "cozy"], 1, "regular", ["all"], 4.6, 2310),
    ("TP-002", "top", "Рубашка хлопковая oversize", "12 STOREEZ", 6990, ["white"], ["minimal", "business_casual", "old_money"], ["calm", "confident"], 3, "oversize", ["all"], 4.7, 880),
    ("TP-003", "top", "Рубашка шёлковая", "Silk Route", 12900, ["ivory"], ["old_money", "romantic"], ["elegant", "calm"], 3, "regular", ["all"], 4.5, 210),
    ("TP-004", "top", "Футболка с принтом", "Street Lab", 2990, ["black"], ["streetwear", "grunge"], ["bold", "energetic"], 1, "relaxed", ["all"], 4.2, 743),
    ("TP-005", "top", "Водолазка тонкая", "Uniqlo", 3490, ["charcoal"], ["minimal", "business_casual", "techwear"], ["calm", "mysterious"], 2, "slim", ["all"], 4.5, 1120),
    ("TP-006", "top", "Топ-бюстье", "Atelier No.5", 4990, ["black"], ["avantgarde", "romantic"], ["bold", "confident"], 2, "slim", ["summer"], 4.1, 132),
    ("TP-007", "top", "Поло трикотажное", "Old Money Club", 7990, ["navy"], ["old_money", "business_casual"], ["elegant", "confident"], 2, "regular", ["all"], 4.6, 356),
    ("TP-008", "top", "Блуза с воланами", "Atelier No.5", 8990, ["blush"], ["romantic", "boho"], ["playful", "calm"], 2, "relaxed", ["all"], 4.4, 188),
    ("TP-009", "top", "Лонгслив спортивный", "Runform", 3290, ["grey"], ["athleisure", "streetwear"], ["energetic", "cozy"], 1, "slim", ["all"], 4.3, 640),
    ("TP-010", "top", "Рубашка фланелевая в клетку", "Street Lab", 4490, ["burgundy"], ["grunge", "boho"], ["cozy", "playful"], 1, "relaxed", ["autumn", "winter"], 4.4, 402),
    ("TP-011", "top", "Топ кроп трикотажный", "Street Lab", 2490, ["black"], ["streetwear", "athleisure"], ["bold", "energetic"], 1, "slim", ["summer", "spring"], 4.0, 512),
    ("TP-012", "top", "Рубашка льняная", "Linen Lab", 5990, ["sand"], ["boho", "minimal", "romantic"], ["calm", "cozy"], 2, "relaxed", ["summer"], 4.5, 298),
    ("TP-013", "top", "Боди базовое", "Uniqlo", 2990, ["beige"], ["minimal", "old_money"], ["calm", "elegant"], 2, "slim", ["all"], 4.4, 720),
    ("TP-014", "top", "Рубашка техническая", "Techform", 8490, ["charcoal"], ["techwear", "streetwear"], ["confident", "mysterious"], 2, "regular", ["all"], 4.3, 156),
    ("TP-015", "top", "Футболка премиум-хлопок", "12 STOREEZ", 3990, ["ivory"], ["minimal", "old_money"], ["calm", "elegant"], 1, "regular", ["all"], 4.7, 610),
    ("TP-016", "top", "Свитшот оверсайз", "Street Lab", 5490, ["olive"], ["streetwear", "athleisure"], ["cozy", "energetic"], 1, "oversize", ["all"], 4.4, 830),
    ("TP-017", "top", "Футболка базовая хлопок", "Street Lab", 1290, ["grey", "white"], ["minimal", "streetwear", "athleisure"], ["calm", "cozy"], 1, "regular", ["all"], 4.1, 1500),
    # --- knitwear ------------------------------------------------------
    ("KN-001", "knitwear", "Свитер кашемир", "Cashmere Lab", 22900, ["camel"], ["old_money", "minimal"], ["elegant", "cozy", "calm"], 2, "regular", ["winter", "autumn"], 4.8, 187),
    ("KN-002", "knitwear", "Свитер шерстяной с косами", "Cozy Line", 8990, ["ivory"], ["romantic", "minimal", "boho"], ["cozy", "calm"], 2, "relaxed", ["winter"], 4.6, 421),
    ("KN-003", "knitwear", "Джемпер тонкий меринос", "Uniqlo", 5990, ["navy"], ["minimal", "business_casual", "old_money"], ["calm", "elegant"], 2, "slim", ["all"], 4.5, 930),
    ("KN-004", "knitwear", "Худи оверсайз", "Street Lab", 6490, ["grey"], ["streetwear", "athleisure"], ["cozy", "energetic"], 1, "oversize", ["all"], 4.5, 1240),
    ("KN-005", "knitwear", "Кардиган на пуговицах", "Cozy Line", 7490, ["blush"], ["romantic", "old_money"], ["cozy", "playful"], 2, "regular", ["all"], 4.4, 268),
    ("KN-006", "knitwear", "Свитер с высоким воротом", "12 STOREEZ", 9990, ["charcoal"], ["minimal", "techwear", "avantgarde"], ["mysterious", "confident"], 2, "regular", ["winter"], 4.6, 342),
    ("KN-007", "knitwear", "Жилет трикотажный", "Old Money Club", 6990, ["beige"], ["old_money", "minimal"], ["elegant", "playful"], 2, "regular", ["all"], 4.3, 174),
    ("KN-008", "knitwear", "Свитер оверсайз мохер", "Atelier No.5", 13900, ["lavender"], ["romantic", "avantgarde"], ["cozy", "playful"], 2, "oversize", ["winter"], 4.4, 96),
    ("KN-009", "knitwear", "Поло-свитер", "Old Money Club", 11900, ["emerald"], ["old_money", "business_casual"], ["elegant", "confident"], 2, "regular", ["autumn", "winter"], 4.5, 143),
    ("KN-010", "knitwear", "Джемпер спортивный", "Runform", 4990, ["teal"], ["athleisure", "streetwear"], ["energetic"], 1, "relaxed", ["all"], 4.2, 388),
    ("KN-011", "knitwear", "Свитер базовый", "Street Lab", 3490, ["grey"], ["minimal", "streetwear"], ["cozy", "calm"], 1, "regular", ["all"], 4.2, 400),
    # --- bottoms -------------------------------------------------------
    ("BT-001", "bottom", "Брюки прямые шерсть", "12 STOREEZ", 9990, ["charcoal"], ["minimal", "business_casual", "old_money"], ["confident", "elegant"], 3, "regular", ["all"], 4.6, 540),
    ("BT-002", "bottom", "Джинсы прямые", "Uniqlo", 4990, ["blue"], ["minimal", "streetwear", "grunge"], ["calm", "energetic"], 1, "regular", ["all"], 4.5, 2100),
    ("BT-003", "bottom", "Джинсы широкие", "Street Lab", 6990, ["blue"], ["streetwear", "boho"], ["playful", "energetic"], 1, "relaxed", ["all"], 4.4, 980),
    ("BT-004", "bottom", "Брюки палаццо", "Atelier No.5", 11900, ["black"], ["avantgarde", "minimal", "old_money"], ["elegant", "confident"], 2, "relaxed", ["all"], 4.5, 320),
    ("BT-005", "bottom", "Юбка миди плиссе", "Atelier No.5", 8990, ["navy"], ["romantic", "old_money", "business_casual"], ["elegant", "playful"], 2, "regular", ["all"], 4.4, 276),
    ("BT-006", "bottom", "Юбка мини кожаная", "Street Lab", 7990, ["black"], ["grunge", "avantgarde", "streetwear"], ["bold", "confident"], 2, "slim", ["all"], 4.2, 214),
    ("BT-007", "bottom", "Чиносы хлопковые", "Uniqlo", 4490, ["sand"], ["minimal", "business_casual", "athleisure"], ["calm", "cozy"], 1, "regular", ["all"], 4.4, 1560),
    ("BT-008", "bottom", "Брюки карго", "Techform", 8990, ["olive"], ["techwear", "streetwear"], ["confident", "energetic"], 1, "relaxed", ["all"], 4.3, 402),
    ("BT-009", "bottom", "Джинсы skinny", "Street Lab", 4990, ["black"], ["grunge", "streetwear"], ["bold"], 1, "slim", ["all"], 4.1, 720),
    ("BT-010", "bottom", "Шорты бермуды", "Linen Lab", 3990, ["beige"], ["boho", "minimal", "athleisure"], ["calm", "playful"], 1, "regular", ["summer"], 4.2, 244),
    ("BT-011", "bottom", "Брюки спортивные", "Runform", 3990, ["grey"], ["athleisure", "streetwear"], ["cozy", "energetic"], 1, "relaxed", ["all"], 4.4, 880),
    ("BT-012", "bottom", "Юбка макси льняная", "Linen Lab", 6990, ["terracotta"], ["boho", "romantic"], ["calm", "playful"], 1, "relaxed", ["summer"], 4.3, 132),
    ("BT-013", "bottom", "Брюки классические со стрелками", "Old Money Club", 12900, ["grey"], ["business_casual", "old_money", "minimal"], ["confident", "elegant"], 3, "regular", ["all"], 4.6, 198),
    ("BT-014", "bottom", "Джинсы белые", "12 STOREEZ", 7990, ["white"], ["minimal", "old_money"], ["calm", "elegant"], 1, "regular", ["summer", "spring"], 4.5, 310),
    ("BT-015", "bottom", "Джинсы базовые", "Street Lab", 2990, ["blue"], ["minimal", "streetwear", "grunge"], ["calm", "energetic"], 1, "regular", ["all"], 4.2, 980),
    # --- dresses -------------------------------------------------------
    ("DR-001", "dress", "Платье-комбинация шёлк", "Atelier No.5", 15900, ["beige"], ["romantic", "old_money", "avantgarde"], ["elegant", "confident"], 3, "regular", ["all"], 4.6, 210),
    ("DR-002", "dress", "Платье миди трикотаж", "12 STOREEZ", 11900, ["black"], ["minimal", "old_money"], ["elegant", "calm"], 2, "slim", ["all"], 4.5, 388),
    ("DR-003", "dress", "Платье-рубашка", "Linen Lab", 8990, ["white"], ["minimal", "boho"], ["calm", "playful"], 2, "relaxed", ["summer"], 4.4, 276),
    ("DR-004", "dress", "Платье макси с принтом", "Atelier No.5", 13900, ["pink"], ["romantic", "boho"], ["playful", "calm"], 2, "relaxed", ["summer", "spring"], 4.5, 190),
    ("DR-005", "dress", "Платье-футляр", "Old Money Club", 17900, ["navy"], ["business_casual", "old_money"], ["confident", "elegant"], 3, "slim", ["all"], 4.6, 154),
    ("DR-006", "dress", "Платье мини оверсайз", "Street Lab", 6990, ["black"], ["streetwear", "avantgarde"], ["bold", "energetic"], 1, "oversize", ["all"], 4.1, 268),
    ("DR-007", "dress", "Платье вязаное", "Cozy Line", 9990, ["camel"], ["romantic", "old_money"], ["cozy", "elegant"], 2, "relaxed", ["winter", "autumn"], 4.4, 122),
    ("DR-008", "dress", "Платье асимметричное", "Avant Studio", 21900, ["violet"], ["avantgarde"], ["bold", "mysterious"], 3, "relaxed", ["all"], 4.3, 74),
    ("DR-009", "dress", "Платье спортивное", "Runform", 4990, ["grey"], ["athleisure", "streetwear"], ["energetic", "cozy"], 1, "relaxed", ["all"], 4.2, 340),
    ("DR-010", "dress", "Сарафан льняной", "Linen Lab", 7990, ["sand"], ["boho", "romantic", "minimal"], ["calm", "cozy"], 1, "relaxed", ["summer"], 4.4, 205),
    # --- shoes ---------------------------------------------------------
    ("SH-001", "shoes", "Кроссовки белые кожаные", "Uniqlo Sport", 8990, ["white"], ["minimal", "streetwear", "athleisure"], ["calm", "energetic"], 1, "regular", ["all"], 4.6, 1890),
    ("SH-002", "shoes", "Лоферы кожаные", "Old Money Club", 14900, ["black"], ["old_money", "business_casual", "minimal"], ["elegant", "confident"], 3, "regular", ["all"], 4.7, 420),
    ("SH-003", "shoes", "Ботинки челси", "12 STOREEZ", 16900, ["chocolate"], ["minimal", "grunge", "business_casual"], ["confident", "calm"], 2, "regular", ["autumn", "winter"], 4.6, 388),
    ("SH-004", "shoes", "Кроссовки беговые", "Runform", 11900, ["grey"], ["athleisure", "streetwear", "techwear"], ["energetic"], 1, "regular", ["all"], 4.5, 1240),
    ("SH-005", "shoes", "Ботинки на шнуровке", "Street Lab", 12900, ["black"], ["grunge", "streetwear", "techwear"], ["bold", "confident"], 2, "regular", ["autumn", "winter"], 4.4, 610),
    ("SH-006", "shoes", "Балетки", "Atelier No.5", 7990, ["black"], ["romantic", "old_money", "minimal"], ["elegant", "playful"], 2, "regular", ["all"], 4.3, 296),
    ("SH-007", "shoes", "Кеды текстильные", "Street Lab", 3990, ["white"], ["streetwear", "athleisure", "grunge"], ["playful", "energetic"], 1, "regular", ["all"], 4.2, 1420),
    ("SH-008", "shoes", "Ботильоны на каблуке", "Atelier No.5", 18900, ["black"], ["avantgarde", "business_casual", "old_money"], ["elegant", "confident"], 3, "slim", ["autumn", "winter"], 4.5, 178),
    ("SH-009", "shoes", "Сандалии кожаные", "Linen Lab", 5990, ["brown"], ["boho", "minimal"], ["calm", "cozy"], 1, "regular", ["summer"], 4.2, 244),
    ("SH-010", "shoes", "Угги короткие", "Cozy Line", 9990, ["sand"], ["athleisure", "boho"], ["cozy"], 1, "relaxed", ["winter"], 4.1, 320),
    ("SH-011", "shoes", "Кроссовки технологичные", "Techform", 15900, ["charcoal"], ["techwear", "athleisure"], ["confident", "energetic"], 1, "regular", ["all"], 4.4, 210),
    ("SH-012", "shoes", "Туфли-лодочки", "Atelier No.5", 13900, ["burgundy"], ["old_money", "business_casual", "romantic"], ["elegant", "confident"], 3, "slim", ["all"], 4.5, 164),
    ("SH-013", "shoes", "Мокасины замшевые", "Old Money Club", 11900, ["camel"], ["old_money", "minimal"], ["calm", "elegant"], 2, "regular", ["spring", "summer"], 4.4, 132),
    ("SH-014", "shoes", "Сапоги высокие", "12 STOREEZ", 22900, ["black"], ["minimal", "avantgarde", "grunge"], ["mysterious", "confident"], 2, "slim", ["winter", "autumn"], 4.6, 205),
    ("SH-015", "shoes", "Кроссовки базовые", "Runform", 2990, ["black"], ["athleisure", "streetwear"], ["energetic", "cozy"], 1, "regular", ["all"], 4.0, 640),
    # --- bags ----------------------------------------------------------
    ("BG-001", "bag", "Сумка-тоут кожаная", "12 STOREEZ", 16900, ["black"], ["minimal", "business_casual", "old_money"], ["confident", "elegant"], 3, "regular", ["all"], 4.6, 340),
    ("BG-002", "bag", "Кроссбоди мини", "Atelier No.5", 9990, ["beige"], ["minimal", "romantic", "old_money"], ["elegant", "playful"], 2, "regular", ["all"], 4.5, 288),
    ("BG-003", "bag", "Рюкзак городской", "Techform", 8990, ["charcoal"], ["techwear", "streetwear", "athleisure"], ["energetic", "confident"], 1, "regular", ["all"], 4.4, 520),
    ("BG-004", "bag", "Сумка плетёная", "Linen Lab", 5990, ["sand"], ["boho", "romantic"], ["cozy", "playful"], 1, "regular", ["summer"], 4.3, 176),
    ("BG-005", "bag", "Шоппер нейлоновый", "Uniqlo", 2990, ["olive"], ["minimal", "athleisure", "streetwear"], ["cozy", "energetic"], 1, "regular", ["all"], 4.2, 940),
    ("BG-006", "bag", "Клатч вечерний", "Atelier No.5", 12900, ["gold"], ["old_money", "avantgarde"], ["elegant", "bold"], 4, "regular", ["all"], 4.4, 96),
    ("BG-007", "bag", "Сумка хобо", "12 STOREEZ", 19900, ["chocolate"], ["old_money", "minimal", "boho"], ["calm", "elegant"], 2, "regular", ["all"], 4.6, 152),
    ("BG-008", "bag", "Поясная сумка", "Street Lab", 3990, ["black"], ["streetwear", "techwear"], ["bold", "energetic"], 1, "regular", ["all"], 4.1, 430),
    ("BG-009", "bag", "Сумка стёганая на цепочке", "Atelier No.5", 24900, ["black"], ["old_money", "avantgarde"], ["elegant", "confident"], 3, "regular", ["all"], 4.7, 88),
    ("BG-010", "bag", "Рюкзак спортивный", "Runform", 4990, ["navy"], ["athleisure", "streetwear"], ["energetic"], 1, "regular", ["all"], 4.3, 380),
    ("BG-011", "bag", "Сумка текстильная", "Street Lab", 1490, ["black"], ["streetwear", "minimal"], ["energetic", "calm"], 1, "regular", ["all"], 4.0, 300),
    # --- accessories ---------------------------------------------------
    ("AC-001", "accessory", "Ремень кожаный", "Old Money Club", 4990, ["brown"], ["old_money", "business_casual", "minimal"], ["elegant", "confident"], 2, "regular", ["all"], 4.5, 260),
    ("AC-002", "accessory", "Шарф кашемировый", "Cashmere Lab", 9990, ["camel"], ["old_money", "minimal"], ["cozy", "elegant"], 2, "regular", ["winter", "autumn"], 4.7, 174),
    ("AC-003", "accessory", "Кепка", "Street Lab", 2490, ["black"], ["streetwear", "athleisure"], ["playful", "energetic"], 1, "regular", ["all"], 4.2, 620),
    ("AC-004", "accessory", "Серьги золотые минимал", "SOKOLOV", 12900, ["gold"], ["minimal", "old_money", "romantic"], ["elegant", "confident"], 3, "regular", ["all"], 4.8, 143),
    ("AC-005", "accessory", "Очки солнцезащитные", "Avant Studio", 7990, ["black"], ["avantgarde", "minimal", "streetwear"], ["bold", "mysterious"], 2, "regular", ["summer", "spring"], 4.3, 210),
    ("AC-006", "accessory", "Цепь серебряная", "SOKOLOV", 6990, ["silver"], ["streetwear", "avantgarde", "grunge"], ["bold", "mysterious"], 2, "regular", ["all"], 4.4, 188),
    ("AC-007", "accessory", "Платок шёлковый", "Silk Route", 5990, ["emerald"], ["old_money", "romantic"], ["elegant", "playful"], 2, "regular", ["all"], 4.5, 132),
    ("AC-008", "accessory", "Часы классические", "SOKOLOV", 18900, ["silver"], ["business_casual", "old_money", "minimal"], ["confident", "elegant"], 3, "regular", ["all"], 4.6, 205),
    ("AC-009", "accessory", "Шапка бини", "Cozy Line", 1990, ["grey"], ["streetwear", "athleisure", "grunge"], ["cozy"], 1, "regular", ["winter"], 4.3, 720),
    ("AC-010", "accessory", "Перчатки кожаные", "12 STOREEZ", 5990, ["black"], ["old_money", "minimal", "business_casual"], ["elegant", "calm"], 2, "regular", ["winter"], 4.5, 96),
    ("AC-011", "accessory", "Носки набор 3 пары", "Cozy Line", 790, ["white", "grey"], ["athleisure", "streetwear"], ["cozy"], 1, "regular", ["all"], 4.0, 210),
]

#: Дополнительные стилевые теги для позиций базового каталога: TikTok/Pinterest
#: 2026 носятся с существующими базовыми вещами, поэтому трендовые эстетики
#: добавлены к подходящим SKU без дублирования товаров.
EXTRA_STYLES: dict[str, tuple[str, ...]] = {
    # office_siren — острая офисная классика
    "OW-007": ("office_siren",),
    "TP-002": ("office_siren",),
    "TP-003": ("office_siren",),
    "BT-001": ("office_siren", "dark_academia"),
    "BT-005": ("office_siren", "balletcore"),
    "SH-002": ("office_siren",),
    "SH-012": ("office_siren",),
    # gorpcore — outdoor в городе
    "OW-008": ("gorpcore",),
    "OW-010": ("gorpcore",),
    "TP-009": ("gorpcore",),
    "BT-008": ("gorpcore",),
    "SH-011": ("gorpcore",),
    "BG-003": ("gorpcore",),
    # y2k — нулевые
    "OW-012": ("y2k",),
    "TP-011": ("y2k",),
    "TP-006": ("y2k",),
    "BT-003": ("y2k",),
    "SH-007": ("y2k", "indie_sleaze"),
    "AC-003": ("y2k",),
    "AC-006": ("y2k", "indie_sleaze"),
    # indie_sleaze — вечериночный винтаж 2010-х
    "OW-004": ("indie_sleaze",),
    "TP-004": ("indie_sleaze",),
    "TP-010": ("indie_sleaze",),
    "BT-009": ("indie_sleaze",),
    "SH-005": ("indie_sleaze",),
    # dark_academia — библиотечная классика
    "OW-001": ("dark_academia",),
    "KN-003": ("dark_academia",),
    "KN-007": ("dark_academia",),
    "SH-013": ("dark_academia",),
    "AC-001": ("dark_academia",),
    # balletcore — мягкость пачки
    "OW-009": ("balletcore",),
    "KN-005": ("balletcore",),
    "SH-006": ("balletcore",),
}

#: Трендовые позиции 2026 (TikTok/Pinterest): office siren / corpcore, gorpcore,
#: Y2K, indie sleaze, dark academia, balletcore.
# (sku, category, name, brand, price, colors, styles, moods, formality, fit, seasons, rating, reviews)
_TREND_ROWS: list[tuple] = [
    # --- office_siren ------------------------------------------------
    ("TP-018", "top", "Блуза с завязками на вороте", "12 STOREEZ", 8990, ["ivory"], ["office_siren", "business_casual", "old_money"], ["elegant", "confident"], 3, "regular", ["all"], 4.5, 160),
    ("BT-016", "bottom", "Юбка-карандаш миди", "Atelier No.5", 9990, ["black"], ["office_siren", "business_casual", "minimal"], ["confident", "elegant"], 3, "slim", ["all"], 4.5, 210),
    ("SH-016", "shoes", "Слингбэки на каблуке", "Atelier No.5", 13900, ["black"], ["office_siren", "old_money", "business_casual"], ["elegant", "confident"], 3, "slim", ["all"], 4.5, 140),
    ("AC-012", "accessory", "Очки «Байонетта»", "Avant Studio", 5990, ["black"], ["office_siren", "y2k"], ["bold", "confident"], 2, "regular", ["all"], 4.3, 190),
    # --- gorpcore ----------------------------------------------------
    ("OW-014", "outerwear", "Флиска техническая", "Techform", 7990, ["olive"], ["gorpcore", "techwear", "athleisure"], ["energetic", "cozy"], 1, "relaxed", ["autumn", "winter", "spring"], 4.4, 320),
    ("BT-017", "bottom", "Брюки парашютные", "Techform", 9490, ["charcoal"], ["gorpcore", "techwear", "streetwear"], ["energetic", "confident"], 1, "relaxed", ["all"], 4.3, 260),
    ("SH-017", "shoes", "Кроссовки трейловые", "Runform", 13900, ["grey"], ["gorpcore", "techwear", "athleisure"], ["energetic"], 1, "regular", ["all"], 4.5, 480),
    ("BG-012", "bag", "Сумка поясная utility", "Techform", 5490, ["black"], ["gorpcore", "techwear", "streetwear"], ["energetic"], 1, "regular", ["all"], 4.2, 150),
    # --- y2k ---------------------------------------------------------
    ("TP-019", "top", "Беби-ти с принтом", "Street Lab", 2290, ["pink"], ["y2k", "streetwear"], ["playful", "bold"], 1, "slim", ["summer", "spring"], 4.1, 340),
    ("BT-018", "bottom", "Джинсы baggy", "Street Lab", 6990, ["blue"], ["y2k", "streetwear"], ["energetic", "playful"], 1, "relaxed", ["all"], 4.3, 520),
    ("BG-013", "bag", "Сумка-багет", "Atelier No.5", 11990, ["silver"], ["y2k", "office_siren"], ["playful", "bold"], 2, "regular", ["all"], 4.4, 150),
    ("SH-018", "shoes", "Кроссовки chunky", "Street Lab", 8990, ["white"], ["y2k", "streetwear", "athleisure"], ["bold", "energetic"], 1, "relaxed", ["all"], 4.3, 610),
    # --- indie_sleaze -------------------------------------------------
    ("OW-015", "outerwear", "Кожаный тренч винтажный", "Avant Studio", 21900, ["black"], ["indie_sleaze", "grunge", "old_money"], ["mysterious", "bold"], 2, "regular", ["autumn", "winter"], 4.4, 86),
    ("TP-020", "top", "Майка-алкоголичка", "Street Lab", 1490, ["white"], ["indie_sleaze", "athleisure", "y2k"], ["energetic", "bold"], 1, "slim", ["summer"], 4.0, 430),
    ("AC-014", "accessory", "Колготки в сетку", "Atelier No.5", 1290, ["black"], ["indie_sleaze", "office_siren", "grunge"], ["bold", "mysterious"], 2, "regular", ["all"], 4.2, 260),
    ("SH-019", "shoes", "Ботинки на платформе", "Street Lab", 14900, ["black"], ["indie_sleaze", "grunge", "avantgarde"], ["bold", "confident"], 2, "regular", ["all"], 4.3, 150),
    # --- dark_academia ------------------------------------------------
    ("OW-016", "outerwear", "Пиджак твидовый", "Old Money Club", 15900, ["brown"], ["dark_academia", "old_money", "business_casual"], ["calm", "elegant"], 2, "regular", ["autumn", "winter"], 4.5, 120),
    ("KN-012", "knitwear", "Жилет аргайл", "Old Money Club", 6490, ["burgundy"], ["dark_academia", "old_money"], ["calm", "playful"], 2, "regular", ["autumn", "winter"], 4.3, 96),
    ("BT-020", "bottom", "Брюки оксфорд с защипами", "Old Money Club", 10900, ["grey"], ["dark_academia", "business_casual", "minimal"], ["confident", "calm"], 2, "regular", ["all"], 4.4, 140),
    ("AC-015", "accessory", "Галстук шерстяной", "Old Money Club", 3990, ["navy"], ["dark_academia", "business_casual"], ["confident", "elegant"], 3, "regular", ["all"], 4.2, 74),
    # --- balletcore ---------------------------------------------------
    ("KN-013", "knitwear", "Кардиган на запах", "Cozy Line", 6990, ["blush"], ["balletcore", "romantic", "minimal"], ["cozy", "playful"], 2, "relaxed", ["all"], 4.4, 210),
    ("BT-021", "bottom", "Юбка миди из тюля", "Atelier No.5", 8990, ["ivory"], ["balletcore", "romantic"], ["playful", "elegant"], 2, "regular", ["spring", "summer", "all"], 4.3, 130),
    ("SH-020", "shoes", "Балетки с лентами", "Atelier No.5", 9990, ["blush"], ["balletcore", "romantic"], ["playful", "elegant"], 2, "regular", ["all"], 4.4, 190),
    ("AC-016", "accessory", "Гетры трикотажные", "Cozy Line", 1990, ["light_grey"], ["balletcore", "athleisure"], ["cozy", "playful"], 1, "regular", ["winter", "autumn"], 4.1, 150),
]

#: Deliberately broken rows — the verification layer must reject these.
_BROKEN_ROWS: list[dict[str, Any]] = [
    {
        "sku": "BAD-001",
        "category": "top",
        "name": "Футболка с подозрительного сайта",
        "brand": "No Name",
        "price_rub": 990,
        "currency": "RUB",
        "url": "http://sketchy-shop.example/item/1",
        "source": "unknown",
        "sizes": ["S", "M"],
        "colors": ["black"],
        "styles": ["streetwear"],
        "moods": ["bold"],
        "seasons": ["all"],
        "rating": 3.0,
        "reviews_count": 2,
    },
    {
        "sku": "BAD-002",
        "category": "shoes",
        "name": "Кроссовки без цены",
        "brand": "No Name",
        "price_rub": 0,
        "currency": "RUB",
        "url": "https://www.lamoda.ru/p/BAD-002",
        "source": "unknown",
        "sizes": ["40"],
        "colors": ["white"],
        "styles": ["streetwear"],
        "moods": ["bold"],
        "seasons": ["all"],
        "rating": 2.5,
        "reviews_count": 1,
    },
    {
        "sku": "BAD-003",
        "category": "bag",
        "name": "Сумка без размеров и атрибутов",
        "brand": "No Name",
        "price_rub": 4500,
        "currency": "RUB",
        "url": "https://www.lamoda.ru/p/BAD-003",
        "source": "unknown",
        "sizes": [],
        "colors": [],
        "styles": [],
        "moods": [],
        "seasons": [],
        "rating": 3.2,
        "reviews_count": 4,
    },
    {
        "sku": "BAD-004",
        "category": "pet_supplies",
        "name": "Лежанка для кота",
        "brand": "No Name",
        "price_rub": 2990,
        "currency": "RUB",
        "url": "https://www.lamoda.ru/p/BAD-004",
        "source": "unknown",
        "sizes": ["one size"],
        "colors": ["grey"],
        "styles": ["minimal"],
        "moods": ["cozy"],
        "seasons": ["all"],
        "rating": 4.0,
        "reviews_count": 10,
    },
]


def _build(row: tuple) -> dict[str, Any]:
    (sku, category, name, brand, price, colors, styles, moods, formality, fit, seasons, rating, reviews) = row
    source_id, base_url = BRAND_SOURCES.get(brand, FALLBACK_SOURCE)
    merged_styles = list(dict.fromkeys(list(styles) + list(EXTRA_STYLES.get(sku, ()))))
    return {
        "sku": sku,
        "category": category,
        "name": name,
        "brand": brand,
        "price_rub": float(price),
        "currency": "RUB",
        "fit": fit,
        "formality": int(formality),
        "colors": list(colors),
        "styles": merged_styles,
        "moods": list(moods),
        "silhouettes": ["all"],
        "seasons": list(seasons),
        "sizes": list(CATEGORY_SIZES.get(category, ONE_SIZE)),
        "materials": [],
        "url": f"{base_url}/p/{sku.lower()}",
        # Фото у локальных позиций нет: живые фото приходят от движка
        # (web-search) в реальном времени; пусто — UI рисует цветной плейсхолдер.
        "image_url": "",
        "source": source_id,
        "gendered": ["feminine"] if sku in FEMININE_ITEMS else [],
        "rating": float(rating),
        "reviews_count": int(reviews),
    }


def seed_products() -> list[dict[str, Any]]:
    """All catalog rows (valid + intentionally broken) as plain dicts."""
    return (
        [_build(row) for row in _ROWS]
        + [_build(row) for row in _TREND_ROWS]
        + [dict(row) for row in _BROKEN_ROWS]
    )


def valid_products() -> list[dict[str, Any]]:
    return [_build(row) for row in _ROWS] + [_build(row) for row in _TREND_ROWS]


def catalog_stats() -> dict[str, int]:
    products = seed_products()
    by_category: dict[str, int] = {}
    for product in products:
        by_category[product["category"]] = by_category.get(product["category"], 0) + 1
    return {"total": len(products), **by_category}
