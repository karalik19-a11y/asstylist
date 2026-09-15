"""Таблицы ключевых слов (порт из ``FashionIntelligence.js``/``TrendEngine.js``).

Английские наборы перенесены из оригинала один-в-один; к каждому добавлены
русские основы (``RU_*``), чтобы движок понимал каталог и запросы asStylist.
"""

from __future__ import annotations

from . import lexicon

SILHOUETTE_KEYWORDS: dict[str, list[str]] = {
    "oversized": ["oversized", "boxy", "voluminous", "dropped shoulder", "cocoon", "оверсайз", "объемн"],
    "fitted": ["fitted", "slim", "tailored", "bodycon", "skinny", "притал", "облегающ", "узк"],
    "relaxed": ["relaxed", "loose", "easy", "soft", "свободн"],
    "structured": ["structured", "architectural", "sculptural", "sharp", "структур", "архитектур"],
    "deconstructed": ["deconstructed", "asymmetric", "raw edge", "unfinished", "distressed", "деконстру", "асимметр", "потерт"],
    "elongated": ["longline", "elongated", "maxi", "floor length", "удлинен", "макси"],
    "cropped": ["cropped", "crop", "short", "коротк", "кроп", "мини"],
    "voluminous": ["voluminous", "volume", "объемн", "ярусн"],
}

MATERIAL_KEYWORDS: dict[str, list[str]] = {
    "sheer": ["sheer", "transparent", "translucent", "mesh", "voile", "organza", "chiffon", "прозрач", "полупрозрач", "сетк", "шифон", "органз"],
    "heavy": ["wool", "leather", "denim", "canvas", "tweed", "felt", "шерст", "кож", "деним", "джинс", "замш", "драп"],
    "fluid": ["silk", "viscose", "cupro", "satin", "crepe", "jersey", "шелк", "вискоз", "атлас", "креп"],
    "technical": ["nylon", "gore-tex", "ripstop", "technical", "performance", "нейлон", "мембран", "технолог", "полиэстер"],
    "textured": ["boucle", "tweed", "cable", "ribbed", "quilted", "padded", "мохер", "стеган", "вязан", "велюр", "бархат", "кружев"],
}

AESTHETIC_MAP: dict[str, list[str]] = {
    "industrial": ["industrial", "utilitarian", "workwear", "carpenter", "military", "индустриальн", "утилитарн", "милитари"],
    "romantic": ["romantic", "sheer", "lace", "ruffle", "delicate", "soft", "романтичн", "кружев", "воланами"],
    "gothic": ["gothic", "dark", "black", "velvet", "corset", "victorian", "готич", "бархат", "темн"],
    "minimal": ["minimal", "clean", "precise", "architectural", "quiet luxury", "минимал", "строг", "базов"],
    "archive": ["archive", "vintage", "90s", "00s", "deadstock", "rare", "архив", "винтаж"],
    "avantgarde": ["avant-garde", "experimental", "conceptual", "sculptural", "авангард", "экспериментальн", "деконстру"],
    "street": ["street", "streetwear", "urban", "skate", "hype", "уличн", "стрит"],
    "editorial": ["editorial", "runway", "high fashion", "couture", "эдиториал", "вечерн"],
}

COLOR_KEYWORDS: tuple[str, ...] = (
    "black", "white", "ivory", "grey", "gray", "navy", "beige", "brown", "olive", "burgundy",
    "red", "blue", "green", "pink", "purple", "silver", "gold", "transparent", "sheer",
)

COOL_COLORS = ("black", "white", "grey", "gray", "navy", "blue", "silver", "purple")
WARM_COLORS = ("beige", "brown", "olive", "burgundy", "red", "gold", "ivory")

DESIGNER_LANGUAGE: dict[str, str] = {
    "rick owens": "dark, elongated, architectural",
    "yohji yamamoto": "deconstructed, black, oversized",
    "comme des garcons": "conceptual, volume, anti-fashion",
    "maison margiela": "deconstructed, artisanal, anonymity",
    "balenciaga": "exaggerated, volume, street-luxury",
    "prada": "ugly-chic, nylon, intellectual",
    "helmut lang": "minimal, precise, modern",
    "lemaire": "quiet luxury, generous volume, natural fibres",
    "jil sander": "purist, precise, minimal",
    "12 storeez": "quiet luxury, clean tailoring",
    "uniqlo": "functional basics, japanese simplicity",
}

