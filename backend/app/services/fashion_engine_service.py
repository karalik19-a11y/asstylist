"""ASSTYLIST Fashion Engine в контуре asStylist.

Здесь движок из репозитория ``karalik19-a11y/-`` (Python-порт в
``app/fashion_engine``) подключается к приложению:

* поиск и подбор вещей идут **только на Авито**: каждая позиция — живое
  объявление со ссылкой, фотографией и ценой в рублях
  (``AvitoSearchProvider``);
* движок подбирает вещи по ключевым словам, названиям, анализу фото и
  описания, затем выполняет отбор: расширение запроса,
  Fashion Intelligence, Taste/anti-generic, архитектура образа
  (hero/base/layer/footwear/accessory), оценка совместимости и критик;
* приложение остаётся страховкой: жёсткий бюджет (бюджетный оптимизатор
  доводит образ до лимита), обязательные слоты плана, слой верификации;
* если Авито временно недоступен, движок всё равно подбирает вещи, а ссылки
  ведут на соответствующие подборки Авито — пустых выдач не бывает.

Итоговый индекс образа — смесь оценки приложения и оценки движка
(``FASHION_ENGINE_SCORE_WEIGHT``), обе цифры показываются в UI.
"""

from __future__ import annotations

import json
import re
import zlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from ..catalog.products import CATEGORY_SIZES
from ..config import settings
from ..engine.body import BodyProfile
from ..engine.budget import build_look
from ..engine.colors import COLORS
from ..engine.explain import item_reasons, look_summary, look_tips, personal_note
from ..engine.look_builder import (
    LookGenerationError,
    LookRequest,
    LookResult,
    PreparedPool,
    generate_look as legacy_generate_look,
    prepare_pool,
)
from ..engine.options import SLOT_CATEGORIES, SLOT_LABELS, SLOT_PLANS, mood_by_id, style_by_id
from ..engine.options import plan_for_season as _plan_for_season
from ..engine.palette import PaletteProfile
from ..engine.ranking import (
    CatalogItem,
    RankingContext,
    ScoredItem,
    look_cohesion,
    look_score,
    score_item,
    style_verdict,
)
from ..fashion_engine import (
    AvitoSearchProvider,
    CatalogSearchProvider,
    EngineOptions,
    FashionEngine,
    MockRealProductProvider,
    ProductItem,
    UserStyleProfile,
    WebSearchProvider,
    avito_search_url,
    lexicon,
)
from ..fashion_engine import keywords as engine_keywords
from ..fashion_engine.search.listing_intel import (
    analyze_listing,
    appearance_match,
    looks_like_listing_url,
)
from ..fashion_engine.search.multi_pass_search import DiscoveryResult
from ..fashion_engine.search.provider import SearchContext
from ..fashion_engine.search.providers.avito_provider import _extract_brand
from ..fashion_engine.search.providers.avito_snapshot_provider import AvitoSnapshotProvider
from ..fashion_engine.types import OutfitResult
from ..vision import photo_traits as photo_traits_module

PIPELINE = "asstylist-fashion-engine"

#: Тир бренда: влияет на подсказки движку (нишевые позиции при высоком niche).
BRAND_TIERS: dict[str, str] = {
    "12 storeez": "designer",
    "atelier no.5": "designer",
    "cashmere lab": "designer",
    "silk route": "designer",
    "avant studio": "designer",
    "old money club": "designer",
    "techform": "designer",
    "lamoda select": "designer",
    "street lab": "contemporary",
    "runform": "contemporary",
    "cozy line": "contemporary",
    "linen lab": "contemporary",
    "sokolov": "contemporary",
    "uniqlo": "mass",
    "uniqlo sport": "mass",
}
DEFAULT_TIER = "contemporary"

#: Насколько вещь из образа движка приоритетнее прочих кандидатов слота.
ENGINE_OUTFIT_BONUS = 0.25

#: Категория приложения → категория движка (если по названию не определить).
APP_CATEGORY_TO_ENGINE: dict[str, str] = {
    "outerwear": "jacket",
    "top": "top",
    "knitwear": "cardigan",
    "bottom": "trousers",
    "dress": "dress",
    "shoes": "shoes",
    "bag": "bag",
    "accessory": "accessory",
}

#: Категория движка → слот приложения.
ENGINE_CATEGORY_TO_SLOT: dict[str, str] = {
    "coat": "outerwear",
    "trench": "outerwear",
    "jacket": "outerwear",
    "blazer": "outerwear",
    "parka": "outerwear",
    "puffer": "outerwear",
    "top": "top",
    "shirt": "top",
    "blouse": "top",
    "knit": "top",
    "sweater": "top",
    "cardigan": "top",
    "vest": "top",
    "trousers": "bottom",
    "jeans": "bottom",
    "skirt": "bottom",
    "shorts": "bottom",
    "dress": "dress",
    "jumpsuit": "dress",
    "boots": "shoes",
    "sneakers": "shoes",
    "shoes": "shoes",
    "bag": "bag",
    "backpack": "bag",
    "tote": "bag",
    "clutch": "bag",
    "crossbody": "bag",
    "accessory": "accessory",
    "belt": "accessory",
    "scarf": "accessory",
    "cap": "accessory",
    "beanie": "accessory",
    "gloves": "accessory",
    "sunglasses": "accessory",
    "earrings": "accessory",
    "chain": "accessory",
    "watch": "accessory",
    "socks": "accessory",
    "tie": "accessory",
}

#: Цвет приложения → слово движка.
APP_COLOR_TO_ENGINE: dict[str, str] = {
    "black": "black",
    "charcoal": "grey",
    "grey": "grey",
    "light_grey": "grey",
    "white": "white",
    "ivory": "ivory",
    "beige": "beige",
    "sand": "beige",
    "camel": "beige",
    "brown": "brown",
    "chocolate": "brown",
    "terracotta": "brown",
    "burgundy": "burgundy",
    "red": "red",
    "coral": "red",
    "pink": "pink",
    "blush": "pink",
    "lavender": "purple",
    "violet": "purple",
    "blue": "blue",
    "navy": "navy",
    "sky": "blue",
    "teal": "green",
    "emerald": "green",
    "olive": "olive",
    "khaki": "olive",
    "green": "green",
    "mustard": "gold",
    "yellow": "gold",
    "orange": "red",
    "silver": "silver",
    "gold": "gold",
}

#: Стиль приложения → профиль движка (ниша, эстетики, ключевые слова запроса).
STYLE_ENGINE: dict[str, dict[str, Any]] = {
    "minimal": {
        "niche": 52,
        "aesthetics": ["minimal"],
        "keywords": "minimal clean precise quiet luxury monochrome",
    },
    "old_money": {
        "niche": 62,
        "aesthetics": ["minimal", "archive"],
        "keywords": "quiet luxury camel cashmere tailored classic loafers",
    },
    "streetwear": {
        "niche": 66,
        "aesthetics": ["street"],
        "keywords": "streetwear urban oversized denim sneakers skate",
    },
    "business_casual": {
        "niche": 55,
        "aesthetics": ["minimal"],
        "keywords": "tailored business blazer shirt trousers precise",
    },
    "techwear": {
        "niche": 78,
        "aesthetics": ["avantgarde", "industrial"],
        "keywords": "technical nylon utilitarian functional dark layering",
    },
    "romantic": {
        "niche": 62,
        "aesthetics": ["romantic"],
        "keywords": "romantic sheer ruffle delicate silk pastel flowy",
    },
    "athleisure": {
        "niche": 50,
        "aesthetics": ["street"],
        "keywords": "athleisure performance sporty knit comfortable",
    },
    "grunge": {
        "niche": 74,
        "aesthetics": ["gothic", "archive"],
        "keywords": "grunge distressed denim leather raw 90s combat boots",
    },
    "boho": {
        "niche": 60,
        "aesthetics": ["romantic"],
        "keywords": "boho natural linen earthy flowy textured",
    },
    "avantgarde": {
        "niche": 85,
        "aesthetics": ["avantgarde", "gothic"],
        "keywords": "avant garde deconstructed asymmetric architectural black sculptural",
    },
    # --- актуальные эстетики TikTok/Pinterest (2026) -------------------
    "office_siren": {
        "niche": 64,
        "aesthetics": ["minimal"],
        "keywords": "corpcore tailored blazer pencil skirt sharp office slingback polished",
    },
    "gorpcore": {
        "niche": 74,
        "aesthetics": ["industrial", "street"],
        "keywords": "gorpcore outdoor technical fleece utility trail functional",
    },
    "y2k": {
        "niche": 68,
        "aesthetics": ["street"],
        "keywords": "y2k baggy denim baby tee metallic playful 2000s",
    },
    "indie_sleaze": {
        "niche": 78,
        "aesthetics": ["archive", "gothic"],
        "keywords": "indie sleaze vintage flash party leather skinny messy",
    },
    "dark_academia": {
        "niche": 70,
        "aesthetics": ["archive", "romantic"],
        "keywords": "dark academia tweed oxford wool collegiate classic",
    },
    "balletcore": {
        "niche": 62,
        "aesthetics": ["romantic"],
        "keywords": "balletcore wrap cardigan tulle delicate ribbons soft",
    },
}

MOOD_ENGINE: dict[str, str] = {
    "confident": "confident strong sharp",
    "calm": "calm soft quiet",
    "playful": "playful light colour",
    "bold": "bold statement graphic",
    "cozy": "cozy soft warm knit",
    "elegant": "elegant refined silk cashmere",
    "energetic": "energetic sporty dynamic",
    "mysterious": "mysterious dark black",
}

OCCASION_ENGINE: dict[str, str] = {
    "everyday": "everyday casual",
    "work": "work tailoring office",
    "date": "date romantic evening",
    "party": "night party statement",
    "travel": "travel comfortable practical",
    "event": "editorial evening occasion",
}

SEASON_ENGINE: dict[str, str] = {
    "all": "all season layering",
    "spring": "spring transitional light",
    "summer": "summer lightweight breathable",
    "autumn": "autumn layering wool",
    "winter": "winter wool warm heavy",
}

FIT_ENGINE: dict[str, str] = {
    "slim": "slim",
    "regular": "regular",
    "relaxed": "relaxed",
    "oversize": "oversized",
}

#: Подсказки для query при замене вещи в конкретном слоте.
SLOT_QUERY_HINTS: dict[str, str] = {
    "outerwear": "coat jacket outerwear layer",
    "top": "top shirt knit sweater",
    "bottom": "trousers jeans skirt bottom",
    "dress": "dress",
    "shoes": "boots shoes sneakers footwear",
    "bag": "bag tote crossbody",
    "accessory": "belt scarf accessory",
}

# ─── Авито: единственный источник товаров ────────────────────────────────────

#: Категория движка → категория приложения (обратное к ENGINE_CATEGORY_TO_SLOT).
ENGINE_TO_APP_CATEGORY: dict[str, str] = {
    "coat": "outerwear", "trench": "outerwear", "jacket": "outerwear",
    "blazer": "outerwear", "parka": "outerwear", "puffer": "outerwear",
    "top": "top", "shirt": "top", "blouse": "top", "vest": "top",
    "knit": "knitwear", "sweater": "knitwear", "cardigan": "knitwear",
    "trousers": "bottom", "jeans": "bottom", "skirt": "bottom",
    "shorts": "bottom", "pants": "bottom", "leggings": "bottom",
    "dress": "dress", "jumpsuit": "dress",
    "boots": "shoes", "sneakers": "shoes", "shoes": "shoes",
    "bag": "bag", "backpack": "bag", "tote": "bag", "clutch": "bag",
    "crossbody": "bag",
    "accessory": "accessory", "belt": "accessory", "scarf": "accessory",
    "cap": "accessory", "beanie": "accessory", "gloves": "accessory",
    "sunglasses": "accessory", "earrings": "accessory", "chain": "accessory",
    "watch": "accessory", "socks": "accessory", "tie": "accessory",
}

#: Слово движка → цвет приложения (первый подходящий id).
ENGINE_TO_APP_COLOR: dict[str, str] = {}
for _app_color, _engine_word in APP_COLOR_TO_ENGINE.items():
    ENGINE_TO_APP_COLOR.setdefault(_engine_word, _app_color)
del _app_color, _engine_word

#: Категории движка, допустимые в каждом слоте при живом поиске.
SLOT_ENGINE_CATEGORIES: dict[str, list[str]] = {}
for _engine_cat, _slot in ENGINE_CATEGORY_TO_SLOT.items():
    SLOT_ENGINE_CATEGORIES.setdefault(_slot, []).append(_engine_cat)
del _engine_cat, _slot

