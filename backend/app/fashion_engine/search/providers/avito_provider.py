"""AvitoSearchProvider — поиск реальных вещей только на Авито.

Единственный источник товаров asStylist: каждая позиция выдачи — живое
объявление Авито с названием, ценой в рублях, ссылкой и фотографией.

Как устроен подбор (по требованию «движок подбирает по ключевым словам,
названиям, анализу фото и описания»):

* **ключевые слова** — запрос движка (часто на английском: ``archive sheer
  top``) переводится в русские термины через ``lexicon.EN_TO_RU`` и словарь
  одежды; совпадения ищутся по стеммам (``lexicon.matches_token``), поэтому
  «шерстяное», «шерстяной» и «шерсть» — одно и то же;
* **названия** — вес попадания в заголовок объявления выше, чем в описание;
  точная фраза и соседние слова дают дополнительный бонус;
* **описание** — анализируется богатство текста (материалы, цвета, размер,
  состояние): подробные объявления с характеристиками ранжируются выше;
* **фото** — наличие снимка обязательно для высокого места в выдаче;
  дополнительно учитываются признаки «настоящего» фото с CDN Авито.

Надёжность (провайдер никогда не роняет пайплайн):

* любой сетевой сбой, блокировка или непонятная вёрстка → пустой список,
  движок продолжает работу и включает резервный режим с дип-линками Авито;
* короткие таймауты, ограничение числа запросов, TTL-кэш (в т.ч. негативных
  ответов) и «выключатель» после блокировки, чтобы не долбить недоступный
  хост;
* парсинг идёт тремя независимыми стратегиями (карточки SERP → JSON-LD →
  ``__NEXT_DATA__``): сломалась одна — работают остальные.
"""

from __future__ import annotations

import html
import json
import re
import time
from typing import Any
from urllib.parse import quote_plus, urlparse

import httpx

from ... import lexicon
from ...helpers import stable_id
from ...types import ProductItem
from ..provider import SearchContext, SearchProvider, ValidationOutcome

#: Раздел одежды на Авито: один стабильный слаг для всех запросов.
AVITO_FASHION_PATH = "odezhda_obuv_aksessuary"
AVITO_HOST = "www.avito.ru"

#: Хосты, которым доверяем как «настоящему Авито».
AVITO_HOSTS = ("avito.ru", "www.avito.ru", "m.avito.ru")

#: Маршрут CDN с фотографиями объявлений.
AVITO_CDN_MARK = "img.avito.st"

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 "
    "Mobile/15E148 Safari/604.1"
)

#: Слова расширений движка, которые для Авито — шум (не несут смысла).
_FILLER_EN = frozenset(
    {
        "designer", "archive", "archives", "runway", "editorial", "independent",
        "contemporary", "emerging", "niche", "brand", "brands", "rare", "cult",
        "underground", "fashion", "styling", "style", "piece", "pieces", "look",
        "outfit", "luxury", "quiet", "menswear", "womenswear", "avant", "garde",
        "collection", "trend", "trends", "aesthetic", "aesthetics", "vibe",
        "vibes", "inspired", "like", "with", "and", "the", "a", "an", "for",
        "new", "best", "buy", "shop", "clothing", "clothes", "wear", "apparel",
        "drop", "drops", "ss", "fw", "fit", "fits", "curated", "selection",
    }
)

#: Английские названия вещей → русские запросы для Авито.
_EN_GARMENT_RU: dict[str, str] = {
    "coat": "пальто", "trench": "тренч", "puffer": "пуховик", "parka": "парка",
    "bomber": "бомбер", "jacket": "куртка", "blazer": "пиджак",
    "cardigan": "кардиган", "sweater": "свитер", "knit": "свитер",
    "hoodie": "худи", "sweatshirt": "свитшот", "vest": "жилет",
    "shirt": "рубашка", "blouse": "блуза", "tshirt": "футболка",
    "t-shirt": "футболка", "tee": "футболка", "top": "топ",
    "turtleneck": "водолазка", "bodysuit": "боди", "polo": "поло",
    "trousers": "брюки", "pants": "брюки", "jeans": "джинсы",
    "skirt": "юбка", "shorts": "шорты", "leggings": "леггинсы",
    "dress": "платье", "jumpsuit": "комбинезон", "suit": "костюм",
    "boots": "ботинки", "boot": "ботинки", "sneakers": "кроссовки",
    "sneaker": "кроссовки", "shoes": "обувь", "shoe": "обувь",
    "loafers": "лоферы", "sandals": "босоножки", "heels": "туфли",
    "bag": "сумка", "backpack": "рюкзак", "tote": "сумка",
    "clutch": "клатч", "crossbody": "сумка", "belt": "ремень",
    "scarf": "шарф", "cap": "кепка", "beanie": "шапка", "hat": "шапка",
    "gloves": "перчатки", "sunglasses": "очки", "watch": "часы",
    "socks": "носки", "tights": "колготки", "swimsuit": "купальник",
    "underwear": "белье", "coatdress": "платье",
    "biker": "косуха", "denim": "джинсовый", "leather": "кожаный",
}

