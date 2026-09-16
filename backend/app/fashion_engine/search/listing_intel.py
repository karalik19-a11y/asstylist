"""Listing Intelligence — отбор конкретного объявления по словам, описанию и фото.

Модуль общий для двух источников реальных вещей:

* ``AvitoSearchProvider`` — живая выдача Авито (HTTP);
* ``AvitoSnapshotProvider`` — снимок выдачи Авито, сохранённый в поставке
  (``app/data/avito_listings.json``), чтобы сервис показывал реальные вещи с
  фото и ссылками даже там, где сеть недоступна или Авито отвечает капчей.

Оба источника приводят объявление к одному виду, а оценивает его этот слой —
поэтому «движок ищет по ключевым словам и выбирает по внешнему виду и описанию»
работает одинаково для живых и закэшированных объявлений.

Что именно измеряется:

* **ключевые слова** — попадания в заголовок (сильнее) и в описание (слабее),
  со стеммингом, поэтому «шерстяное» ≈ «шерсть» ≈ «шерстяной»;
* **описание** — материал, цвет, силуэт, состояние, размер, сезон: чем
  конкретнее объявление, тем выше доверие;
* **внешний вид** — наличие и качество фотографии с CDN Авито, а когда фото
  реально доступно (``app.vision.photo_traits``) — его измеренные признаки:
  доминирующие оттенки, яркость, насыщенность, «студийность» фона. Они
  сравниваются с палитрой пользователя и выбранным образом.

Все функции детерминированы: одинаковый вход → одинаковый порядок объявлений.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .. import lexicon

#: Маркеры подачи объявления (кто носит вещь).
GENDER_MARKERS: dict[str, tuple[str, ...]] = {
    "feminine": ("женск", "девуш", "women", "woman", "female", "wmn"),
    "masculine": ("мужск", "мужчин", "men ", "men's", "male", "man "),
}

#: Состояние вещи → оценка доверия (1 — новая, 0 — сильно б/у).
CONDITION_MARKERS: tuple[tuple[str, float, str], ...] = (
    ("новое с биркой", 1.0, "новое с биркой"),
    ("новое", 0.96, "новое"),
    ("идеальн", 0.92, "идеальное"),
    ("отличн", 0.88, "отличное"),
    ("хорош", 0.78, "хорошее"),
    ("ношен", 0.55, "ношеное"),
    ("б/у", 0.5, "б/у"),
    ("есть дефект", 0.3, "с дефектом"),
)

#: Слова стиля в объявлении → id стиля приложения (подсказка вкуса).
STYLE_MARKERS: dict[str, tuple[str, ...]] = {
    "minimal": ("минимал", "базов", "монохром", "лаконич", "minimal"),
    "old_money": ("кашемир", "кэмел", "классик", "лофер", "tweed", "твид"),
    "streetwear": ("оверсайз", "стрит", "худи", "сникер", "oversize", "streetwear"),
    "business_casual": ("пиджак", "блейзер", "брюки со стрелк", "рубашка", "tailored"),
    "techwear": ("техно", "мембран", "утеплител", "карго", "nylon", "нейлон"),
    "romantic": ("кружев", "шифон", "атлас", "летящ", "бант", "оборк"),
    "athleisure": ("спортив", "тренировоч", "флис", "sport"),
    "grunge": ("гранж", "потёрт", "потерт", "кожан", "рок", "винтаж"),
    "boho": ("лён", "льнян", "этно", "бахром", "вязан"),
    "avantgarde": ("асимметр", "деконструк", "архитектур", "авангард", "oversize volume"),
    "office_siren": ("притален", "офисн", "юбка-карандаш", "корпоратив"),
    "gorpcore": ("гортекс", "треккинг", "аутдор", "функциональн", "флис"),
    "y2k": ("y2k", "багги", "джинсы низкой посадки", "металлик"),
    "indie_sleaze": ("инди", "клубн", "кожан", "скинни", "винтаж"),
    "dark_academia": ("твид", "шерст", "оксфорд", "колледж", "гранж академия"),
    "balletcore": ("балет", "трикотаж", "обёрт", "пачка", "ribbon"),
}

#: Сезонные слова в объявлении.
SEASON_MARKERS: dict[str, tuple[str, ...]] = {
    "winter": ("зимн", "пухов", "утепл", "шерст", "мех", "тёпл", "тепл"),
    "summer": ("летн", "лёгк", "легк", "хлопок", "лён", "льнян", "шифон"),
    "spring": ("демисезон", "ветровк", "тренч", "плащ"),
    "autumn": ("демисезон", "шерст", "твид", "пальто"),
}

_SIZE_TOKEN_RE = re.compile(r"\b(XXS|XS|S|M|L|XL|XXL|XXXL|ONE\s?SIZE)\b", re.IGNORECASE)
_SIZE_NUM_RE = re.compile(r"\b(3[4-9]|4[0-9]|5[0-8])\b")
_SIZE_FOOTWEAR_RE = re.compile(r"\b(3[5-9]|4[0-6])\b")
_IMG_SIZE_RE = re.compile(r"(\d{3,4})x(\d{3,4})")
_WORDS_RE = re.compile(r"[a-zа-яё0-9']{3,}", re.IGNORECASE)


@dataclass
class ListingTraits:
    """Разбор объявления: что за вещь, из чего, какого оттенка и в каком состоянии."""

    colors: list[str] = field(default_factory=list)
    materials: list[str] = field(default_factory=list)
    silhouettes: list[str] = field(default_factory=list)
    aesthetics: list[str] = field(default_factory=list)
    garments: list[str] = field(default_factory=list)
    style_hint: str | None = None
    season_hint: str | None = None
    gendered: str = "unisex"
    condition: str | None = None
    condition_score: float = 0.6
    size_tokens: list[str] = field(default_factory=list)
    photo_quality: float = 0.0
    photo_traits: dict[str, Any] = field(default_factory=dict)
    text_richness: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "colors": list(self.colors),
            "materials": list(self.materials),
            "silhouettes": list(self.silhouettes),
            "aesthetics": list(self.aesthetics),
            "garments": list(self.garments),
            "style_hint": self.style_hint,
            "season_hint": self.season_hint,
            "gendered": self.gendered,
            "condition": self.condition,
            "condition_score": round(self.condition_score, 3),
            "sizes": list(self.size_tokens),
            "photo_quality": round(self.photo_quality, 3),
            "photo_traits": dict(self.photo_traits),
            "text_richness": round(self.text_richness, 3),
        }


@dataclass
class AppearanceMatch:
    """Насколько объявление подходит конкретному запросу и человеку."""

    score: float = 0.0
    components: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "components": {key: round(value, 4) for key, value in self.components.items()},
            "notes": list(self.notes),
        }


# ─── разбор объявления ───────────────────────────────────────────────────────


def _first_marker(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def photo_quality(url: str) -> float:
    """Качество снимка по ссылке: CDN Авито, размеры, число кадров в галерее."""
    if not url:
        return 0.0
    score = 10.0
    lowered = url.lower()
    if "img.avito.st" in lowered:
        score += 4.0
    match = _IMG_SIZE_RE.search(lowered)
    if match:
        width = int(match.group(1))
        score += 6.0 if width >= 640 else 4.0 if width >= 320 else 2.0
    if "cqp=" in lowered or "width=" in lowered:
        score += 2.0
    return score


def analyze_listing(
    title: str,
    description: str = "",
    params: str = "",
    image: str = "",
    *,
    photo_traits: dict[str, Any] | None = None,
) -> ListingTraits:
    """Разобрать объявление: цвета, материалы, силуэт, состояние, подача, фото."""
    text = " ".join(part for part in (title, params, description) if part).strip()
    lowered = text.lower().replace("ё", "е")
    traits = ListingTraits()

    traits.garments = lexicon.detect_terms(text, ("garment",))
    traits.materials = lexicon.detect_terms(text, ("material",))
    traits.silhouettes = lexicon.detect_terms(text, ("silhouette",))
    traits.aesthetics = lexicon.detect_terms(text, ("aesthetic",))
    traits.colors = lexicon.detect_colors(text)

    # Фото: измеренные признаки (если удалось скачать) важнее эвристики по URL.
    traits.photo_traits = dict(photo_traits or {})
    traits.photo_quality = photo_quality(image)
    if traits.photo_traits:
        traits.photo_quality += 6.0
        for color in traits.photo_traits.get("colors") or []:
            if color not in traits.colors:
                traits.colors.append(color)

    for style_id, markers in STYLE_MARKERS.items():
        if _first_marker(lowered, markers):
            traits.style_hint = style_id
            break
    for season_id, markers in SEASON_MARKERS.items():
        if _first_marker(lowered, markers):
            traits.season_hint = season_id
            break

    feminine = _first_marker(lowered, GENDER_MARKERS["feminine"])
    masculine = _first_marker(lowered, GENDER_MARKERS["masculine"])
    traits.gendered = "feminine" if feminine and not masculine else "masculine" if masculine and not feminine else "unisex"

    for marker, score, label in CONDITION_MARKERS:
        if marker in lowered:
            traits.condition = label
            traits.condition_score = score
            break

    sizes: list[str] = []
    for token in _SIZE_TOKEN_RE.findall(text):
        normalized = token.upper().replace(" ", "")
        if normalized not in sizes:
            sizes.append(normalized)
    clothing = any(word in lowered for word in ("пальто", "куртк", "брюк", "джинс", "плать", "юбк", "свитер", "рубаш"))
    numeric_re = _SIZE_TOKEN_RE
    numbers = _SIZE_NUM_RE.findall(text) if not clothing or sizes else []
    for number in numbers:
        if number not in sizes:
            sizes.append(number)
    traits.size_tokens = sizes[:6]
    _ = numeric_re

    # Насыщенность описания: материалы, цвета, размер, состояние, детали кроя.
    richness = min(6.0, 1.2 * len(traits.materials) + 1.0 * len(traits.colors) + 0.8 * len(traits.silhouettes))
    if traits.size_tokens:
        richness += 1.0
    if traits.condition:
        richness += 1.0
    if len(description) >= 60:
        richness += 1.5
    traits.text_richness = round(richness, 3)
    return traits


# ─── сопоставление с запросом ────────────────────────────────────────────────


def query_match(ru_query: str, query_tokens: list[str], title: str, description: str) -> tuple[float, list[str]]:
    """Попадание запроса в заголовок/описание объявления (со стеммингом)."""
    title_stems = set(lexicon.tokenize(title))
    desc_stems = set(lexicon.tokenize(description)) if description else set()
    score = 0.0
    hits: list[str] = []
    for token in query_tokens:
        if token in title_stems:
            score += 14.0
            hits.append(token)
        elif any(lexicon.matches_token(token, other) for other in title_stems):
            score += 10.0
            hits.append(token)
        elif token in desc_stems or any(lexicon.matches_token(token, other) for other in desc_stems):
            score += 6.0
    lowered_query = (ru_query or "").lower()
    for word in _WORDS_RE.findall(title.lower()):
        if len(word) >= 4 and word in lowered_query:
            score += 4.0
    return score, list(dict.fromkeys(hits))[:6]


def appearance_match(
    traits: ListingTraits,
    *,
    preferred_colors: list[str] | None = None,
    avoid_colors: list[str] | None = None,
    silhouette_preference: str | None = None,
    style: str | None = None,
    season: str | None = None,
    presentation: str = "unisex",
    budget: float = 0.0,
    price: float = 0.0,
    size: str | None = None,
) -> AppearanceMatch:
    """Оценка «подходит ли вещь человеку» по внешнему виду и описанию.

    Возвращает 0…1 и разбор по слагаемым — его показывают в интерфейсе, чтобы
    у выбора была причина, а не «AI так решил».
    """
    preferred = set(preferred_colors or [])
    avoid = set(avoid_colors or [])
    components: dict[str, float] = {}
    notes: list[str] = []

    # Цвет: любимые оттенки — плюс, исключённые — минус.
    palette_hits = [color for color in traits.colors if color in preferred]
    palette_misses = [color for color in traits.colors if color in avoid]
    if traits.colors:
        color_score = 0.6
        color_score += 0.25 if palette_hits else 0.0
        color_score -= 0.5 * len(palette_misses)
        components["color"] = max(0.0, min(1.0, color_score))
        if palette_hits:
            notes.append(f"оттенок из вашей палитры ({', '.join(palette_hits[:2])})")
        elif traits.colors:
            notes.append(f"оттенок {traits.colors[0]} — нейтрально к палитре")
    else:
        components["color"] = 0.55

    # Материал и силуэт — то, что реально видно в описании объявления.
    components["material"] = min(1.0, 0.45 + 0.18 * len(traits.materials))
    if traits.materials:
        notes.append(f"фактура: {', '.join(traits.materials[:2])}")
    silhouette_score = 0.5
    if silhouette_preference and silhouette_preference in traits.silhouettes:
        silhouette_score = 0.95
    elif traits.silhouettes:
        silhouette_score = 0.78
    components["silhouette"] = silhouette_score
    if traits.silhouettes:
        notes.append(f"силуэт: {', '.join(traits.silhouettes[:2])}")

    # Стиль и сезон по словам объявления.
    components["style"] = 0.9 if (style and traits.style_hint == style) else 0.6 if traits.style_hint else 0.5
    if style and traits.style_hint == style:
        notes.append("попадает в выбранное направление")
    components["season"] = 0.85 if (season in (None, "all") or not traits.season_hint) else (
        0.95 if traits.season_hint == season else 0.45
    )

    # Подача: женское объявление для feminine-запроса и наоборот.
    if presentation in ("feminine", "masculine") and traits.gendered != "unisex":
        components["presentation"] = 1.0 if traits.gendered == presentation else 0.25
    else:
        components["presentation"] = 0.8

    # Размер: если человек указал размер, а он виден в объявлении.
    if size:
        normalized = str(size).strip().upper()
        components["size"] = 1.0 if normalized in {token.upper() for token in traits.size_tokens} else 0.6
    else:
        components["size"] = 0.75

    # Состояние и «живость» объявления.
    components["condition"] = traits.condition_score
    components["photo"] = min(1.0, traits.photo_quality / 22.0)
    components["description"] = min(1.0, traits.text_richness / 10.0)

    # Бюджет: вещь дешевле лимита — плюс, дороже — минус (жёсткий фильтр выше).
    if budget > 0 and price > 0:
        components["budget"] = 1.0 if price <= budget else max(0.0, 1.0 - (price - budget) / max(budget, 1.0))
    else:
        components["budget"] = 0.7

    weights = {
        "color": 0.17,
        "material": 0.10,
        "silhouette": 0.13,
        "style": 0.13,
        "season": 0.06,
        "presentation": 0.11,
        "size": 0.06,
        "condition": 0.08,
        "photo": 0.09,
        "description": 0.04,
        "budget": 0.03,
    }
    total = sum(components.get(key, 0.0) * weight for key, weight in weights.items())
    if palette_misses and len(palette_misses) >= max(1, len(traits.colors)):
        total *= 0.6
        notes.append("оттенок исключён из подбора")
    return AppearanceMatch(score=round(total, 4), components=components, notes=notes[:4])


def size_hint(text: str) -> list[str]:
    """Размеры, которые видны в заголовке/описании объявления."""
    return analyze_listing(text).size_tokens


def looks_like_listing_url(url: str) -> bool:
    """Ссылка ведёт на конкретное объявление, а не на поиск по разделу."""
    if not url:
        return False
    path = url.split("?", 1)[0]
    return bool(re.search(r"_\d{6,}$", path))


__all__ = [
    "AppearanceMatch",
    "ListingTraits",
    "analyze_listing",
    "appearance_match",
    "looks_like_listing_url",
    "photo_quality",
    "query_match",
    "size_hint",
]