#: Русские существительные слотов для запросов к Авито.
RU_SLOT_NOUNS: dict[str, str] = {
    "outerwear": "пальто",
    "top": "свитер",
    "bottom": "брюки",
    "dress": "платье",
    "shoes": "ботинки",
    "bag": "сумка",
    "accessory": "шарф",
}

#: Стиль → русские определения для запроса к Авито.
STYLE_RU_ADJ: dict[str, str] = {
    "minimal": "базовый",
    "old_money": "кашемир классический",
    "streetwear": "оверсайз",
    "business_casual": "классический",
    "techwear": "технический",
    "romantic": "кружевной",
    "athleisure": "спортивный",
    "grunge": "кожаный потертый",
    "boho": "льняной",
    "avantgarde": "асимметричный",
    "office_siren": "приталенный",
    "gorpcore": "флис",
    "y2k": "джинсовый",
    "indie_sleaze": "винтажный кожаный",
    "dark_academia": "твид шерстяной",
    "balletcore": "трикотажный",
}

#: Сезон → русское определение для запроса к Авито.
SEASON_RU_ADJ: dict[str, str] = {
    "winter": "зимний",
    "spring": "демисезонный",
    "summer": "летний",
    "autumn": "демисезонный",
    "all": "",
}

#: Подача → русское определение для запроса к Авито.
PRESENTATION_RU: dict[str, str] = {
    "feminine": "женский",
    "masculine": "мужской",
    "unisex": "",
}

#: Повод → формальность вещи с Авито (1 — повседневная … 3 — строгая).
OCCASION_FORMALITY: dict[str, int] = {
    "everyday": 1, "work": 3, "date": 2, "party": 2, "travel": 1, "event": 3,
}

_AVITO_PROVIDER: AvitoSearchProvider | None = None
_AVITO_SNAPSHOT_PROVIDER: AvitoSnapshotProvider | None = None


def avito_provider() -> AvitoSearchProvider:
    """Синглтон провайдера Авито (общий TTL-кэш на процесс)."""
    global _AVITO_PROVIDER
    if _AVITO_PROVIDER is None:
        _AVITO_PROVIDER = AvitoSearchProvider(
            city=settings.avito_city,
            timeout=settings.avito_timeout_sec,
            max_results=settings.avito_max_results,
            cache_ttl_sec=settings.avito_cache_ttl_sec,
            negative_ttl_sec=settings.avito_negative_ttl_sec,
        )
    return _AVITO_PROVIDER


def reset_avito_provider() -> None:
    """Сбросить синглтоны (нужно тестам при смене настроек)."""
    global _AVITO_PROVIDER, _AVITO_SNAPSHOT_PROVIDER
    _AVITO_PROVIDER = None
    _AVITO_SNAPSHOT_PROVIDER = None
    photo_traits_module.clear_cache()


def is_avito_url(url: str) -> bool:
    """Верификация «ссылки только на Авито»: хост из белого списка Авито."""
    try:
        host = (urlparse(url or "").hostname or "").lower()
    except ValueError:
        return False
    return any(host == allowed or host.endswith("." + allowed)
               for allowed in ("avito.ru",))


def ensure_avito_links(result: LookResult) -> LookResult:
    """Страховка «только Авито»: любая не-авито ссылка заменяется честным
    дип-линком на подборку Авито по этой вещи. Объявления не трогаем.

    Каждая вещь получает ``link_kind``: ``listing`` — ссылка ведёт на
    конкретное объявление (фото и цена которого показаны), ``search`` —
    резерв, подборка по этой вещи. Интерфейс честно различает эти два случая.
    """
    if not settings.avito_enabled:
        return result
    provider = avito_provider()
    for item in result.items:
        url = str(item.get("url") or "")
        if url and is_avito_url(url):
            item["source"] = "avito"
            item["link_kind"] = listing_url_kind(url)
            continue
        text = f"{item.get('brand') or ''} {item.get('name') or ''}".strip() or "одежда"
        item["url"] = provider.search_url_for(text)
        item["source"] = "avito"
        item["link_kind"] = "search"
        item["feed"] = "search"
        reasons = list(item.get("reasons") or [])
        note = "Ссылка ведёт на подборку Авито по этой вещи — там живые объявления с фото и ценами."
        if note not in reasons:
            reasons.append(note)
        item["reasons"] = reasons[:5]
    return result


def _slot_noun(slot: str, request: LookRequest) -> str:
    """Главное существительное слота с учётом сезона и повода."""
    season = request.season or "all"
    occasion = request.occasion or "everyday"
    if slot == "outerwear":
        return "куртка" if season == "summer" else "пальто"
    if slot == "top":
        if occasion == "work":
            return "рубашка"
        return "футболка" if season == "summer" else "свитер"
    if slot == "bottom":
        if request.presentation == "feminine" and season == "summer":
            return "юбка"
        return "брюки" if occasion == "work" else "джинсы"
    if slot == "shoes":
        if season == "summer":
            return "кеды"
        return "ботинки" if season in ("winter", "autumn", "spring") else "кроссовки"
    if slot == "accessory":
        return "шапка" if season == "winter" else "шарф"
    return RU_SLOT_NOUNS.get(slot, "одежда")


def _user_query_keywords(text: str | None, limit: int = 2) -> list[str]:
    """Самые содержательные слова свободной формулировки пользователя."""
    if not text:
        return []
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ]{4,}", text.lower().replace("ё", "е"))
    keywords: list[str] = []
    for word in words:
        if word in lexicon.RU_STOPWORDS or len(word) < 4:
            continue
        if word not in keywords:
            keywords.append(word)
        if len(keywords) >= limit:
            break
    return keywords


def ru_slot_query(request: LookRequest, slot: str) -> str:
    """Короткий русский запрос к Авито для слота образа.

    Формула: подача + существительное слота + стиль + сезон + слова
    пользователя. Короткие запросы дают у Авито самую релевантную выдачу.
    """
    parts: list[str] = []
    presentation = PRESENTATION_RU.get(request.presentation or "unisex", "")
    if presentation:
        parts.append(presentation)
    parts.append(_slot_noun(slot, request))
    style_adj = STYLE_RU_ADJ.get(request.style or "minimal", "")
    parts.extend(style_adj.split()[:2])
    season_adj = SEASON_RU_ADJ.get(request.season or "all", "")
    if season_adj:
        parts.append(season_adj)
    color_ru = ""
    for color_id in list(request.preferred_colors or [])[:1]:
        spec = COLORS.get(color_id)
        if spec is not None:
            color_ru = spec.ru.lower()
            break
    if color_ru:
        parts.append(color_ru)
    parts.extend(_user_query_keywords(request.query))
    deduped = list(dict.fromkeys(part for part in parts if part))[:6]
    return " ".join(deduped) if deduped else "одежда"


def _avito_colors(card: ProductItem, request: LookRequest) -> list[str]:
    """Цвета приложения для объявления: честная детекция + безопасный запас."""
    colors: list[str] = []
    for engine_word in lexicon.detect_colors(f"{card.name} {card.description}"):
        app_color = ENGINE_TO_APP_COLOR.get(engine_word)
        if app_color and app_color not in colors:
            colors.append(app_color)
    if card.color:
        app_color = ENGINE_TO_APP_COLOR.get(str(card.color).lower())
        if app_color and app_color not in colors:
            colors.insert(0, app_color)
    if colors:
        return colors[:3]
    avoid = set(request.avoid_colors or [])
    for candidate in list(request.preferred_colors or []) + ["grey", "black", "white", "navy", "beige"]:
        if candidate in COLORS and candidate not in avoid:
            return [candidate]
    return ["grey"]


def _avito_sizes(card: ProductItem, app_category: str) -> list[str]:
    """Размеры из заголовка/описания; иначе — полный ряд категории.

    Полный ряд — осознанный fail-open: фильтр размера не должен выкидывать
    живые объявления, где размер указан только на фото или в карточке Авито.
    """
    text = f"{card.name} {card.description}"
    found: list[str] = []
    for token in re.findall(r"\b(XXS|XS|S|M|L|XL|XXL|XXXL)\b", text, re.IGNORECASE):
        normalized = token.upper()
        if normalized not in found:
            found.append(normalized)
    for number in re.findall(r"\b(3[4-9]|4[0-9]|5[0-8])\b", text):
        if number not in found:
            found.append(number)
    if found:
        return found[:6]
    return list(CATEGORY_SIZES.get(app_category, ("one size",)))


def _avito_fit(card: ProductItem) -> str:
    text = f"{card.name} {card.description}".lower()
    if "оверсайз" in text or "oversize" in text:
        return "oversize"
    if "облегающ" in text or "слим" in text or "slim" in text or "скинни" in text:
        return "slim"
    if "свободн" in text or "релакс" in text or "relax" in text or "прямой" in text:
        return "relaxed"
    return "regular"


def avito_card_to_catalog_item(
    card: ProductItem,
    request: LookRequest,
    index: int = 0,
) -> CatalogItem:
    """Живое объявление Авито → позиция для ранжировщика приложения.

    Ссылка, фото и цена сохраняются как есть; стили/настроения/сезоны
    наследуются от запроса (объявление уже отобрано под них живым поиском).
    """
    sku = card.sku or card.id or f"avito_{index}"
    engine_cat = str(card.category or "accessory").lower().split()[0]
    app_category = ENGINE_TO_APP_CATEGORY.get(engine_cat, "accessory")
    colors = _avito_colors(card, request)
    return CatalogItem(
        product_id=zlib.crc32(sku.encode("utf-8")) % 2_147_483_647,
        sku=sku,
        category=app_category,
        name=card.name or "Вещь с Авито",
        brand=card.brand or _extract_brand(card.name) or "Без бренда",
        price_rub=float(card.price or 0),
        url=card.source_url,
        image_url=card.image or "",
        colors=colors,
        color_hexes=[COLORS[color].hex for color in colors if color in COLORS],
        styles=[request.style or "minimal"],
        moods=[request.mood or "calm"],
        silhouettes=[],
        # Кому адресована вещь по объявлению («женское», «мужское»):
        # ранжировщик приложения отсекает заведомо не своё.
        gendered=[str((card.meta or {}).get("gender") or "").strip()]
        if str((card.meta or {}).get("gender") or "").strip()
        else [],
        seasons=["all"] if (request.season or "all") == "all" else [request.season],
        sizes=_avito_sizes(card, app_category),
        fit=_avito_fit(card),
        formality=OCCASION_FORMALITY.get(request.occasion or "everyday", 2),
        rating=4.5,
        reviews_count=30,
        verification_status="verified",
        verification_score=round(min(0.97, max(0.6, float(card.confidence or 0.7))), 3),
        source="avito",
    )

#: Перевод отзывов критика движка (строки портированы дословно).
CRITIC_RU: dict[str, str] = {
    "Silhouette is too predictable / safe. Needs stronger shape language.": (
        "Силуэт слишком предсказуемый — нужна более сильная форма."
    ),
    "No clear hero piece. The outfit lacks a strong focal point.": (
        "Нет явной ключевой вещи — образу не хватает фокуса."
    ),
    "Insufficient contrast in texture or volume.": "Мало контраста по фактуре или объёму.",
    "Too many generic items. Dilutes the fashion strength of the look.": (
        "Слишком много масс-маркета — он размывает характер образа."
    ),
    "Styling thesis is weak or generic. Needs a sharper cultural idea.": (
        "Стилистический тезис слабый — нужна более точная идея."
    ),
    "Color story is fragmented.": "Цветовая история распадается.",
    "Overall item quality is not high enough for a strong editorial-feeling look.": (
        "Среднее качество вещей ниже уровня сильного эдиториал-образа."
    ),
    "CRITICAL: Outfit needs full rebuild.": "Критично: образ нужно пересобрать.",
    "Several issues detected — recommend refinement.": "Найдено несколько замечаний — стоит уточнить состав.",
    "Strong, coherent, fashion-forward look. Approved.": "Сильный, цельный образ — одобрено.",
    "Minor notes only. Acceptable.": "Только мелкие замечания, допустимо.",
}


# ─── карточки движка из каталога приложения ─────────────────────────────────


def brand_tier(brand: str) -> str:
    return BRAND_TIERS.get((brand or "").strip().lower(), DEFAULT_TIER)