#: Английские слова без прямого перевода в lexicon → русский.
_EN_EXTRA_RU: dict[str, str] = {
    "ivory": "айвори", "khaki": "хаки", "mustard": "горчичный",
    "coral": "коралловый", "terracotta": "терракотовый", "beige": "бежевый",
    "burgundy": "бордовый", "emerald": "изумрудный", "velvet": "бархат",
    "suede": "замша", "chiffon": "шифон", "lace": "кружево",
    "cashmere": "кашемир", "tweed": "твид", "corduroy": "вельвет",
    "pleated": "плиссе", "ribbed": "в рубчик", "rib": "рубчик",
    "floral": "цветочный", "striped": "в полоску", "checked": "в клетку",
    "long": "длинный", "short": "короткий", "wide": "широкий",
    "narrow": "узкий", "high": "высокий", "low": "низкий",
    "warm": "теплый", "light": "легкий", "soft": "мягкий",
    "woman": "женский", "women": "женский", "female": "женский",
    "man": "мужской", "men": "мужской", "male": "мужской",
    "unisex": "унисекс", "kids": "детский", "winter": "зимний",
    "summer": "летний", "autumn": "демисезонный", "spring": "демисезонный",
    "warmth": "теплый", "waterproof": "водонепроницаемый",
}

#: Бренды, которые узнаём в заголовках (для честного поля brand).
_KNOWN_BRANDS: tuple[str, ...] = (
    "12 storeez", "lime", "zarina", "befree", "ostin", "o'stin", "sinsay",
    "reserved", "mohito", "house", "cropp", "zara", "mango", "bershka",
    "pull&bear", "pull bear", "stradivarius", "massimo dutti", "oysho",
    "uniqlo", "h&m", "h m", "cos", "arket", "monki", "weekday", "& other stories",
    "nike", "adidas", "puma", "reebok", "new balance", "asics", "vans", "converse",
    "levi's", "levi", "lee", "wrangler", "colin's", "gloria jeans",
    "lacoste", "tommy hilfiger", "calvin klein", "ralph lauren", "boss",
    "gerry weber", "tom tailor", "s.oliver", "esprit", "mexx", "savage",
    "finn flare", "baon", "snowimage", "sokolov", "585", "sunlight",
    " Henderson".strip(), "zarina", "love republic", " Befree".strip(),
    "tatuum", "terranova", "new yorker", "koton", "defacto", "incity",
    "rick owens", "margiela", "yohji", "comme des garcons", "undercover",
    "stone island", "c.p. company", "cp company", "the north face",
    "columbia", "salomon", "arcteryx", "patagonia", "napapijri",
)

# ─── регулярные выражения парсера SERP ───────────────────────────────────────