PRESTIGE_BRANDS: tuple[str, ...] = (
    "rick owens", "ann demeulemeester", "yohji", "margiela", "comme des garcons",
    "helmut lang", "julius", "lemaire", "undercover", "balenciaga", "jil sander",
    "issey miyake", "prada", "acne studios",
)

MASS_MARKET_BRANDS: tuple[str, ...] = (
    "zara", "h&m", "hm", "uniqlo", "mango", "asos", "shein", "primark", "gap",
    "old navy", "bershka", "pull&bear", "wildberries", "lamoda basic",
)

#: Актуальные направления из ``TrendEngine`` (оригинальный набор).
EMERGING_AESTHETICS: tuple[tuple[str, float, str], ...] = (
    ("industrial romanticism", 0.82, "interesting"),
    ("deconstructed 90s minimalism", 0.78, "interesting"),
    ("neo-gothic editorial", 0.75, "interesting"),
    ("post-punk archive", 0.80, "interesting"),
    ("quiet luxury", 0.70, "popular"),
    ("gorpcore", 0.65, "popular"),
    ("balletcore", 0.55, "popular"),
    ("transparent layering", 0.88, "interesting"),
    ("exaggerated volume", 0.77, "interesting"),
    ("archive revival", 0.85, "interesting"),
)

RISING_SILHOUETTES: tuple[str, ...] = (
    "oversized blazer", "sheer long sleeve", "barrel pant", "longline coat",
    "deconstructed shirt", "asymmetric top", "wide leg trouser",
)

RECURRING_MATERIALS: tuple[str, ...] = (
    "sheer viscose", "mesh", "washed leather", "technical nylon", "heavy wool", "cupro",
)

#: Тезисы, которые умеет предлагать TrendEngine (для перевода в UI).
THESIS_LABELS_RU: dict[str, str] = {
    # тезисы стилей asStylist (см. TrendEngine._THESIS_TRIGGERS)
    "Quiet Luxury Tailoring": "Тихая роскошь и точный крой",
    "Minimal Precision": "Точный минимализм",
    "Technical Utility": "Техничный утилитаризм",
    "Soft Romanticism": "Мягкая романтика",
    "Craft Bohemia": "Ремесленное бохо",
    "Sport Couture": "Спортивный кутюр",
    "Sharp Tailoring": "Строгий городской крой",
    # тезисы оригинала
    "Industrial Romanticism": "Индустриальная романтика",
    "Transparent Layering": "Прозрачные слои",
    "Deconstructed 90s Minimalism": "Деконструированный минимализм 90-х",
    "Post-Structural Tailoring": "Постструктурный крой",
    "Neo-Gothic Editorial": "Неоготический эдиториал",
    "Post-Punk Archive": "Пост-панк архив",
    "Archive Revival": "Возрождение архива",
    "Exaggerated Volume": "Гипертрофированный объём",
    "Contemporary Editorial": "Современный эдиториал",
    "Refined Utilitarian": "Утончённый утилитаризм",
}


def thesis_label_ru(thesis: str | None) -> str:
    if not thesis:
        return ""
    return THESIS_LABELS_RU.get(thesis, thesis)


def keyword_hit(text: str, tokens: list[str], keyword: str) -> bool:
    """Проверка одного ключевого слова: подстрока для EN, основы — для RU."""
    lowered = keyword.lower().replace("ё", "е")
    if lowered and lowered in text:
        return True
    if any("а" <= char <= "я" for char in lowered):
        key = lexicon.stem_ru(lowered)
        return any(lexicon.matches_token(token, key) for token in tokens)
    return False


def any_keyword(text: str, tokens: list[str], keywords: list[str]) -> bool:
    return any(keyword_hit(text, tokens, keyword) for keyword in keywords)