def to_engine_card(item: CatalogItem) -> ProductItem:
    """``CatalogItem`` (₽, русские теги) → ``ProductItem`` движка."""
    name_terms = lexicon.detect_terms(item.name, ("garment", "material", "silhouette", "aesthetic"))
    style_profile = STYLE_ENGINE.get(item.styles[0] if item.styles else "minimal", STYLE_ENGINE["minimal"])
    style_terms = [word for word in str(style_profile["keywords"]).split() if len(word) > 3]
    mood_terms = [word for mood in item.moods for word in str(MOOD_ENGINE.get(mood, "")).split() if len(word) > 3]
    color_terms = [APP_COLOR_TO_ENGINE[color] for color in item.colors if color in APP_COLOR_TO_ENGINE]
    winter = "winter" in item.seasons or "autumn" in item.seasons
    seasonal = "winter wool layered" if winter else "light breathable summer"

    description = " ".join(
        dict.fromkeys(
            name_terms
            + style_terms
            + mood_terms
            + color_terms
            + [APP_CATEGORY_TO_ENGINE.get(item.category, "accessory"), item.fit, seasonal]
        )
    )
    tags = list(
        dict.fromkeys(
            name_terms
            + color_terms
            + [word for word in " ".join(name_terms).split() if word]
            + item.styles
            + item.moods
            + item.colors
        )
    )
    tier = brand_tier(item.brand)
    category = lexicon.engine_category(item.name, APP_CATEGORY_TO_ENGINE.get(item.category, "accessory"))
    return ProductItem(
        id=item.sku,
        sku=item.sku,
        product_id=item.product_id,
        name=item.name,
        brand=item.brand,
        category=category,
        price=float(item.price_rub),
        currency="RUB",
        image=item.image_url,
        source_url=item.url,
        source_type=tier,
        availability="available",
        confidence=min(0.99, max(settings.fashion_engine_min_confidence, float(item.verification_score or 0.7))),
        description=description,
        color=color_terms[0] if color_terms else None,
        tags=tags,
        meta={
            "tier": tier,
            "app_category": item.category,
            "styles": list(item.styles),
            "moods": list(item.moods),
            "color_ids": list(item.colors),
            "formality": item.formality,
            "rating": item.rating,
            "reviews": item.reviews_count,
        },
    )


def slot_for_item(item: CatalogItem, engine_category: str | None) -> str:
    """Слот приложения: приоритет у категории движка, но только если она
    согласуется с категорией каталога."""
    app_slots = [slot for slot, categories in SLOT_CATEGORIES.items() if item.category in categories]
    mapped = ENGINE_CATEGORY_TO_SLOT.get(str(engine_category or "").lower())
    if mapped and mapped in app_slots:
        return mapped
    if app_slots:
        return app_slots[0]
    return mapped or "accessory"


# ─── профиль и запрос для движка ────────────────────────────────────────────


def _fit_preference(body: BodyProfile | None) -> str:
    if body is None or not body.recommended_fits:
        return "regular"
    return FIT_ENGINE.get(body.recommended_fits[0], "regular")


def build_profile(
    request: LookRequest,
    *,
    palette: PaletteProfile | None = None,
    body: BodyProfile | None = None,
) -> UserStyleProfile:
    """Профиль движка из запроса приложения."""
    style_profile = STYLE_ENGINE.get(request.style, STYLE_ENGINE["minimal"])
    colors: list[str] = []
    for color_id in list(request.preferred_colors) + list(getattr(palette, "recommended", ()) or [])[:4]:
        mapped = APP_COLOR_TO_ENGINE.get(color_id)
        if mapped and mapped not in colors:
            colors.append(mapped)
    disliked = [
        APP_COLOR_TO_ENGINE[color_id]
        for color_id in request.avoid_colors
        if color_id in APP_COLOR_TO_ENGINE
    ]
    niche = request.niche_level if request.niche_level is not None else int(style_profile["niche"])
    return UserStyleProfile(
        niche_level=niche,
        aesthetics=list(style_profile["aesthetics"]),
        budget_max=float(request.budget_rub),
        currency="RUB",
        occasion=request.occasion,
        fit_preference=_fit_preference(body),
        gender=request.presentation,
        colors=colors,
        preferred_silhouette=[_fit_preference(body)],
        disliked_items=sorted(set(disliked)),
        height_cm=request.height_cm,
        notes=list(getattr(palette, "signals", ()) or []),
    )


def build_engine_query(
    request: LookRequest,
    *,
    palette: PaletteProfile | None = None,
    body: BodyProfile | None = None,
    extra: str = "",
) -> str:
    """Свободный текстовый запрос для движка (RU + EN термины)."""
    style_profile = STYLE_ENGINE.get(request.style, STYLE_ENGINE["minimal"])
    parts: list[str] = []
    if request.query:
        parts.append(request.query)
        parts.append(lexicon.translate_text(request.query, ("garment", "material", "silhouette", "aesthetic")))
        parts.extend(lexicon.detect_colors(request.query))
    parts.append(str(style_profile["keywords"]))
    parts.append(str(MOOD_ENGINE.get(request.mood, "")))
    parts.append(str(OCCASION_ENGINE.get(request.occasion, "")))
    parts.append(str(SEASON_ENGINE.get(request.season, "")))
    fit = _fit_preference(body)
    parts.append(fit)
    # Цвета добавляем только выбранные пользователем: автоматическая палитра
    # из фото слишком охотно уводит тезис движка в «тёмную» сторону.
    for color_id in list(request.preferred_colors)[:3]:
        mapped = APP_COLOR_TO_ENGINE.get(color_id)
        if mapped:
            parts.append(mapped)
    if extra:
        parts.append(extra)
    return " ".join(part for part in parts if part).strip()


def _request_from_look(look: Any) -> LookRequest:
    ranking = look.loads(look.ranking_json, {}) if hasattr(look, "loads") else {}
    query = ranking.get("query")
    return LookRequest(
        style=look.style,
        mood=look.mood,
        occasion=look.occasion,
        season=look.season,
        presentation=look.presentation,
        height_cm=float(look.height_cm),
        weight_kg=float(look.weight_kg),
        budget_rub=float(look.budget_rub),
        preferred_colors=list(ranking.get("preferred_colors") or []),
        avoid_colors=list(ranking.get("avoid_colors") or []),
        size=ranking.get("size"),
        weights=ranking.get("weights"),
        query=str(query).strip() if isinstance(query, str) and query.strip() else None,
    )


# ─── запуск движка ──────────────────────────────────────────────────────────


def _web_provider() -> WebSearchProvider | None:
    """Живой провайдер из настроек; None, если источники не сконфигурированы."""
    if not settings.web_search_enabled:
        return None
    provider = WebSearchProvider(
        serpapi_key=settings.serpapi_api_key,
        google_key=settings.google_cse_api_key,
        google_cx=settings.google_cse_cx,
        feed_url=settings.product_feed_url,
        fx_rates=settings.fx_rates,
        timeout=settings.web_search_timeout_sec,
        max_results=settings.web_search_max_results,
    )
    return provider if provider.available() else None


def _providers(
    cards: list[ProductItem],
    *,
    min_score: float = 8.0,
    include_external: bool = False,
    live: bool | None = None,
) -> list[Any]:
    """Провайдеры движка.

    Основной режим (``AVITO_ENABLED=true``): только Авито — живые объявления
    со ссылками, фото и ценами. ``live=False`` внутри этого режима означает
    «движок поверх уже собранного пула Авито» (без повторных HTTP-запросов).

    Резервный режим (``AVITO_ENABLED=false``, тесты/офлайн): прежний каталог
    приложения; внешние источники (живой web-поиск, мок-архетипы)
    подключаются только в поисковой выдаче (``include_external=True``).
    """
    use_live = settings.avito_enabled if live is None else bool(live and settings.avito_enabled)
    if use_live:
        providers: list[Any] = [avito_provider()]
        # Снимок выдачи идёт вторым источником: пока живая выдача отвечает,
        # он ничего не добавляет, но как только Авито закрылся капчей или
        # отдал пустой список — в образе остаются конкретные объявления.
        if settings.avito_snapshot_enabled:
            providers.append(avito_snapshot_provider())
        return providers
    providers = [CatalogSearchProvider(cards, min_score=min_score)]
    if not include_external:
        return providers
    web = _web_provider()
    if web is not None:
        providers.append(web)
    if settings.fashion_engine_enable_mock:
        providers.append(MockRealProductProvider())
    return providers


@dataclass
class EngineRun:
    """Результат прогона движка по каталогу приложения."""

    query: str
    profile: UserStyleProfile
    discovery: DiscoveryResult
    outfit: OutfitResult
    cards: dict[str, ProductItem] = field(default_factory=dict)
    providers: list[str] = field(default_factory=list)
    #: Сколько вещей пришло из живой выдачи Авито, а сколько — из снимка.
    feeds: dict[str, int] = field(default_factory=dict)
    #: Человеческие пояснения к источникам («живых объявлений: 6»).
    feed_notes: list[str] = field(default_factory=list)
    live_error: str | None = None
    snapshot_captured_at: str = ""

    @property
    def ordered_skus(self) -> list[str]:
        return [card.sku or card.id for card in self.discovery.products]

    def rank_index(self, sku: str) -> int | None:
        try:
            return self.ordered_skus.index(sku)
        except ValueError:
            return None


def run_engine(
    prepared: PreparedPool,
    request: LookRequest,
    *,
    cards: list[ProductItem] | None = None,
    include_external: bool = False,
    live: bool | None = None,
) -> EngineRun:
    """Прогнать пайплайн движка.

    Живой режим (Авито включён и ``live`` не запрещён): discovery идёт по
    объявлениям Авито напрямую. Иначе — по пулу кандидатов приложения
    (``include_external=True`` добавляет живой web-поиск и мок-архетипы).
    """
    use_live = settings.avito_enabled if live is None else bool(live and settings.avito_enabled)
    profile = build_profile(request, palette=prepared.palette, body=prepared.body)
    query = build_engine_query(request, palette=prepared.palette, body=prepared.body)

    if use_live:
        providers = _providers([], live=True)
        options = EngineOptions(
            max_products=settings.fashion_engine_max_products,
            limit_per_query=min(settings.fashion_engine_limit_per_query, settings.avito_max_results),
            min_confidence=settings.fashion_engine_min_confidence,
            max_queries=settings.avito_max_queries,
        )
        engine = FashionEngine(providers=providers, options=options)
        discovery = engine.discover(query, profile)
        outfit = engine.create_outfit(query, profile, preloaded=discovery)
        _rate_appearance(discovery.products, request, profile)
        snapshot = avito_snapshot_provider()
        return EngineRun(
            query=query,
            profile=profile,
            discovery=discovery,
            outfit=outfit,
            cards={card.sku or card.id: card for card in discovery.products},
            providers=[provider.name for provider in providers],
            feeds=_feed_counts(discovery.products),
            live_error=avito_provider().last_error,
            snapshot_captured_at=snapshot.captured_at.isoformat() if snapshot.captured_at else "",
        )

    if cards is None:
        cards = [to_engine_card(scored.item) for scored in prepared.ranked]
    cards = cards[: max(1, settings.fashion_engine_max_cards)]

    providers = _providers(cards, include_external=include_external, live=False)

    options = EngineOptions(
        max_products=settings.fashion_engine_max_products,
        limit_per_query=settings.fashion_engine_limit_per_query,
        min_confidence=settings.fashion_engine_min_confidence,
    )
    engine = FashionEngine(providers=providers, options=options)
    discovery = engine.discover(query, profile)
    outfit = engine.create_outfit(query, profile, preloaded=discovery)
    return EngineRun(
        query=query,
        profile=profile,
        discovery=discovery,
        outfit=outfit,
        cards={card.sku or card.id: card for card in cards},
        providers=[provider.name for provider in providers],
    )


# ─── сборка ответа ──────────────────────────────────────────────────────────


def aesthetic_ru(run: EngineRun) -> str:
    """Эстетика движка по-русски: тезис + доминирующий оттенок образа."""
    thesis = engine_keywords.thesis_label_ru(run.outfit.styling_thesis)
    items = list(run.outfit.items)
    color_id = ""
    for item in items:
        attributes = item.fashion_attributes
        if attributes and attributes.color not in (None, "", "unknown"):
            color_id = str(attributes.color)
            break
    spec = COLORS.get(color_id)
    if spec is None:
        return thesis
    return f"{thesis} · палитра: {spec.ru}"


def _critic_ru(feedback: list[str]) -> list[str]:
    return [CRITIC_RU.get(line, line) for line in feedback]


def _taste_mix(run: EngineRun) -> dict[str, int]:
    mix: dict[str, int] = {}
    for card in run.discovery.products:
        mix[card.taste_category] = mix.get(card.taste_category, 0) + 1
    return mix