_ITEM_ID_RE = re.compile(r'data-item-id="(\d{5,})"')
_HREF_RE = re.compile(r'href="((?:https?://[a-z0-9.\-]*avito\.ru)?/[^"]*?_\d{5,}[^"]*)"')
_TITLE_RE = re.compile(r'data-marker="item-title"[^>]*>(.*?)</a>', re.DOTALL)
_NAME_RE = re.compile(r'itemprop="name"[^>]*>(.*?)<', re.DOTALL)
_TITLE_ATTR_RE = re.compile(r'title="([^"]{8,200})"')
_PRICE_META_RE = re.compile(r'itemprop="price"\s+content="([\d.]+)"')
_PRICE_BLOCK_RE = re.compile(r'data-marker="item-price"[^>]*>(.*?)</(?:p|div|span)>', re.DOTALL)
_PRICE_TEXT_RE = re.compile(r"([\d][\d\s\u00a0\u2009\u202f]{2,})\s*(?:₽|руб)", re.IGNORECASE)
_IMG_RE = re.compile(
    r'(?:src|data-src)="((?:https:)?//[^"]*avito[^"]*?\.(?:jpe?g|webp|png)[^"]*)"',
    re.IGNORECASE,
)
_IMG_ANY_RE = re.compile(r'(https://\d+\.img\.avito\.st[^\s"\']+)')
_PARAMS_RE = re.compile(r'data-marker="item-specific-params"[^>]*>(.*?)</div>', re.DOTALL)
_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL
)
_JSON_LD_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL
)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

#: Признаки блокировки/капчи в ответе.
_BLOCK_MARKS = ("captcha", "доступ ограничен", "подтвердите, что вы не робот",
                "проверка безопасности", "доступ с вашего ip", "too many requests")


def _clean_text(raw: str, limit: int = 300) -> str:
    text = _TAG_RE.sub(" ", html.unescape(raw or ""))
    text = _WS_RE.sub(" ", text).strip(" \t\n\r-–—:|·")
    return text[:limit].strip()


def _parse_price(raw: str | None) -> float | None:
    if not raw:
        return None
    digits = re.sub(r"[^\d]", "", str(raw).split(",")[0].split(".")[0]
                    if re.search(r"[₽руб]", str(raw), re.IGNORECASE) else str(raw))
    # «1,290.50» не встречается на Авито; цены всегда в рублях целыми.
    try:
        value = float(digits) if digits else None
    except ValueError:
        return None
    if value is None or value <= 0 or value > 10_000_000:
        return None
    return value


def _abs_avito_url(href: str) -> str:
    href = (href or "").strip()
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
    elif href.startswith("/"):
        href = f"https://{AVITO_HOST}{href}"
    try:
        parsed = urlparse(href)
    except ValueError:
        return ""
    host = (parsed.hostname or "").lower()
    if not any(host == allowed or host.endswith("." + allowed) for allowed in AVITO_HOSTS):
        return ""
    # Чистый путь без трекинговых параметров — ссылка стабильна и честна.
    return f"https://{AVITO_HOST}{parsed.path}" if parsed.path else ""


def avito_search_url(text: str, city: str = "rossiya") -> str:
    """Настоящая ссылка на выдачу Авито по тексту (резервный режим)."""
    query = _WS_RE.sub(" ", (text or "").strip())
    if not query:
        query = "одежда"
    slug = re.sub(r"[^a-zа-яё0-9_\-]+", "", city.lower().replace("ё", "е")) or "rossiya"
    return f"https://{AVITO_HOST}/{slug}/{AVITO_FASHION_PATH}?q={quote_plus(query)}"


def translate_query_to_ru(query: str) -> str:
    """Запрос движка (RU+EN) → короткий русский запрос для Авито."""
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ\-&']{2,}", (query or "").lower().replace("ё", "е"))
    out: list[str] = []
    index = 0
    while index < len(words):
        word = words[index].strip("-&'")
        nxt = words[index + 1].strip("-&'") if index + 1 < len(words) else ""
        bigram = f"{word} {nxt}" if nxt else ""
        if bigram and bigram in lexicon.EN_TO_RU:
            out.append(lexicon.EN_TO_RU[bigram])
            index += 2
            continue
        if not word or word in lexicon.RU_STOPWORDS or word in _FILLER_EN:
            index += 1
            continue
        if re.search(r"[а-я]", word):
            if len(word) >= 3:
                out.append(word)
        elif word in lexicon.EN_TO_RU:
            out.append(lexicon.EN_TO_RU[word])
        elif word in _EN_GARMENT_RU:
            out.append(_EN_GARMENT_RU[word])
        elif word in _EN_EXTRA_RU:
            out.append(_EN_EXTRA_RU[word])
        elif word.isalpha() and len(word) >= 3:
            # Возможно бренд (zara, lime) — оставляем как есть.
            out.append(word)
        index += 1
    deduped = list(dict.fromkeys(out))[:8]
    return " ".join(deduped) if deduped else "одежда"