#: Роль вещи по слоту — для позиций, которые добрал бюджетный оптимизатор
#: (движок их в своём образе не выбирал).
ROLE_BY_SLOT: dict[str, str] = {
    "outerwear": "layer",
    "top": "hero",
    "bottom": "base",
    "dress": "hero",
    "shoes": "footwear",
    "bag": "accessory",
    "accessory": "accessory",
}


def _engine_item_meta(
    card: ProductItem | None,
    slot: str,
    *,
    role: str | None = None,
    in_engine_outfit: bool = False,
) -> dict[str, Any]:
    if card is None:
        return {
            "slot": slot,
            "slot_label": SLOT_LABELS.get(slot, slot),
            "role": role or ROLE_BY_SLOT.get(slot),
            "role_label": lexicon.role_label_ru(role or ROLE_BY_SLOT.get(slot)),
            "fashion_score": 0,
            "taste_category": "",
            "taste_label": "",
            "source_in_run": "budget-guard",
        }
    attributes = card.fashion_attributes
    components = card.taste_components or {}
    resolved_role = role or card.role or ROLE_BY_SLOT.get(slot)
    return {
        "slot": slot,
        "slot_label": SLOT_LABELS.get(slot, slot),
        "role": resolved_role,
        "role_label": lexicon.role_label_ru(resolved_role),
        "in_engine_outfit": in_engine_outfit,
        "source_in_run": "engine-outfit" if in_engine_outfit else "engine-shortlist",
        "taste_category": card.taste_category,
        "taste_label": lexicon.taste_label_ru(card.taste_category),
        "fashion_score": int(card.fashion_score or 0),
        "trend_relevance": round(float(getattr(attributes, "trend_relevance", 0.4) or 0.4), 3),
        "uniqueness": round(float(components.get("uniqueness", 50) or 50) / 100, 3),
        "generic_score": int(card.generic_score or 0),
        "silhouette": list(getattr(attributes, "silhouette", []) or []),
        "material": getattr(attributes, "material", None),
        "aesthetic": getattr(attributes, "aesthetic", None),
        "engine_category": card.category,
        "provider": card.provider,
    }


def _engine_reasons(
    card: ProductItem | None,
    run: EngineRun,
    limit: int = 3,
    *,
    role: str | None = None,
) -> list[str]:
    if card is None:
        return []
    resolved_role = role or card.role
    reasons = [
        f"Разбор: {lexicon.role_label_ru(resolved_role)} · {lexicon.taste_label_ru(card.taste_category)} "
        f"({int(card.fashion_score or 0)}/100)"
    ]
    attributes = card.fashion_attributes
    if attributes is not None:
        details: list[str] = []
        if attributes.material and attributes.material != "unknown":
            details.append(f"фактура — {lexicon.material_label_ru(attributes.material)}")
        if attributes.silhouette:
            labels = [lexicon.silhouette_label_ru(value) for value in attributes.silhouette[:2]]
            details.append("силуэт — " + ", ".join(label for label in labels if label))
        if attributes.aesthetic and attributes.aesthetic != "contemporary":
            details.append(f"эстетика — {lexicon.aesthetic_label_ru(attributes.aesthetic)}")
        if details:
            reasons.append("Fashion Intelligence: " + "; ".join(details))
    thesis = engine_keywords.thesis_label_ru(run.outfit.styling_thesis)
    if thesis:
        reasons.append(f"Работает на тезис образа «{thesis}»")
    return reasons[:limit]


def _engine_tips(run: EngineRun) -> list[str]:
    logic = run.outfit.styling_logic or {}
    tips: list[str] = []
    if logic.get("silhouette") and logic["silhouette"] != "balanced":
        tips.append(f"Силуэтная формула: {logic['silhouette'].replace('+', '·')}.")
    if logic.get("color") and logic["color"] != "monochrome":
        tips.append(f"Цветовая ось: {logic['color'].replace('/', '·')}.")
    if logic.get("focalPoint"):
        tips.append(f"Фокусная вещь — {logic['focalPoint']}.")
    if run.outfit.critic_decision == "APPROVE":
        tips.append("Образ одобрен критиком без правок.")
    elif run.outfit.critic_feedback:
        tips.append(f"Критик: {_critic_ru(run.outfit.critic_feedback)[0]}")
    return tips


def _blended_score(app_score: float, card: ProductItem | None, rank_index: int | None, total: int) -> float:
    """Оценка позиции: движок + ранжировщик приложения (детерминированно)."""
    engine_norm = float(card.fashion_score or 0) / 100 if card else 0.5
    rank_bonus = 0.0
    if rank_index is not None and total > 0:
        rank_bonus = max(0.0, 1.0 - rank_index / total)
    return round(0.55 * engine_norm + 0.30 * app_score + 0.15 * rank_bonus, 4)


#: Доля релевантности тексту запроса в позиции вещи внутри выдачи поиска.
#: Без неё выдача определялась бы только fashion score вещи и не зависела бы
#: от запроса (у провайдера поверх всего каталога пул одинаковый для всех
#: расширенных запросов).
SEARCH_RELEVANCE_WEIGHT = 0.15

#: ``query_match`` провайдера — сумма попаданий по токенам запроса; за
#: «полную» релевантность принимаем 60 баллов (примерно четыре точных
#: попадания), дальше рост не даёт преимущества.
SEARCH_RELEVANCE_FULL = 60.0


def _query_relevance(card: ProductItem | None) -> float:
    if card is None:
        return 0.0
    raw = float((card.meta or {}).get("query_match") or 0.0)
    return max(0.0, min(1.0, raw / SEARCH_RELEVANCE_FULL))


def _search_position(
    app_score: float,
    card: ProductItem | None,
    rank_index: int | None,
    total: int,
) -> float:
    """Позиция вещи в выдаче поиска: гибридная оценка + релевантность запросу."""
    base = _blended_score(app_score, card, rank_index, total)
    return round((1 - SEARCH_RELEVANCE_WEIGHT) * base + SEARCH_RELEVANCE_WEIGHT * _query_relevance(card), 4)


def _engine_block(
    run: EngineRun,
    *,
    app_score: float,
    final_score: float,
    repair: str | None,
    fallback: str | None = None,
) -> dict[str, Any]:
    meta = run.outfit.meta or {}
    return {
        "pipeline": PIPELINE,
        "enabled": True,
        "engine_version": str(meta.get("engineVersion", "")),
        "styling_thesis": run.outfit.styling_thesis,
        "styling_thesis_ru": engine_keywords.thesis_label_ru(run.outfit.styling_thesis),
        "aesthetic": run.outfit.aesthetic,
        "aesthetic_ru": aesthetic_ru(run),
        "outfit_score": round(float(run.outfit.outfit_score or 0), 1),
        "app_score": round(float(app_score), 1),
        "final_score": round(float(final_score), 1),
        "score_formula": f"{round((1 - settings.fashion_engine_score_weight) * 100)}% приложение + "
        f"{round(settings.fashion_engine_score_weight * 100)}% движок",
        "critic_decision": run.outfit.critic_decision,
        "critic_feedback": _critic_ru(run.outfit.critic_feedback),
        "styling_logic": run.outfit.styling_logic,
        "roles": {card.sku or card.id: card.role for card in run.outfit.items},
        "queries_used": list(meta.get("queriesUsed") or run.discovery.queries_used[:8]),
        "queries_total": int(meta.get("queriesTotal") or len(run.discovery.queries_used)),
        "candidates": {
            "raw_items": int(meta.get("rawItems") or run.discovery.raw_items),
            "considered": int(meta.get("totalCandidatesConsidered") or run.discovery.considered),
            "validated": int(meta.get("validatedProducts") or len(run.discovery.products)),
            "outfits_built": int(meta.get("candidatesBuilt") or 0),
            "dropped": dict(meta.get("dropped") or run.discovery.dropped),
        },
        "taste_mix": _taste_mix(run),
        "niche_level": run.profile.niche_level,
        "aesthetics": list(run.profile.aesthetics),
        "fit_preference": run.profile.fit_preference,
        "profile": run.profile.to_dict(),
        "theses": list(meta.get("theses") or []),
        "alternatives": list(run.outfit.alternatives),
        "repair": repair,
        "fallback": fallback,
        "providers": list(run.providers),
        # Откуда пришли конкретные объявления: живая выдача и/или снимок.
        "feeds": dict(run.feeds),
        "feed_notes": list(run.feed_notes),
        "live_error": run.live_error,
        "snapshot_captured_at": run.snapshot_captured_at,
    }


def _slot_pool(prepared: PreparedPool, run: EngineRun, slot: str) -> list[ScoredItem]:
    """Кандидаты слота в порядке движка, затем — в порядке приложения."""
    slot_items = prepared.candidates_by_slot.get(slot) or []
    by_sku = {scored.sku: scored for scored in slot_items}
    ordered: list[ScoredItem] = []
    for card in run.discovery.products:
        sku = card.sku or card.id
        if sku in by_sku:
            ordered.append(by_sku.pop(sku))
    ordered.extend(sorted(by_sku.values(), key=lambda s: (-s.score, s.item.price_rub, s.item.sku)))
    return ordered


def _alternatives(prepared: PreparedPool, run: EngineRun, slot: str, taken: set[str], limit: int = 3) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    for scored in _slot_pool(prepared, run, slot):
        if scored.sku in taken:
            continue
        card = run.cards.get(scored.sku)
        options.append(
            {
                "sku": scored.sku,
                "name": scored.item.name,
                "brand": scored.item.brand,
                "price_rub": scored.item.price_rub,
                "score": round(scored.score, 3),
                "colors": list(scored.item.colors),
                "fashion_score": int(card.fashion_score or 0) if card else 0,
                "taste_category": card.taste_category if card else "",
            }
        )
        if len(options) >= limit:
            break
    return options


def generate_look(products: list[CatalogItem], request: LookRequest) -> LookResult:
    """Собрать образ движком ASSTYLIST (вещи — только с Авито).

    Основной режим: живые объявления Авито → интеллект движка → бюджетная
    страховка приложения. Резервный режим (``AVITO_ENABLED=false``): прежний
    пул каталога приложения.
    """
    if settings.avito_enabled:
        return generate_look_avito(products, request)
    prepared = prepare_pool(products, request)
    run = run_engine(prepared, request, live=False)
    return _assemble_look(prepared, request, run)


# ─── пул реальных объявлений: живая выдача + снимок выдачи ────────────────────

#: Источник карточки: живая выдача Авито или сохранённый снимок реальных объявлений.
FEED_LIVE = "live"
FEED_SNAPSHOT = "snapshot"


def avito_snapshot_provider() -> AvitoSnapshotProvider:
    """Синглтон провайдера-снимка: реальные объявления, сохранённые в поставке."""
    global _AVITO_SNAPSHOT_PROVIDER
    if _AVITO_SNAPSHOT_PROVIDER is None:
        _AVITO_SNAPSHOT_PROVIDER = AvitoSnapshotProvider(
            settings.avito_snapshot_path or None,
            max_results=max(8, settings.avito_max_results),
            max_age_days=settings.avito_snapshot_max_age_days,
        )
    return _AVITO_SNAPSHOT_PROVIDER


def feed_of(card: ProductItem) -> str:
    """Живое объявление или позиция из снимка выдачи."""
    return FEED_SNAPSHOT if (card.meta or {}).get("snapshot") else FEED_LIVE


def listing_url_kind(url: str) -> str:
    """``listing`` — ссылка на конкретное объявление, ``search`` — подборка."""
    return "listing" if looks_like_listing_url(url) else "search"


def _snapshot_cards_for_slot(
    request: LookRequest,
    slot: str,
    profile: UserStyleProfile,
    *,
    limit: int,
    exclude: set[str] | None = None,
) -> list[ProductItem]:
    """Реальные объявления из снимка выдачи под конкретный слот."""
    if not settings.avito_snapshot_enabled or limit <= 0:
        return []
    provider = avito_snapshot_provider()
    try:
        cards = provider.search(
            ru_slot_query(request, slot),
            SearchContext(
                user_profile=profile,
                limit=max(limit, 4),
                categories=list(SLOT_ENGINE_CATEGORIES.get(slot, [])),
            ),
        )
    except Exception:
        return []
    taken = exclude or set()
    return [card for card in cards if str(card.sku or card.id) not in taken][:limit]


def _top_up_with_snapshot(
    cards: list[ProductItem],
    request: LookRequest,
    slots: list[str],
    profile: UserStyleProfile,
) -> list[ProductItem]:
    """Добрать слоты реальными объявлениями из снимка, если живая выдача тонка.

    Пользователь должен видеть конкретную вещь с фото и ссылкой на объявление
    в каждом слоте образа — независимо от того, пустил ли Авито живой запрос.
    """
    if not settings.avito_snapshot_enabled:
        return []
    per_slot = max(1, int(settings.avito_snapshot_per_slot))
    live_by_slot: dict[str, int] = {}
    for card in cards:
        if feed_of(card) != FEED_LIVE:
            continue
        slot = ENGINE_CATEGORY_TO_SLOT.get(str(card.category or "").lower(), "accessory")
        live_by_slot[slot] = live_by_slot.get(slot, 0) + 1

    taken = {str(card.sku or card.id) for card in cards}
    added: list[ProductItem] = []
    for slot in slots:
        missing = per_slot - live_by_slot.get(slot, 0)
        if missing <= 0:
            continue
        for card in _snapshot_cards_for_slot(
            request, slot, profile, limit=missing, exclude=taken
        ):
            taken.add(str(card.sku or card.id))
            added.append(card)
    return added


def _apply_appearance(
    cards: list[ProductItem],
    request: LookRequest,
    profile: UserStyleProfile,
    *,
    with_photos: bool = True,
) -> None:
    """Оценить внешний вид каждой вещи: описание + фотография объявления.

    Ключевые слова дают релевантность, а этот слой отвечает на вопрос «та ли
    это вещь»: оттенок, фактура, силуэт, состояние, подача и то, что видно на
    снимке (при доступности CDN Авито — измеренные признаки фотографии).
    """
    photo_budget = max(0, int(settings.avito_photo_max_per_look)) if (
        with_photos and settings.avito_photo_analysis
    ) else 0
    for card in cards:
        image = str(card.image or "")
        existing = dict((card.meta or {}).get("photo_traits") or {})
        photo: dict[str, Any] | None = None
        if photo_budget > 0 and image and not existing:
            photo = photo_traits_module.traits_for_url(
                image, timeout=settings.avito_photo_timeout_sec
            )
            photo_budget -= 1
        traits = analyze_listing(
            card.name,
            card.description or "",
            "",
            image,
            photo_traits=photo or existing or None,
        )
        if photo:
            # Оттенки со снимка приходят как id палитры приложения — переводим
            # в слова движка, чтобы сравнивать с палитрой пользователя.
            engine_words = [
                APP_COLOR_TO_ENGINE[color_id]
                for color_id in (photo.get("colors") or [])
                if color_id in APP_COLOR_TO_ENGINE
            ]
            for word in engine_words:
                if word not in traits.colors:
                    traits.colors.append(word)
        match = appearance_match(
            traits,
            preferred_colors=list(profile.colors),
            avoid_colors=[word for word in profile.disliked_items if word],
            silhouette_preference=(profile.preferred_silhouette or [None])[0],
            style=request.style,
            season=request.season,
            presentation=request.presentation,
            budget=float(request.budget_rub or 0),
            price=float(card.price or 0),
            size=request.size,
        )
        meta = card.meta if isinstance(card.meta, dict) else {}
        meta["appearance"] = match.to_dict()
        meta["traits"] = traits.to_dict()
        meta["appearance_reasons"] = _appearance_reasons(traits, match)
        meta["photo_traits"] = photo or existing or {}
        meta["feed"] = feed_of(card)
        meta["link_kind"] = listing_url_kind(card.source_url)
        card.meta = meta
        # Уверенность растёт вместе с совпадением по внешнему виду и описанию.
        card.confidence = round(
            min(0.97, max(0.55, 0.5 * float(card.confidence or 0.6) + 0.5 * (0.6 + 0.4 * match.score))),
            3,
        )


def _rate_appearance(
    cards: list[ProductItem],
    request: LookRequest,
    profile: UserStyleProfile,
    *,
    with_photos: bool = True,
) -> None:
    """Учесть внешний вид вещи в её итоговой оценке (один раз на вещь).

    Оценка движка отвечает за вкус и архитектуру образа, а этот слой — за то,
    подходит ли конкретная вещь: оттенок, фактура, силуэт, состояние и фото.
    """
    missing = [card for card in cards if not (card.meta or {}).get("appearance")]
    if missing:
        _apply_appearance(missing, request, profile, with_photos=with_photos)
    for card in cards:
        meta = card.meta if isinstance(card.meta, dict) else {}
        if meta.get("appearance_blended"):
            continue
        appearance = float((meta.get("appearance") or {}).get("score") or 0.0)
        engine_score = float(card.fashion_score or 0)
        meta["engine_fashion_score"] = int(engine_score)
        meta["appearance_blended"] = True
        card.meta = meta
        blended = int(round(0.68 * engine_score + 32.0 * appearance))
        if meta.get("presentation_conflict"):
            # Вещь другого адресата («мужской» свитер для женского образа):
            # не выбрасываем — вдруг это единственное, что нашлось, но вперёд
            # пускаем то, что человеку действительно подходит.
            blended = max(0, blended - 6)
        card.fashion_score = blended


def _feed_counts(cards: list[ProductItem]) -> dict[str, int]:
    """Сколько вещей пришло живой выдачей, а сколько — снимком."""
    counts = {FEED_LIVE: 0, FEED_SNAPSHOT: 0}
    for card in cards:
        feed = feed_of(card)
        counts[feed] = counts.get(feed, 0) + 1
    return counts


def _appearance_reasons(traits: Any, match: Any) -> list[str]:
    """Человеческие причины выбора вещи: что видно на фото и в описании."""
    reasons: list[str] = []
    if traits.colors:
        labels = [COLORS[color].ru for color in traits.colors[:2] if color in COLORS]
        if labels:
            reasons.append(f"Оттенок: {', '.join(labels)} — согласуется с палитрой образа.")
    if traits.materials:
        materials = [lexicon.material_label_ru(term) for term in traits.materials[:2]]
        reasons.append(f"Фактура по описанию: {', '.join(materials)}.")
    if traits.silhouettes:
        silhouettes = [lexicon.silhouette_label_ru(term) for term in traits.silhouettes[:2]]
        reasons.append(f"Силуэт: {', '.join(silhouettes)}.")
    if traits.condition:
        reasons.append(f"Состояние по объявлению: {traits.condition}.")
    if traits.photo_traits:
        photo = traits.photo_traits
        if photo.get("colors_hex"):
            tone = "тёмный" if photo.get("brightness", 0.5) < 0.35 else "светлый"
            studio = "студийный кадр" if photo.get("background_flat") else "живое фото"
            reasons.append(f"На фото: {tone} кадр, {studio} — снимок проверен.")
        else:
            reasons.append("Фото объявления проверено: вещь видна на снимке.")
    elif traits.photo_quality:
        reasons.append("Есть фото объявления с CDN Авито — вещь видно целиком.")
    if match.components.get("presentation", 1.0) < 0.5:
        reasons.append("Внимание: подача объявления (муж/жен) отличается от вашей — проверьте крой.")
    return reasons[:4]


def _fetch_avito_pool(
    request: LookRequest,
    *,
    body: BodyProfile | None = None,
    palette: PaletteProfile | None = None,
    slots: list[str] | None = None,
) -> tuple[list[ProductItem], list[str]]:
    """Пул реальных объявлений: живой Авито + снимок выдачи.

    Каждый слот получает свой короткий русский запрос; живая выдача идёт
    параллельно, а недостающие слоты добираются реальными объявлениями из
    снимка — пустой или «дефолтной» выдачи не бывает. Возвращает
    (карточки без дублей, запросы слотов).
    """
    target_slots = list(slots) if slots else list(SLOT_CATEGORIES)
    profile = build_profile(request, palette=palette, body=body)
    provider = avito_provider()
    slot_queries = {slot: ru_slot_query(request, slot) for slot in target_slots}

    def _one(slot: str) -> list[ProductItem]:
        try:
            return provider.search(
                slot_queries[slot],
                SearchContext(
                    user_profile=profile,
                    limit=settings.avito_max_results,
                    categories=list(SLOT_ENGINE_CATEGORIES.get(slot, [])),
                ),
            )
        except Exception:
            return []

    fetched: list[ProductItem] = []
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="avito") as pool:
        futures = [pool.submit(_one, slot) for slot in target_slots]
        for future in futures:
            try:
                fetched.extend(future.result(timeout=settings.avito_timeout_sec + 4.0))
            except Exception:
                continue

    seen: set[str] = set()
    unique: list[ProductItem] = []
    for card in fetched:
        key = str(card.sku or card.id)
        if key in seen:
            continue
        seen.add(key)
        meta = card.meta if isinstance(card.meta, dict) else {}
        meta["feed"] = FEED_LIVE
        meta["link_kind"] = listing_url_kind(card.source_url)
        card.meta = meta
        unique.append(card)

    unique.extend(_top_up_with_snapshot(unique, request, target_slots, profile))
    _apply_appearance(unique, request, profile)
    # Порядок: сначала лучшее совпадение по словам и внешнему виду.
    unique.sort(
        key=lambda card: (
            -float((card.meta or {}).get("appearance", {}).get("score") or 0),
            -float((card.meta or {}).get("query_match") or (card.meta or {}).get("selection_score") or 0),
            card.id,
        )
    )
    return unique, [slot_queries[slot] for slot in target_slots]


def _fallback_catalog_as_avito(
    products: list[CatalogItem],
    request: LookRequest,
    reason: str,
) -> LookResult:
    """Резервный режим: подбор по каталогу, но ВСЕ ссылки — на Авито.

    Включается, только если живая выдача Авито пуста (сеть закрыта или блок).
    Образ собирается прежним ранжировщиком, а каждая карточка ведёт на
    подборку Авито по этой вещи — пустых выдач не бывает никогда.
    """
    result = ensure_avito_links(legacy_generate_look(products, request))
    profile = build_profile(request)
    diagnostics = dict(result.diagnostics or {})
    diagnostics["engine"] = {
        "pipeline": "legacy-ranker",
        "enabled": True,
        "runtime_mode": "avito-fallback",
        "fallback": "avito-unreachable",
        "fallback_reason": reason,
        "providers": ["avito"],
        "web_sources": ["avito"],
        "niche_level": profile.niche_level,
        "aesthetics": list(profile.aesthetics),
    }
    warnings = list(diagnostics.get("warnings") or [])
    warnings.append(reason)
    diagnostics["warnings"] = warnings
    result.diagnostics = diagnostics
    return result