def _extract_brand(title: str) -> str:
    lowered = f" {title.lower()} "
    for brand in _KNOWN_BRANDS:
        if brand and f" {brand} " in lowered or lowered.startswith(brand + " "):
            return " ".join(part.capitalize() for part in brand.split(" "))
    match = re.search(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", title)
    if match and len(match.group(1)) >= 3:
        return match.group(1)
    return "Авито"


class AvitoSearchProvider(SearchProvider):
    """Живой поиск по объявлениям Авито. Никогда не бросает исключений."""

    name = "avito"

    def __init__(
        self,
        *,
        city: str = "rossiya",
        timeout: float = 6.0,
        max_results: int = 10,
        cache_ttl_sec: int = 900,
        negative_ttl_sec: int = 180,
        user_agent: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(self.name, options)
        self.city = (city or "rossiya").strip() or "rossiya"
        self.timeout = float(timeout or 6.0)
        self.max_results = max(1, int(max_results or 10))
        self.cache_ttl = max(60, int(cache_ttl_sec or 900))
        self.negative_ttl = max(30, int(negative_ttl_sec or 180))
        self.user_agent = user_agent or _DEFAULT_USER_AGENT
        self._cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
        self._blocked_until: float = 0.0
        self.last_error: str | None = None
        self.last_live_ok: bool = False

    # ─── публичный API ────────────────────────────────────────────────────

    def search_url_for(self, text: str) -> str:
        return avito_search_url(text, self.city)

    def clear_cache(self) -> None:
        self._cache.clear()
        self._blocked_until = 0.0

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    def search(self, query: str, context: SearchContext) -> list[ProductItem]:
        try:
            return self._search_guarded(query, context)
        except Exception as exc:  # провайдер не имеет права ронять пайплайн
            self.last_error = f"{type(exc).__name__}: {exc}"
            return []

    def validate_item(self, item: ProductItem) -> ValidationOutcome:
        host = ""
        try:
            host = (urlparse(item.source_url or "").hostname or "").lower()
        except ValueError:
            pass
        if not host or not any(host == h or host.endswith("." + h) for h in AVITO_HOSTS):
            return ValidationOutcome(valid=False, confidence=0.2, reason="ссылка не ведёт на Авито")
        if not (item.price or 0) > 0:
            return ValidationOutcome(valid=False, confidence=0.3, reason="нет цены у объявления")
        return ValidationOutcome(valid=True, confidence=float(item.confidence or 0.7))

    # ─── поиск ────────────────────────────────────────────────────────────

    def _search_guarded(self, query: str, context: SearchContext) -> list[ProductItem]:
        ru_query = translate_query_to_ru(query)
        limit = max(1, min(int(context.limit or 8), self.max_results))
        categories = [str(c).lower() for c in (context.categories or [])]
        budget = float(context.user_profile.budget_max or 0)

        raw_items = self._raw_results(ru_query)
        if not raw_items:
            return []

        query_tokens = [t for t in lexicon.tokenize(f"{query} {ru_query}") if len(t) >= 3]
        scored: list[tuple[float, ProductItem]] = []
        for raw in raw_items:
            item = self._to_product(raw, ru_query, query_tokens, budget)
            if item is None:
                continue
            scored.append((float(item.meta.get("query_match") or 0.0), item))

        if categories:
            filtered = [pair for pair in scored if pair[1].category in categories]
            # Fail-open: если фильтр выкосил всё — отдаём лучшее без фильтра,
            # иначе слоты движка останутся пустыми.
            if filtered:
                scored = filtered
        scored.sort(key=lambda pair: (-pair[0], pair[1].id))

        # Фото обязательно для высокого места: если снимков хватает —
        # отдаём только объявления с фото, иначе — всё честно найденное.
        with_photo = [(score, item) for score, item in scored if item.image]
        if len(with_photo) >= min(3, limit):
            return [item for _score, item in with_photo[:limit]]
        return [item for _score, item in scored[:limit]]

    # ─── загрузка и кэш ─────────────────────────────────────────────────

    def _raw_results(self, ru_query: str) -> list[dict[str, Any]]:
        now = time.monotonic()
        cached = self._cache.get(ru_query)
        if cached is not None and now - cached[0] < self.cache_ttl:
            return cached[1]
        if now < self._blocked_until:
            return []

        html_text = self._fetch_html(ru_query)
        if not html_text:
            # Негативный кэш живёт короче: Авито мог быть недоступен временно.
            self._cache[ru_query] = (now - self.cache_ttl + self.negative_ttl, [])
            return []
        items = self._parse(html_text)
        ttl = self.cache_ttl if items else self.negative_ttl
        self._cache[ru_query] = (now - self.cache_ttl + ttl, items)
        # Кэш не должен расти бесконечно.
        if len(self._cache) > 200:
            oldest = sorted(self._cache, key=lambda key: self._cache[key][0])[:100]
            for key in oldest:
                self._cache.pop(key, None)
        return items

    def _fetch_html(self, ru_query: str) -> str:
        url = f"https://{AVITO_HOST}/{self.city}/{AVITO_FASHION_PATH}"
        params = {"q": ru_query}
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.5",
            "Cache-Control": "no-cache",
        }
        try:
            response = httpx.get(
                url,
                params=params,
                headers=headers,
                timeout=httpx.Timeout(self.timeout, connect=min(3.0, self.timeout)),
                follow_redirects=True,
            )
        except httpx.HTTPError as exc:
            self.last_error = f"сеть: {type(exc).__name__}"
            self._note_block(120.0)
            return ""
        except (OSError, ValueError) as exc:
            self.last_error = f"сеть: {exc}"
            self._note_block(120.0)
            return ""
        if response.status_code in (403, 429, 503):
            self.last_error = f"http {response.status_code}: Авито ограничил доступ"
            self._note_block(300.0)
            return ""
        if response.status_code != 200:
            self.last_error = f"http {response.status_code}"
            return ""
        text = response.text or ""
        lowered = text[:20000].lower()
        if any(mark in lowered for mark in _BLOCK_MARKS) and "data-item-id" not in lowered:
            self.last_error = "Авито показал проверку (капча)"
            self._note_block(300.0)
            return ""
        self.last_error = None
        self.last_live_ok = True
        return text

    def _note_block(self, seconds: float) -> None:
        self._blocked_until = max(self._blocked_until, time.monotonic() + seconds)
        self.last_live_ok = False

    # ─── парсинг ──────────────────────────────────────────────────────────

    def _parse(self, html_text: str) -> list[dict[str, Any]]:
        items = self._parse_cards(html_text)
        if len(items) >= 3:
            return items
        # Запасные стратегии: добираем то, чего не хватило карточкам.
        seen = {item["avito_id"] for item in items}
        for extra in self._parse_json_ld(html_text) + self._parse_next_data(html_text):
            if extra["avito_id"] not in seen:
                seen.add(extra["avito_id"])
                items.append(extra)
        return items

    def _parse_cards(self, html_text: str) -> list[dict[str, Any]]:
        matches = list(_ITEM_ID_RE.finditer(html_text))
        items: list[dict[str, Any]] = []
        for index, match in enumerate(matches):
            avito_id = match.group(1)
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else start + 8000
            block = html_text[start:min(end, start + 8000)]

            href_match = _HREF_RE.search(block)
            url = _abs_avito_url(href_match.group(1)) if href_match else ""
            if not url:
                url = f"https://{AVITO_HOST}/item_{avito_id}"

            title = ""
            title_match = _TITLE_RE.search(block)
            if title_match:
                title = _clean_text(title_match.group(1), 160)
            if len(title) < 3:
                name_match = _NAME_RE.search(block)
                if name_match:
                    title = _clean_text(name_match.group(1), 160)
            if len(title) < 3:
                attr_match = _TITLE_ATTR_RE.search(block)
                if attr_match:
                    title = _clean_text(attr_match.group(1), 160)
            if len(title) < 3:
                continue

            price: float | None = None
            price_meta = _PRICE_META_RE.search(block)
            if price_meta:
                price = _parse_price(price_meta.group(1))
            if price is None:
                price_block = _PRICE_BLOCK_RE.search(block)
                if price_block:
                    price = _parse_price(_clean_text(price_block.group(1), 60))
            if price is None:
                price_text = _PRICE_TEXT_RE.search(_clean_text(block[:3000], 3000))
                if price_text:
                    price = _parse_price(price_text.group(1))
            if price is None:
                continue

            image = ""
            img_match = _IMG_RE.search(block)
            if img_match:
                image = html.unescape(img_match.group(1))
                if image.startswith("//"):
                    image = "https:" + image
            if not image:
                any_match = _IMG_ANY_RE.search(block)
                if any_match:
                    image = html.unescape(any_match.group(1))

            params = ""
            params_match = _PARAMS_RE.search(block)
            if params_match:
                params = _clean_text(params_match.group(1), 220)

            items.append(
                {
                    "avito_id": avito_id,
                    "title": title,
                    "price": price,
                    "url": url,
                    "image": image,
                    "params": params,
                }
            )
            if len(items) >= 40:
                break
        return items

    def _parse_json_ld(self, html_text: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        try:
            for match in _JSON_LD_RE.finditer(html_text):
                try:
                    payload = json.loads(match.group(1))
                except (ValueError, TypeError):
                    continue
                nodes = payload if isinstance(payload, list) else [payload]
                for node in nodes:
                    if not isinstance(node, dict):
                        continue
                    elements = node.get("itemListElement") or []
                    if node.get("@type") == "Product":
                        elements = [node]
                    for element in elements if isinstance(elements, list) else []:
                        parsed = self._json_ld_product(
                            element.get("item", element) if isinstance(element, dict) else None
                        )
                        if parsed is not None:
                            items.append(parsed)
                        if len(items) >= 40:
                            return items
        except Exception:
            return items
        return items

    def _json_ld_product(self, node: Any) -> dict[str, Any] | None:
        if not isinstance(node, dict):
            return None
        name = str(node.get("name") or "").strip()
        url = _abs_avito_url(str(node.get("url") or ""))
        offers = node.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = _parse_price((offers or {}).get("price") if isinstance(offers, dict) else None)
        if len(name) < 3 or not url or price is None:
            return None
        image = node.get("image") or ""
        if isinstance(image, list):
            image = image[0] if image else ""
        match = re.search(r"_(\d{5,})(?:$|[/?])", url)
        return {
            "avito_id": match.group(1) if match else stable_id(url, prefix=""),
            "title": _clean_text(name, 160),
            "price": price,
            "url": url,
            "image": str(image or ""),
            "params": _clean_text(str(node.get("description") or ""), 220),
        }

    def _parse_next_data(self, html_text: str) -> list[dict[str, Any]]:
        match = _NEXT_DATA_RE.search(html_text)
        if not match:
            return []
        try:
            payload = json.loads(match.group(1))
        except (ValueError, TypeError):
            return []
        items: list[dict[str, Any]] = []
        seen: set[str] = set()
        stack: list[Any] = [payload]
        visited = 0
        while stack and visited < 40000 and len(items) < 40:
            visited += 1
            node = stack.pop()
            if isinstance(node, dict):
                title = node.get("title") or node.get("name")
                price_node = node.get("price") or node.get("priceValue") or node.get("priceDetailed")
                url = node.get("urlPath") or node.get("url") or node.get("link")
                if isinstance(title, str) and len(title) >= 3 and url:
                    price = self._next_price(price_node)
                    abs_url = _abs_avito_url(str(url))
                    if price is not None and abs_url and abs_url not in seen:
                        seen.add(abs_url)
                        image = ""
                        images = node.get("images") or node.get("image") or ""
                        if isinstance(images, list) and images:
                            first = images[0]
                            image = str(first.get("url", "") if isinstance(first, dict) else first or "")
                        elif isinstance(images, str):
                            image = images
                        elif isinstance(images, dict):
                            image = str(images.get("url", "") or "")
                        id_match = re.search(r"_(\d{5,})(?:$|[/?])", abs_url)
                        items.append(
                            {
                                "avito_id": id_match.group(1)
                                if id_match
                                else stable_id(abs_url, prefix=""),
                                "title": _clean_text(title, 160),
                                "price": price,
                                "url": abs_url,
                                "image": image,
                                "params": "",
                            }
                        )
                        continue
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
        return items

    @staticmethod
    def _next_price(node: Any) -> float | None:
        if isinstance(node, (int, float)):
            return _parse_price(node)
        if isinstance(node, str):
            return _parse_price(node)
        if isinstance(node, dict):
            for key in ("value", "amount", "price", "discount", "total"):
                if key in node:
                    parsed = AvitoSearchProvider._next_price(node[key])
                    if parsed is not None:
                        return parsed
        return None

    # ─── карточка движка + скоринг ────────────────────────────────────────

    def _to_product(
        self,
        raw: dict[str, Any],
        ru_query: str,
        query_tokens: list[str],
        budget: float,
    ) -> ProductItem | None:
        title = str(raw.get("title") or "").strip()
        url = str(raw.get("url") or "")
        price = raw.get("price")
        if len(title) < 3 or not url or not isinstance(price, (int, float)) or price <= 0:
            return None

        params = str(raw.get("params") or "")
        description = title if not params else f"{title} · {params}"
        brand = _extract_brand(title)
        category = lexicon.engine_category(f"{title} {params}", "accessory")
        colors = lexicon.detect_colors(f"{title} {params}")
        terms = lexicon.detect_terms(f"{title} {params}")

        tags = list(
            dict.fromkeys(
                terms
                + colors
                + [stem for stem in lexicon.tokenize(title) if len(stem) >= 4][:12]
                + ([brand.lower()] if brand != "Авито" else [])
            )
        )

        title_stems = lexicon.tokenize(title)
        title_set = set(title_stems)
        desc_stems = lexicon.tokenize(params) if params else []
        score = 0.0
        for token in query_tokens:
            if token in title_set:
                score += 14.0
            elif any(lexicon.matches_token(token, other) for other in title_stems):
                score += 10.0
            elif token in desc_stems or any(lexicon.matches_token(token, o) for o in desc_stems):
                score += 6.0
        for tag in tags:
            if len(str(tag)) > 2 and str(tag).lower() in ru_query.lower():
                score += 16.0
        # Бонус за точную фразу: соседние слова запроса в заголовке.
        words = [w for w in re.findall(r"[a-zа-яё]{3,}", ru_query.lower()) if w]
        joined_title = f" {title.lower()} "
        for first, second in zip(words, words[1:]):
            if first in joined_title and second in joined_title:
                score += 8.0
                break

        # Анализ описания: материалы/цвета/размер/состояние = доверие.
        richness = 0.0
        if len(params) >= 30:
            richness += 4.0
        richness += min(9.0, 3.0 * len(terms) + 2.0 * len(colors))
        if re.search(r"\b\d{2}\b|\b(XS|S|M|L|XL|XXL)\b", f"{title} {params}", re.IGNORECASE):
            richness += 3.0
        if re.search(r"нов|состоян|отличн|идеальн", f"{title} {params}".lower()):
            richness += 2.0
        score += richness

        # Анализ фото: снимок с CDN Авито — признак живого объявления.
        image = str(raw.get("image") or "")
        photo_score = 0.0
        if image:
            photo_score += 10.0
            if AVITO_CDN_MARK in image:
                photo_score += 4.0
            if re.search(r"1280|960|640|width=|x\d{3,}", image):
                photo_score += 3.0
        score += photo_score

        if brand != "Авито":
            score += 5.0
        if budget > 0:
            if price <= budget:
                score += 6.0
            elif price > budget * 1.15:
                score -= 20.0

        confidence = min(0.97, max(0.55, 0.60 + score / 320.0))
        sku = f"avito_{raw.get('avito_id')}"
        return ProductItem(
            id=stable_id("avito", raw.get("avito_id"), title, prefix="avito_"),
            sku=sku,
            name=_clean_text(title, 120),
            brand=brand,
            category=category,
            price=float(price),
            currency="RUB",
            image=image,
            source_url=url,
            source_type="marketplace",
            availability="available",
            confidence=round(confidence, 3),
            description=_clean_text(description, 280),
            color=colors[0] if colors else None,
            tags=tags,
            meta={
                "query_match": round(score, 1),
                "photo_score": round(photo_score, 1),
                "description_score": round(richness, 1),
                "source_domain": "avito.ru",
                "avito_id": str(raw.get("avito_id") or ""),
                "tier": "contemporary",
                "live": True,
            },
        )


__all__ = [
    "AVITO_FASHION_PATH",
    "AVITO_HOST",
    "AVITO_HOSTS",
    "AvitoSearchProvider",
    "avito_search_url",
    "translate_query_to_ru",
]