def generate_look_avito(products: list[CatalogItem], request: LookRequest) -> LookResult:
    """Образ из живых объявлений Авито: поиск → интеллект → бюджет."""
    try:
        reference = prepare_pool(products, request)
    except LookGenerationError:
        raise LookGenerationError("Каталог пуст — не из чего собрать образ")

    plan_id = request.plan if request.plan in SLOT_PLANS else _plan_for_season(request.season, request.occasion)
    target_slots = [slot for slot in SLOT_PLANS[plan_id]["slots"]]
    # Пул собираем шире плана, чтобы у движка был выбор архитектуры образа
    # (например, «платье вместо верха с низом»).
    for extra in ("top", "bottom", "dress", "shoes"):
        if extra not in target_slots:
            target_slots.append(extra)

    raw_cards, slot_queries = _fetch_avito_pool(
        request, body=reference.body, palette=reference.palette, slots=target_slots
    )
    covered = {
        ENGINE_CATEGORY_TO_SLOT.get(str(card.category or "").lower(), "accessory") for card in raw_cards
    }
    live_cards = [card for card in raw_cards if feed_of(card) == FEED_LIVE]
    snapshot_cards = [card for card in raw_cards if feed_of(card) == FEED_SNAPSHOT]
    live_error = avito_provider().last_error
    snapshot = avito_snapshot_provider()
    snapshot_at = snapshot.captured_at.isoformat() if snapshot.captured_at else ""
    if len(raw_cards) < 3 or len(covered & set(target_slots)) < 2:
        # Ни живой выдачи, ни снимка реальных объявлений — только тогда прежний
        # каталог. Это последний резерв, и ссылки в нём честно помечены как
        # подборки Авито, а не как объявления.
        return _fallback_catalog_as_avito(
            products,
            request,
            "Объявления Авито недоступны"
            + (f" ({live_error})" if live_error else "")
            + " и снимок выдачи пуст — подобрали вещи по каталогу и дали ссылки на подборки Авито.",
        )

    profile = build_profile(request, palette=reference.palette, body=reference.body)
    engine = FashionEngine(
        providers=[avito_provider()],
        options=EngineOptions(
            max_products=settings.fashion_engine_max_products,
            limit_per_query=settings.avito_max_results,
            min_confidence=settings.fashion_engine_min_confidence,
        ),
    )
    enriched = engine.enrich(raw_cards, profile)
    # Оценка движка (вкус, ниша, архитектура) складывается с оценкой внешнего
    # вида конкретной вещи: оттенок, фактура, силуэт, состояние и фото.
    _rate_appearance(enriched, request, profile, with_photos=False)
    enriched.sort(key=lambda card: (-float(card.fashion_score or 0), card.id))
    products_capped = enriched[: settings.fashion_engine_max_products]
    for card in products_capped:
        if not card.provider:
            card.provider = "avito"
    discovery = DiscoveryResult(
        products=products_capped,
        references=[],
        queries_used=slot_queries,
        raw_items=len(raw_cards),
        considered=len(raw_cards),
        dropped={"antigeneric": 0, "confidence": 0, "budget": 0, "duplicates": 0},
    )
    main_query = build_engine_query(request, palette=reference.palette, body=reference.body)
    outfit = engine.create_outfit(main_query, profile, preloaded=discovery)
    if not outfit.items:
        return _fallback_catalog_as_avito(
            products,
            request,
            "Объявления Авито не прошли отбор движка — подобрали вещи и дали ссылки на Авито.",
        )
    feed_notes: list[str] = []
    if live_cards:
        feed_notes.append(f"живых объявлений Авито в пуле: {len(live_cards)}")
    if snapshot_cards:
        note = f"объявлений из снимка выдачи: {len(snapshot_cards)}"
        if snapshot_at:
            note += f" (снимок от {snapshot_at})"
        feed_notes.append(note)
    if live_error and live_cards:
        feed_notes.append(f"часть запросов Авито отдала не полностью: {live_error}")

    run = EngineRun(
        query=main_query,
        profile=profile,
        discovery=discovery,
        outfit=outfit,
        cards={card.sku or card.id: card for card in products_capped},
        providers=["avito"],
        feeds={FEED_LIVE: len(live_cards), FEED_SNAPSHOT: len(snapshot_cards)},
        feed_notes=feed_notes,
        live_error=live_error,
        snapshot_captured_at=snapshot_at,
    )

    avito_pool = [avito_card_to_catalog_item(card, request, index) for index, card in enumerate(products_capped)]
    try:
        prepared = prepare_pool(avito_pool, request)
    except LookGenerationError as exc:
        return _fallback_catalog_as_avito(
            products, request, f"Объявления Авито не прошли отбор ({exc}) — подобрали вещи и дали ссылки на Авито."
        )
    try:
        return _assemble_look(prepared, request, run)
    except LookGenerationError:
        return _fallback_catalog_as_avito(
            products, request, "Из объявлений Авито не сложился полный образ — подобрали вещи и дали ссылки на Авито."
        )


def _listing_block(card: ProductItem | None, item: CatalogItem) -> dict[str, Any]:
    """Паспорт конкретного объявления для карточки вещи в интерфейсе."""
    meta = dict(card.meta or {}) if card is not None else {}
    traits = dict(meta.get("traits") or {})
    appearance = dict(meta.get("appearance") or {})
    photo = dict(meta.get("photo_traits") or {})
    feed = meta.get("feed") or ("snapshot" if meta.get("snapshot") else "live")
    return {
        "kind": meta.get("link_kind") or listing_url_kind(item.url),
        "feed": feed,
        "avito_id": str(meta.get("avito_id") or ""),
        "city": str(meta.get("city") or ""),
        "condition": str(meta.get("condition") or traits.get("condition") or ""),
        "sizes": list(meta.get("sizes") or traits.get("sizes") or []),
        "captured_at": str(meta.get("captured_at") or meta.get("snapshot_captured_at") or ""),
        "appearance_score": round(float(appearance.get("score") or 0.0), 3),
        "appearance_components": dict(appearance.get("components") or {}),
        "photo_analyzed": bool(photo),
        "colors_hex": list(photo.get("colors_hex") or []),
    }


def _assemble_look(prepared: PreparedPool, request: LookRequest, run: EngineRun) -> LookResult:
    """Сборка образа из пула приложения и прогона движка.

    Единый финал для каталожного и авито-режимов: кандидаты по слотам в
    порядке движка → бюджетный оптимизатор → карточки с объяснениями.
    """
    if not run.outfit.items:
        reason = (run.outfit.critic_feedback or ["не нашлось достаточно вещей"])[0]
        raise LookGenerationError(f"Образ не удалось собрать: {reason}")

    plan_slots = prepared.plan["slots"]
    roles = {card.sku or card.id: card.role for card in run.outfit.items}

    # Кандидаты по слотам в порядке движка: Fashion Score, место в его образе и
    # релевантность запросу. Вещи из образа движка получают приоритет — дальше
    # бюджетный оптимизатор приложения доводит состав до лимита и добирает
    # обязательные слоты, не выходя за бюджет.
    slot_candidates: dict[str, list[ScoredItem]] = {}
    for slot, pool in prepared.candidates_by_slot.items():
        enriched: list[ScoredItem] = []
        for scored in pool:
            breakdown = score_item(scored.item, prepared.ctx).breakdown
            blended = _blended_score(
                scored.score,
                run.cards.get(scored.sku),
                run.rank_index(scored.sku),
                len(run.discovery.products),
            )
            if scored.sku in roles:
                blended = min(1.0, round(blended + ENGINE_OUTFIT_BONUS, 4))
            enriched.append(ScoredItem(item=scored.item, score=blended, breakdown=breakdown))
        enriched.sort(key=lambda s: (-s.score, s.item.price_rub, s.item.sku))
        slot_candidates[slot] = enriched

    draft = build_look(slot_candidates, plan_slots, request.budget_rub)
    if len(draft.picked) < 3:
        raise LookGenerationError(
            "Образ не удалось собрать: после бюджетной страховки осталось меньше трёх вещей"
        )

    chosen: dict[str, tuple[ScoredItem, ProductItem | None]] = {
        slot: (scored, run.cards.get(scored.sku)) for slot, scored in draft.picked.items()
    }
    engine_kept = sum(1 for scored, _card in chosen.values() if scored.sku in roles)
    repair: str | None = None if engine_kept == len(chosen) else "budget-optimiser"
    budget_info: dict[str, Any] = {
        "total_rub": draft.total_rub,
        "budget_rub": draft.budget_rub,
        "over_budget": draft.over_budget,
        "dropped_slots": list(draft.dropped_slots),
        "warnings": list(draft.warnings),
        "budget_utilization": round(draft.total_rub / draft.budget_rub, 3) if draft.budget_rub else 0.0,
        "engine_outfit_items": len(run.outfit.items),
        "engine_outfit_kept": engine_kept,
    }

    slot_order = {slot: spec.get("order", 9) for slot, spec in plan_slots.items()}
    ordered = sorted(chosen.items(), key=lambda pair: (slot_order.get(pair[0], 9), pair[0]))

    taken = {scored.sku for scored, _card in chosen.values()}
    ctx_info = {
        "style": request.style,
        "mood": request.mood,
        "palette_label": prepared.palette.season_label,
        "silhouette_ru": prepared.body.silhouette_ru,
    }

    items_payload: list[dict[str, Any]] = []
    for index, (slot, (scored, card)) in enumerate(ordered):
        in_engine_outfit = scored.sku in roles
        role = roles.get(scored.sku)
        meta = _engine_item_meta(card, slot, role=role, in_engine_outfit=in_engine_outfit)
        card_meta = card.meta if card is not None and isinstance(card.meta, dict) else {}
        # Адрес вещи: конкретное объявление (прямая ссылка + фото) и откуда оно
        # взялось — живая выдача или снимок. Эти поля переживают сохранение в БД.
        meta["feed"] = card_meta.get("feed") or ("snapshot" if card_meta.get("snapshot") else "live")
        meta["link_kind"] = card_meta.get("link_kind") or listing_url_kind(scored.item.url)
        meta["listing"] = _listing_block(card, scored.item)
        breakdown: dict[str, Any] = dict(scored.breakdown)
        breakdown["engineAttributes"] = meta
        if meta.get("fashion_score"):
            breakdown["engine"] = round(meta["fashion_score"] / 100, 3)
            breakdown["trend"] = meta.get("trend_relevance", 0.4)
            breakdown["uniqueness"] = meta.get("uniqueness", 0.5)
        card_meta = card.meta if card is not None and isinstance(card.meta, dict) else {}
        reasons = (
            _engine_reasons(card, run, role=role)
            # Что видно на фото и в описании объявления: оттенок, фактура,
            # силуэт, состояние — чтобы выбор вещи был объяснён, а не «так решил ИИ».
            + [str(note) for note in (card_meta.get("appearance_reasons") or [])]
            + item_reasons(scored, ctx_info)
        )
        unique_reasons: list[str] = []
        for reason in reasons:
            if reason not in unique_reasons:
                unique_reasons.append(reason)
        items_payload.append(
            {
                "position": index,
                "slot": slot,
                "slot_label": SLOT_LABELS.get(slot, slot),
                "sku": scored.sku,
                "category": scored.item.category,
                "name": scored.item.name,
                "brand": scored.item.brand,
                "price_rub": scored.item.price_rub,
                "url": scored.item.url,
                "image_url": scored.item.image_url,
                "colors": scored.item.colors,
                "color_hexes": scored.item.color_hexes,
                "fit": scored.item.fit,
                "score": scored.score,
                "breakdown": breakdown,
                # Метаданные движка доступны и напрямую (UI), и внутри
                # breakdown (persistence в LookItem.breakdown_json).
                "engine": meta,
                "reasons": unique_reasons[:5],
                "verification_status": scored.item.verification_status,
                "verification_score": round(scored.item.verification_score, 3),
                "source": scored.item.source,
                # Конкретное объявление: живое или из снимка выдачи, но всегда
                # с прямой ссылкой, фото и ценой именно этой вещи.
                "feed": meta.get("feed"),
                "link_kind": meta.get("link_kind"),
                "listing": meta.get("listing"),
                "alternatives": _alternatives(prepared, run, slot, taken),
            }
        )

    chosen_scored = {slot: scored for slot, (scored, _card) in ordered}
    cohesion = look_cohesion(list(chosen_scored.values()), prepared.ctx)
    app_score = look_score(list(chosen_scored.values()), cohesion)
    weight = max(0.0, min(1.0, float(settings.fashion_engine_score_weight)))
    engine_score = float(run.outfit.outfit_score or 0)
    final_score = round((1 - weight) * app_score + weight * engine_score, 1)
    verdict = style_verdict(final_score)

    tips = look_tips(list(prepared.body.tips), prepared.palette.to_dict(), request.style, chosen_scored)
    tips = list(dict.fromkeys(tips + _engine_tips(run)))[:7]

    thesis_ru = engine_keywords.thesis_label_ru(run.outfit.styling_thesis)
    summary = look_summary(
        request.style,
        request.mood,
        request.occasion,
        budget_info["total_rub"],
        request.budget_rub,
        chosen_scored,
        final_score,
    )
    if thesis_ru:
        summary = f"«{thesis_ru}» · оценка {engine_score:.0f}/100. {summary}"

    engine_block = _engine_block(run, app_score=app_score, final_score=final_score, repair=repair)

    diagnostics = {
        "plan": prepared.plan_id,
        "plan_description": prepared.plan["description"],
        "candidates_total": len(prepared.ranked),
        "rejected_total": len(prepared.rejected),
        "rejected_sample": prepared.rejected[:10],
        "dropped_slots": budget_info["dropped_slots"],
        "warnings": budget_info["warnings"],
        "budget": budget_info,
        "weights": prepared.ctx.weights,
        "excluded_skus": request.exclude_skus,
        "engine": engine_block,
    }

    return LookResult(
        items=items_payload,
        total_rub=budget_info["total_rub"],
        budget_rub=request.budget_rub,
        score=final_score,
        verdict=verdict,
        cohesion=cohesion,
        summary=summary,
        tips=tips,
        body=prepared.body,
        palette=prepared.palette,
        plan=prepared.plan_id,
        diagnostics=diagnostics,
        personal_note=personal_note(
            style=request.style,
            mood=request.mood,
            occasion=request.occasion,
            palette=prepared.palette,
            body=prepared.body,
            picked=chosen_scored,
            total_rub=budget_info["total_rub"],
            budget_rub=request.budget_rub,
        ),
    )


def _engine_outfit_skus(look: Any) -> set[str]:
    """SKU вещей, которые движок выбрал в образ (из сохранённого ``ranking_json``)."""
    raw = getattr(look, "ranking_json", None)
    if not raw:
        return set()
    try:
        ranking = look.loads(raw, {}) if hasattr(look, "loads") else json.loads(raw)
    except Exception:  # сохранённый образ мог быть записан прошлой версией
        return set()
    if not isinstance(ranking, dict):
        return set()
    engine = ranking.get("engine")
    roles = engine.get("roles") if isinstance(engine, dict) else None
    if isinstance(roles, dict):
        return {str(sku) for sku in roles}
    return set()


def rerank_for_slot_avito(
    slot: str,
    *,
    look: Any,
    ctx: RankingContext,
) -> list[ScoredItem]:
    """Замены для слота — свежие объявления Авито, отсортированные движком."""
    request = _request_from_look(look)
    profile = build_profile(request, palette=ctx.palette, body=ctx.body)
    query = f"{request.query or ''} {SLOT_QUERY_HINTS.get(slot, slot)}".strip()
    try:
        cards = avito_provider().search(
            query,
            SearchContext(
                user_profile=profile,
                limit=max(8, settings.avito_max_results),
                categories=list(SLOT_ENGINE_CATEGORIES.get(slot, [])),
            ),
        )
    except Exception:
        cards = []
    # Только честные попадания в слот: категория объявления должна совпасть.
    cards = [
        card
        for card in cards
        if ENGINE_CATEGORY_TO_SLOT.get(str(card.category or "").lower(), "accessory") == slot
    ]
    # Мало живых объявлений (или сайт закрыт капчей) — добираем реальными
    # объявлениями из снимка выдачи, чтобы замена была конкретной вещью.
    if len(cards) < max(4, settings.avito_max_results // 2):
        taken = {str(card.sku or card.id) for card in cards}
        cards.extend(
            _snapshot_cards_for_slot(
                request,
                slot,
                profile,
                limit=max(4, settings.avito_max_results - len(cards)),
                exclude=taken,
            )
        )
    if not cards:
        return []
    _apply_appearance(cards, request, profile)
    engine = FashionEngine(
        providers=[avito_provider()],
        options=EngineOptions(
            max_products=max(12, len(cards)),
            limit_per_query=4,
            min_confidence=settings.fashion_engine_min_confidence,
        ),
    )
    engine.enrich(cards, profile)
    for card in cards:
        if not card.provider:
            card.provider = "avito"
    order = {card.sku or card.id: index for index, card in enumerate(cards)}
    total = max(1, len(cards))
    enriched: list[ScoredItem] = []
    for index, card in enumerate(cards):
        item = avito_card_to_catalog_item(card, request, index)
        app_scored = score_item(item, ctx)
        breakdown: dict[str, Any] = dict(app_scored.breakdown)
        breakdown["engine"] = round(float(card.fashion_score or 0) / 100, 3)
        breakdown["engineAttributes"] = _engine_item_meta(card, slot)
        breakdown["engineOutfit"] = False
        enriched.append(
            ScoredItem(
                item=item,
                score=_blended_score(app_scored.score, card, order.get(card.sku or card.id), total),
                breakdown=breakdown,
            )
        )
    enriched.sort(key=lambda s: (-s.score, s.item.price_rub, s.item.sku))
    return enriched


def rerank_for_slot(
    ranked: list[ScoredItem],
    slot: str,
    *,
    look: Any,
    ctx: RankingContext,
) -> list[ScoredItem]:
    """Переставить кандидатов слота по релевантности движка (для «Заменить»)."""
    if settings.avito_enabled:
        try:
            live = rerank_for_slot_avito(slot, look=look, ctx=ctx)
        except Exception:
            live = []
        if live:
            return live
    request = _request_from_look(look)
    profile = build_profile(request, palette=ctx.palette, body=ctx.body)
    query = build_engine_query(
        request,
        palette=ctx.palette,
        body=ctx.body,
        extra=SLOT_QUERY_HINTS.get(slot, slot),
    )
    cards = [to_engine_card(scored.item) for scored in ranked]
    providers = _providers(cards, min_score=0.0)
    engine = FashionEngine(
        providers=providers,
        options=EngineOptions(
            max_products=max(12, min(len(cards), settings.fashion_engine_max_products)),
            limit_per_query=4,
            min_confidence=settings.fashion_engine_min_confidence,
        ),
    )
    discovery = engine.discover(query, profile)
    # Слот показывается целиком: вещи вне пула запросов тоже должны получить
    # атрибуты, fashion score и taste-категорию движка.
    engine.enrich(cards, profile)
    # Вещи, которые движок выбрал в образ при генерации: их видно в сохранённом
    # образе, поэтому замена слота не должна предлагать им на замену случайную
    # позицию из шортлиста. Пул одного слота целого образа не образует, поэтому
    # роли берём из самого образа (ranking_json → engine.roles).
    chosen = _engine_outfit_skus(look)
    order = {card.sku or card.id: index for index, card in enumerate(discovery.products)}
    total = max(1, len(discovery.products))
    cards_by_sku = {card.sku or card.id: card for card in cards}

    enriched: list[ScoredItem] = []
    for scored in ranked:
        card = cards_by_sku.get(scored.sku)
        breakdown: dict[str, Any] = dict(scored.breakdown)
        if card is not None and card.fashion_attributes is not None:
            breakdown["engine"] = round(float(card.fashion_score or 0) / 100, 3)
            breakdown["engineAttributes"] = _engine_item_meta(card, slot)
        blended = _blended_score(scored.score, card, order.get(scored.sku), total)
        in_engine_outfit = scored.sku in chosen
        if in_engine_outfit:
            blended = min(1.0, round(blended + ENGINE_OUTFIT_BONUS, 4))
        breakdown["engineOutfit"] = in_engine_outfit
        enriched.append(ScoredItem(item=scored.item, score=blended, breakdown=breakdown))
    # Вещь, которую движок выбрал в этот слот, идёт первой: пользователь видит
    # её в образе, остальные — альтернативы в порядке движка.
    enriched.sort(key=lambda s: (not s.breakdown.get("engineOutfit"), -s.score, s.item.price_rub, s.item.sku))
    return enriched


# ─── поиск (для экрана «Поиск» и API движка) ────────────────────────────────


#: Человекочитаемая пометка источника для позиций не из каталога приложения.
SOURCE_LABELS_RU: dict[str, str] = {
    "avito": "Авито",
    "web-search": "онлайн-находка",
    "mock-real-catalog": "архетипный дизайнер",
    "partner-feed": "партнёрский магазин",
}


def _external_item_payload(card: ProductItem, run: EngineRun) -> dict[str, Any] | None:
    """Карточка живой/справочной находки для выдачи поиска.

    Это реальные вещи из интернета/справочника архетипов: у них есть ссылка,
    фото и цена, но они не проходили слой верификации asStylist — поэтому у
    них особый статус и они не попадают в образ, только в поисковую выдачу.
    """
    if not card.source_url:
        return None
    sku = card.sku or card.id
    if (card.currency or "RUB").upper() == "RUB":
        price_rub = float(card.price or 0)
        price_note = ""
    else:
        price_rub = settings.to_rub(float(card.price or 0), card.currency or "EUR")
        if price_rub is None:
            return None
        price_note = f"{card.price:g} {card.currency}"
    slot = ENGINE_CATEGORY_TO_SLOT.get(str(card.category or "").lower(), "accessory")
    meta = _engine_item_meta(card, slot)
    source_label = SOURCE_LABELS_RU.get(card.provider or card.source_type, card.provider or card.source_type)
    reasons = _engine_reasons(card, run, limit=2)
    reasons.append(f"Источник: {source_label} · {str((card.meta or {}).get('source_domain') or 'внешний каталог')}")
    return {
        "sku": sku,
        "name": card.name,
        "brand": card.brand,
        "category": card.category,
        "slot": slot,
        "slot_label": SLOT_LABELS.get(slot, slot),
        "price_rub": price_rub,
        "price_note": price_note,
        "url": card.source_url,
        "image_url": card.image or "",
        "colors": [card.color] if card.color else [],
        "color_hexes": [],
        "score": _search_position(0.5, card, run.rank_index(sku), len(run.discovery.products)),
        "engine": meta,
        "reasons": reasons[:4],
        "verification_status": "external",
        "verification_score": round(float(card.confidence or 0.6), 3),
        "source": card.provider or card.source_type,
    }


def _snapshot_search_items(
    request: LookRequest,
    prepared: PreparedPool,
    *,
    query: str,
    limit: int,
) -> list[dict[str, Any]]:
    """Реальные объявления из снимка выдачи для экрана «Поиск вещей»."""
    if not settings.avito_snapshot_enabled:
        return []
    provider = avito_snapshot_provider()
    profile = build_profile(request, palette=prepared.palette, body=prepared.body)
    try:
        cards = provider.search(
            query,
            SearchContext(user_profile=profile, limit=max(limit * 2, 8)),
        )
    except Exception:
        return []
    if not cards:
        return []
    _apply_appearance(cards, request, profile)
    cards.sort(
        key=lambda card: (
            -float((card.meta or {}).get("selection_score") or 0.0),
            -float((card.meta or {}).get("appearance", {}).get("score") or 0.0),
            card.id,
        )
    )
    captured = provider.captured_at.isoformat() if provider.captured_at else ""
    ctx_info = {
        "style": request.style,
        "mood": request.mood,
        "palette_label": prepared.palette.season_label,
        "silhouette_ru": prepared.body.silhouette_ru,
    }
    items: list[dict[str, Any]] = []
    for index, card in enumerate(cards[: max(1, limit)]):
        catalog_item = avito_card_to_catalog_item(card, request, index)
        app_scored = score_item(catalog_item, prepared.ctx)
        slot = ENGINE_CATEGORY_TO_SLOT.get(str(card.category or "").lower(), "accessory")
        meta = _engine_item_meta(card, slot)
        head = "Реальное объявление Авито с фото, ценой и ссылкой"
        if captured:
            head += f" (снимок выдачи от {captured})"
        reasons = (
            [head + "."]
            + [str(note) for note in ((card.meta or {}).get("appearance_reasons") or [])]
            + item_reasons(app_scored, ctx_info, limit=2)
        )
        items.append(
            {
                "sku": catalog_item.sku,
                "name": catalog_item.name,
                "brand": catalog_item.brand,
                "category": catalog_item.category,
                "slot": slot,
                "slot_label": SLOT_LABELS.get(slot, slot),
                "price_rub": catalog_item.price_rub,
                "price_note": "",
                "url": catalog_item.url,
                "image_url": catalog_item.image_url,
                "colors": list(catalog_item.colors),
                "color_hexes": list(catalog_item.color_hexes),
                "score": round(float(app_scored.score), 4),
                "engine": meta,
                "reasons": list(dict.fromkeys(reasons))[:5],
                "verification_status": "verified",
                "verification_score": round(float(card.confidence or 0.7), 3),
                "source": "avito",
                "feed": FEED_SNAPSHOT,
                "link_kind": "listing",
                "listing": _listing_block(card, catalog_item),
            }
        )
    return items


def search_avito(
    request: LookRequest,
    prepared: PreparedPool,
    *,
    query: str,
    limit: int = 8,
) -> dict[str, Any]:
    """Свободный поиск вещей движком — только по объявлениям Авито.

    Живая выдача: название, цена, ссылка и фото каждого объявления. Если Авито
    недоступен — резервный режим: подбор по каталогу, но все ссылки ведут на
    соответствующие подборки Авито.
    """
    run = run_engine(prepared, request, live=True)
    # Сначала вещи с максимальным совпадением по запросу, затем — по вкусу:
    # иначе разные запросы давали бы одну и ту же выдачу.
    discovered = sorted(
        run.discovery.products,
        key=lambda card: (
            -_query_relevance(card),
            -float(card.fashion_score or 0),
            card.id,
        ),
    )[: max(1, limit)]

    ctx_info = {
        "style": request.style,
        "mood": request.mood,
        "palette_label": prepared.palette.season_label,
        "silhouette_ru": prepared.body.silhouette_ru,
    }
    items: list[dict[str, Any]] = []
    for index, card in enumerate(discovered):
        if not card.source_url or not (card.price or 0) > 0:
            continue
        catalog_item = avito_card_to_catalog_item(card, request, index)
        app_scored = score_item(catalog_item, prepared.ctx)
        slot = ENGINE_CATEGORY_TO_SLOT.get(str(card.category or "").lower(), "accessory")
        meta = _engine_item_meta(card, slot)
        reasons = (
            _engine_reasons(card, run, limit=3)
            + item_reasons(app_scored, ctx_info, limit=2)
            + ["Найдено на Авито — живое объявление с фото и ценой."]
        )
        items.append(
            {
                "sku": catalog_item.sku,
                "name": catalog_item.name,
                "brand": catalog_item.brand,
                "category": catalog_item.category,
                "slot": slot,
                "slot_label": SLOT_LABELS.get(slot, slot),
                "price_rub": catalog_item.price_rub,
                "price_note": "",
                "url": catalog_item.url,
                "image_url": catalog_item.image_url,
                "colors": list(catalog_item.colors),
                "color_hexes": list(catalog_item.color_hexes),
                "score": _search_position(
                    app_scored.score, card, run.rank_index(card.sku or card.id), len(run.discovery.products)
                ),
                "engine": meta,
                "reasons": list(dict.fromkeys(reasons))[:5],
                "verification_status": "verified",
                "verification_score": round(float(card.confidence or 0.7), 3),
                "source": "avito",
                "feed": feed_of(card),
                "link_kind": (card.meta or {}).get("link_kind") or listing_url_kind(card.source_url),
                "listing": _listing_block(card, catalog_item),
            }
        )

    fallback = None
    fallback_reason = None
    if not items:
        # Живая выдача не дала результата — показываем реальные объявления из
        # снимка выдачи. Это по-прежнему конкретные вещи с фото, ценой и
        # ссылкой на объявление, просто найденные раньше.
        items = _snapshot_search_items(request, prepared, query=query, limit=limit)
        if items:
            fallback = "avito-snapshot"
            fallback_reason = avito_provider().last_error or "живая выдача Авито пуста"
    if not items:
        fallback = "avito-unreachable"
        fallback_reason = avito_provider().last_error or "живая выдача Авито пуста"
        provider = avito_provider()
        for scored in prepared.ranked[: max(1, limit)]:
            slot = slot_for_item(scored.item, APP_CATEGORY_TO_ENGINE.get(scored.item.category))
            app_scored = score_item(scored.item, prepared.ctx)
            items.append(
                {
                    "sku": scored.sku,
                    "name": scored.item.name,
                    "brand": scored.item.brand,
                    "category": scored.item.category,
                    "slot": slot,
                    "slot_label": SLOT_LABELS.get(slot, slot),
                    "price_rub": scored.item.price_rub,
                    "price_note": "",
                    "url": provider.search_url_for(f"{scored.item.brand} {scored.item.name}"),
                    "image_url": scored.item.image_url,
                    "colors": list(scored.item.colors),
                    "color_hexes": list(scored.item.color_hexes),
                    "score": round(app_scored.score, 4),
                    "engine": {},
                    "reasons": item_reasons(app_scored, ctx_info)
                    + ["Ссылка ведёт на подборку Авито по этой вещи — там живые объявления с фото и ценами."],
                    "verification_status": scored.item.verification_status,
                    "verification_score": round(scored.item.verification_score, 3),
                    "source": "avito",
                    # Последний резерв: это не объявление, а подборка Авито.
                    "feed": "search",
                    "link_kind": "search",
                    "listing": _listing_block(None, scored.item),
                }
            )

    total = round(sum(item["price_rub"] for item in items), 2)
    theses = engine_keywords.THESIS_LABELS_RU
    thesis = run.outfit.styling_thesis
    return {
        "query": query,
        "engine": {
            "pipeline": PIPELINE,
            "engine_version": str((run.outfit.meta or {}).get("engineVersion", "")),
            "styling_thesis": thesis,
            "styling_thesis_ru": engine_keywords.thesis_label_ru(thesis),
            "aesthetic": run.outfit.aesthetic,
            "aesthetic_ru": aesthetic_ru(run),
            "outfit_score": round(float(run.outfit.outfit_score or 0), 1),
            "styling_logic": run.outfit.styling_logic,
            "critic_decision": run.outfit.critic_decision,
            "critic_feedback": _critic_ru(run.outfit.critic_feedback),
            "queries_used": list((run.outfit.meta or {}).get("queriesUsed") or run.discovery.queries_used[:8]),
            "queries_total": len(run.discovery.queries_used),
            "candidates": {
                "raw_items": run.discovery.raw_items,
                "considered": len(run.discovery.products),
                "validated": len(run.discovery.products),
                "dropped": dict(run.discovery.dropped),
            },
            "niche_level": run.profile.niche_level,
            "aesthetics": list(run.profile.aesthetics),
            "profile": run.profile.to_dict(),
            "taste_mix": _taste_mix(run),
            "alternatives": list(run.outfit.alternatives),
            "fallback": fallback,
            "fallback_reason": fallback_reason,
            "providers": ["avito"],
            "web_sources": ["avito"],
            # Откуда пришли вещи: живая выдача или снимок реальных объявлений.
            "feeds": dict(run.feeds),
            "feed_notes": list(run.feed_notes),
            "live_error": run.live_error,
            "snapshot_captured_at": run.snapshot_captured_at,
        },
        "thesis_options": [theses.get(name, name) for name in (run.outfit.meta or {}).get("theses", [])],
        "items": items,
        "total_rub": total,
        "budget_rub": request.budget_rub,
        "suggested_request": {
            "query": query,
            "style": request.style,
            "mood": request.mood,
            "occasion": request.occasion,
            "season": request.season,
            "presentation": request.presentation,
            "budget_rub": request.budget_rub,
            "height_cm": request.height_cm,
            "weight_kg": request.weight_kg,
            "niche_level": run.profile.niche_level,
        },
    }


def search(
    payload: dict[str, Any],
    products: list[CatalogItem],
    *,
    limit: int = 8,
) -> dict[str, Any]:
    """Свободный текстовый поиск вещей по движку (без сохранения образа)."""
    query = str(payload.get("query") or "").strip()
    if len(query) < 2:
        raise LookGenerationError("Нужен текстовый запрос длиной от 2 символов")

    request = LookRequest(
        style=str(payload.get("style") or "minimal"),
        mood=str(payload.get("mood") or "calm"),
        occasion=str(payload.get("occasion") or "everyday"),
        season=str(payload.get("season") or "all"),
        presentation=str(payload.get("presentation") or "unisex"),
        height_cm=float(payload.get("height_cm") or 172),
        weight_kg=float(payload.get("weight_kg") or 68),
        budget_rub=float(payload.get("budget_rub") or settings.budget_max_rub),
        preferred_colors=list(payload.get("preferred_colors") or []),
        avoid_colors=list(payload.get("avoid_colors") or []),
        size=payload.get("size"),
        query=query,
        niche_level=payload.get("niche_level"),
        weights=settings.resolved_ranking_weights(),
    )
    prepared = prepare_pool(products, request)
    if settings.avito_enabled:
        return search_avito(request, prepared, query=query, limit=limit)
    run = run_engine(prepared, request, include_external=True, live=False)
    run_providers = run.providers
    web = _web_provider()
    web_sources = web.configured_sources() if web is not None else []

    theses = engine_keywords.THESIS_LABELS_RU
    thesis = run.outfit.styling_thesis
    cards = run.cards
    # Сначала вещи, которые провайдер отметил как совпадение по запросу, затем
    # остальной проверенный пул: иначе разные запросы давали бы одну выдачу.
    discovered = sorted(
        run.discovery.products,
        key=lambda card: (
            -_query_relevance(card),
            -float(card.fashion_score or 0),
            card.id,
        ),
    )[: max(1, limit)]
    by_sku = {scored.sku: scored for scored in prepared.ranked}

    items: list[dict[str, Any]] = []
    for card in discovered:
        sku = card.sku or card.id
        scored = by_sku.get(sku)
        if scored is None:
            # Живые находки и справочные архетипы: не из каталога приложения.
            external = _external_item_payload(card, run)
            if external is not None:
                items.append(external)
            continue
        slot = slot_for_item(scored.item, card.category)
        meta = _engine_item_meta(card, slot)
        app_scored = score_item(scored.item, prepared.ctx)
        items.append(
            {
                "sku": sku,
                "name": scored.item.name,
                "brand": scored.item.brand,
                "category": scored.item.category,
                "slot": slot,
                "slot_label": SLOT_LABELS.get(slot, slot),
                "price_rub": scored.item.price_rub,
                "price_note": "",
                "url": scored.item.url,
                "image_url": scored.item.image_url,
                "colors": list(scored.item.colors),
                "color_hexes": list(scored.item.color_hexes),
                "score": _search_position(
                    app_scored.score, card, run.rank_index(sku), len(run.discovery.products)
                ),
                "engine": meta,
                "reasons": _engine_reasons(card, run, limit=3)
                + item_reasons(
                    app_scored,
                    {
                        "style": request.style,
                        "mood": request.mood,
                        "palette_label": prepared.palette.season_label,
                        "silhouette_ru": prepared.body.silhouette_ru,
                    },
                    limit=2,
                ),
                "verification_status": scored.item.verification_status,
                "verification_score": round(scored.item.verification_score, 3),
                "source": scored.item.source,
            }
        )

    fallback = None
    if not items:
        fallback = "engine-empty"
        for scored in prepared.ranked[: max(1, limit)]:
            slot = slot_for_item(scored.item, APP_CATEGORY_TO_ENGINE.get(scored.item.category))
            items.append(
                {
                    "sku": scored.sku,
                    "name": scored.item.name,
                    "brand": scored.item.brand,
                    "category": scored.item.category,
                    "slot": slot,
                    "slot_label": SLOT_LABELS.get(slot, slot),
                    "price_rub": scored.item.price_rub,
                    "price_note": "",
                    "url": scored.item.url,
                    "image_url": scored.item.image_url,
                    "colors": list(scored.item.colors),
                    "color_hexes": list(scored.item.color_hexes),
                    "score": scored.score,
                    "engine": {},
                    "reasons": item_reasons(
                        scored,
                        {
                            "style": request.style,
                            "mood": request.mood,
                            "palette_label": prepared.palette.season_label,
                            "silhouette_ru": prepared.body.silhouette_ru,
                        },
                    ),
                    "verification_status": scored.item.verification_status,
                    "verification_score": round(scored.item.verification_score, 3),
                }
            )

    total = round(sum(item["price_rub"] for item in items), 2)
    return {
        "query": query,
        "engine": {
            "pipeline": PIPELINE,
            "engine_version": str((run.outfit.meta or {}).get("engineVersion", "")),
            "styling_thesis": thesis,
            "styling_thesis_ru": engine_keywords.thesis_label_ru(thesis),
            "aesthetic": run.outfit.aesthetic,
        "aesthetic_ru": aesthetic_ru(run),
            "outfit_score": round(float(run.outfit.outfit_score or 0), 1),
            "styling_logic": run.outfit.styling_logic,
            "critic_decision": run.outfit.critic_decision,
            "critic_feedback": _critic_ru(run.outfit.critic_feedback),
            "queries_used": list((run.outfit.meta or {}).get("queriesUsed") or run.discovery.queries_used[:8]),
            "queries_total": len(run.discovery.queries_used),
            "candidates": {
                "raw_items": run.discovery.raw_items,
                "considered": run.discovery.considered,
                "validated": len(run.discovery.products),
                "dropped": dict(run.discovery.dropped),
            },
            "niche_level": run.profile.niche_level,
            "aesthetics": list(run.profile.aesthetics),
            "profile": run.profile.to_dict(),
            "taste_mix": _taste_mix(run),
            "alternatives": list(run.outfit.alternatives),
            "fallback": fallback,
            "providers": list(run_providers),
            "web_sources": web_sources,
        },
        "thesis_options": [theses.get(name, name) for name in (run.outfit.meta or {}).get("theses", [])],
        "items": items,
        "total_rub": total,
        "budget_rub": request.budget_rub,
        "suggested_request": {
            "query": query,
            "style": request.style,
            "mood": request.mood,
            "occasion": request.occasion,
            "season": request.season,
            "presentation": request.presentation,
            "budget_rub": request.budget_rub,
            "height_cm": request.height_cm,
            "weight_kg": request.weight_kg,
            "niche_level": run.profile.niche_level,
        },
    }

__all__ = [
    "APP_CATEGORY_TO_ENGINE",
    "APP_COLOR_TO_ENGINE",
    "BRAND_TIERS",
    "ENGINE_CATEGORY_TO_SLOT",
    "ENGINE_TO_APP_CATEGORY",
    "EngineRun",
    "MOOD_ENGINE",
    "OCCASION_ENGINE",
    "PIPELINE",
    "STYLE_ENGINE",
    "avito_card_to_catalog_item",
    "avito_provider",
    "brand_tier",
    "build_engine_query",
    "build_profile",
    "ensure_avito_links",
    "generate_look",
    "generate_look_avito",
    "is_avito_url",
    "rerank_for_slot",
    "rerank_for_slot_avito",
    "reset_avito_provider",
    "ru_slot_query",
    "run_engine",
    "search",
    "search_avito",
    "slot_for_item",
    "to_engine_card",
]
