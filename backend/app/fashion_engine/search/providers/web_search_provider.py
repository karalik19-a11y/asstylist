"""WebSearchProvider — живой поиск вещей по интернету.

Источники (результаты складываются, дедупликация по «бренд::название»):

* **партнёрский фид магазина** — ``PRODUCT_FEED_URL``, JSON-массив товаров
  ``[{name, brand, price, currency, category, image, url, tags?}, …]``;
* **SerpAPI Google Shopping** — ``SERPAPI_API_KEY`` (engine=google_shopping);
* **Google Custom Search** — ``GOOGLE_CSE_API_KEY`` + ``GOOGLE_CSE_CX``.

Гарантии пайплайна сохранены:

* любой сетевой/парсинговый сбой → пустой список, движок продолжает работу;
* товары никогда не выдумываются: каждый результат — реальная карточка с
  URL, изображением и ценой;
* цены нормализуются в рубли через курсы ``settings.fx_rates`` (исходная
  цена хранится в ``meta[\"price_original\"]``), чтобы бюджетный фильтр
  движка и интерфейс работали в одних единицах.
"""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from ... import lexicon
from ...helpers import stable_id
from ...types import ProductItem
from ..provider import SearchContext, SearchProvider, ValidationOutcome

_SERPAPI_URL = "https://serpapi.com/search.json"
_GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"

#: Как часто перечитывать партнёрский фид (секунды).
_FEED_TTL_SEC = 15 * 60

_PRICE_RE = re.compile(r"(\d[\d\s\u00a0.,]*)")


def _http_get_json(url: str, *, params: dict[str, Any], timeout: float) -> dict[str, Any] | list[Any] | None:
    """Вся сеть провайдера — в одной функции: любой сбой → None."""
    try:
        response = httpx.get(url, params=params, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError, OSError):
        return None


def _parse_price(raw: Any) -> float | None:
    """«25 999 ₽» / «$1,290.50» / 12990 → float; None, если цены нет."""
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw) if raw > 0 else None
    match = _PRICE_RE.search(str(raw))
    if not match:
        return None
    text = match.group(1).replace("\u00a0", " ").strip()
    # «1,290.50» → 1290.50; «25 999,00» → 25999.00
    normalized = text.replace(" ", "")
    if normalized.count(",") == 1 and (normalized.count(".") == 0 or normalized.rfind(",") > normalized.rfind(".")):
        normalized = normalized.replace(".", "").replace(",", ".")
    else:
        normalized = normalized.replace(",", "")
    try:
        value = float(normalized)
    except ValueError:
        return None
    return value if value > 0 else None


def _detect_currency(text: str, default: str = "RUB") -> str:
    lowered = (text or "").lower()
    if "€" in lowered or "eur" in lowered:
        return "EUR"
    if "$" in lowered or "usd" in lowered:
        return "USD"
    if "£" in lowered or "gbp" in lowered:
        return "GBP"
    if "₽" in lowered or "руб" in lowered:
        return "RUB"
    return default


class WebSearchProvider(SearchProvider):
    """Живой поиск: фид магазина + SerpAPI Google Shopping + Google CSE."""

    name = "web-search"

    def __init__(
        self,
        *,
        serpapi_key: str | None = None,
        google_key: str | None = None,
        google_cx: str | None = None,
        feed_url: str | None = None,
        fx_rates: dict[str, float] | None = None,
        timeout: float = 6.0,
        max_results: int = 8,
        options: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(self.name, options)
        self.serpapi_key = serpapi_key
        self.google_key = google_key
        self.google_cx = google_cx
        self.feed_url = feed_url
        self.fx_rates = {"RUB": 1.0, **dict(fx_rates or {})}
        self.timeout = float(timeout)
        self.max_results = int(max_results)
        self._feed_cache: list[dict[str, Any]] | None = None
        self._feed_loaded_at: float = 0.0

    # ─── конфигурация ─────────────────────────────────────────────────
    def configured_sources(self) -> list[str]:
        sources: list[str] = []
        if self.feed_url:
            sources.append("partner-feed")
        if self.serpapi_key:
            sources.append("serpapi:google-shopping")
        if self.google_key and self.google_cx:
            sources.append("google-cse")
        return sources

    def available(self) -> bool:
        return bool(self.configured_sources())

    # ─── публичный поиск ──────────────────────────────────────────────
    def search(self, query: str, context: SearchContext) -> list[ProductItem]:
        query = (query or "").strip()
        if not query or not self.available():
            return []

        limit = max(1, int(context.limit or 8))
        found: list[ProductItem] = []
        found.extend(self._search_feed(query, limit))
        found.extend(self._search_serpapi(query, limit))
        found.extend(self._search_google_cse(query, limit))

        seen: set[str] = set()
        ranked: list[tuple[float, ProductItem]] = []
        for item in found:
            key = f"{(item.brand or '').lower()}::{(item.name or '').lower()}"
            if key in seen:
                continue
            seen.add(key)
            ranked.append((self._relevance(item, query), item))
        ranked.sort(key=lambda pair: (-pair[0], pair[1].id))
        return [item for _score, item in ranked[:limit]]

    def validate_item(self, item: ProductItem) -> ValidationOutcome:
        if not item.source_url or not (item.price or 0) > 0:
            return ValidationOutcome(valid=False, confidence=0.3, reason="нет ссылки или цены у живой находки")
        return ValidationOutcome(valid=True, confidence=float(item.confidence or 0.65))

    # ─── источник: партнёрский фид ────────────────────────────────────
    def _feed_items(self) -> list[dict[str, Any]]:
        if not self.feed_url:
            return []
        now = time.monotonic()
        if self._feed_cache is not None and now - self._feed_loaded_at < _FEED_TTL_SEC:
            return self._feed_cache
        data = _http_get_json(self.feed_url, params={}, timeout=self.timeout)
        rows: list[dict[str, Any]] = []
        if isinstance(data, list):
            rows = [row for row in data if isinstance(row, dict)]
        elif isinstance(data, dict):
            candidate = data.get("items") or data.get("products") or []
            rows = [row for row in candidate if isinstance(row, dict)]
        self._feed_cache = rows
        self._feed_loaded_at = now
        return rows

    def _search_feed(self, query: str, limit: int) -> list[ProductItem]:
        normalized = query.lower().replace("ё", "е")
        tokens = [token for token in lexicon.tokenize(normalized) if len(token) >= 3]
        scored: list[tuple[float, dict[str, Any]]] = []
        for row in self._feed_items():
            text = " ".join(
                str(row.get(key) or "")
                for key in ("name", "brand", "category", "description")
            ).lower()
            text += " " + " ".join(str(tag).lower() for tag in row.get("tags") or [])
            score = 0.0
            for token in tokens:
                if token in text:
                    score += 12.0
            for tag in row.get("tags") or []:
                tag_text = str(tag).lower()
                if len(tag_text) > 2 and tag_text in normalized:
                    score += 18.0
            if self.to_rub_amount(row)[0] is not None:
                price_rub = self.to_rub_amount(row)[0]
                if score > 0 and price_rub is not None:
                    scored.append((score, row))
        scored.sort(key=lambda pair: (-pair[0], str(pair[1].get("name") or "")))
        items: list[ProductItem] = []
        for _score, row in scored[:limit]:
            item = self._row_to_item(row, confidence=0.85, feed=True)
            if item is not None:
                items.append(item)
        return items

    # ─── источник: SerpAPI Google Shopping ────────────────────────────
    def _search_serpapi(self, query: str, limit: int) -> list[ProductItem]:
        if not self.serpapi_key:
            return []
        data = _http_get_json(
            _SERPAPI_URL,
            params={
                "engine": "google_shopping",
                "q": query,
                "gl": "ru",
                "hl": "ru",
                "num": min(self.max_results, max(limit * 2, 10)),
                "api_key": self.serpapi_key,
            },
            timeout=self.timeout,
        )
        items: list[ProductItem] = []
        if isinstance(data, dict):
            for row in data.get("shopping_results") or []:
                if not isinstance(row, dict):
                    continue
                price = _parse_price(row.get("extracted_price")) or _parse_price(row.get("price"))
                if price is None:
                    continue
                currency = _detect_currency(str(row.get("price") or ""), default="RUB")
                url = str(row.get("product_link") or row.get("link") or "")
                if not url:
                    continue
                items.append(
                    self._make_item(
                        name=str(row.get("title") or "").strip(),
                        brand=str(row.get("source") or urlparse(url).netloc),
                        price=price,
                        currency=currency,
                        url=url,
                        image=str(row.get("thumbnail") or ""),
                        query=query,
                        confidence=0.72,
                        extra_tags=[],
                    )
                )
        return [item for item in items if item is not None][:limit]

    # ─── источник: Google Custom Search ───────────────────────────────
    def _search_google_cse(self, query: str, limit: int) -> list[ProductItem]:
        if not (self.google_key and self.google_cx):
            return []
        data = _http_get_json(
            _GOOGLE_CSE_URL,
            params={
                "key": self.google_key,
                "cx": self.google_cx,
                "q": query,
                "num": min(self.max_results, max(limit, 5), 10),
                "safe": "active",
                "gl": "ru",
                "lr": "lang_ru",
            },
            timeout=self.timeout,
        )
        items: list[ProductItem] = []
        if isinstance(data, dict):
            for row in data.get("items") or []:
                if not isinstance(row, dict):
                    continue
                pagemap = row.get("pagemap") or {}

                def first(key: str) -> dict[str, Any]:
                    entries = pagemap.get(key) or []
                    return entries[0] if entries and isinstance(entries[0], dict) else {}

                offer = first("offer")
                product = first("product")
                price = _parse_price(offer.get("price")) or _parse_price(product.get("price"))
                if price is None:
                    continue
                currency = str(offer.get("pricecurrency") or product.get("pricecurrency") or "RUB").upper()
                image = first("cse_image").get("src") or first("cse_thumbnail").get("src") or ""
                url = str(row.get("link") or "")
                if not url:
                    continue
                items.append(
                    self._make_item(
                        name=str(product.get("name") or row.get("title") or "").strip(),
                        brand=str(offer.get("seller") or row.get("displayLink") or urlparse(url).netloc),
                        price=price,
                        currency=currency,
                        url=url,
                        image=str(image),
                        query=query,
                        confidence=0.62,
                        extra_tags=[],
                    )
                )
        return [item for item in items if item is not None][:limit]

    # ─── нормализация ─────────────────────────────────────────────────
    def to_rub_amount(self, row: dict[str, Any]) -> tuple[float | None, float, str]:
        price = _parse_price(row.get("price"))
        if price is None:
            return None, 0.0, "RUB"
        currency = str(row.get("currency") or "RUB").upper()
        rate = float(self.fx_rates.get(currency, 1.0))
        return round(price * rate, 2), price, currency

    def _row_to_item(self, row: dict[str, Any], *, confidence: float, feed: bool = False) -> ProductItem | None:
        price_rub, price, currency = self.to_rub_amount(row)
        if price_rub is None:
            return None
        return self._make_item(
            name=str(row.get("name") or "").strip(),
            brand=str(row.get("brand") or urlparse(str(row.get("url") or "")).netloc),
            price=price,
            currency=currency,
            url=str(row.get("url") or ""),
            image=str(row.get("image") or ""),
            query="",
            confidence=confidence,
            extra_tags=[str(tag) for tag in row.get("tags") or []],
            category=str(row.get("category") or ""),
            description=str(row.get("description") or ""),
            price_rub=price_rub,
        )

    def _make_item(
        self,
        *,
        name: str,
        brand: str,
        price: float,
        currency: str,
        url: str,
        image: str,
        query: str,
        confidence: float,
        extra_tags: list[str],
        category: str = "",
        description: str = "",
        price_rub: float | None = None,
    ) -> ProductItem | None:
        if not name or not url or price <= 0:
            return None
        if price_rub is None:
            rate = float(self.fx_rates.get(currency.upper(), 1.0))
            price_rub = round(price * rate, 2)
        tags = [tag for tag in extra_tags if tag]
        engine_category = lexicon.engine_category(" ".join([name, category]), "accessory")
        item = ProductItem(
            id=stable_id("web", brand, name, url, prefix="web_"),
            sku=stable_id("web", brand, name, url, prefix="web_"),
            name=name,
            brand=brand,
            category=engine_category,
            price=price_rub,
            currency="RUB",
            image=image,
            source_url=url,
            source_type="web",
            availability="available",
            confidence=confidence,
            tags=tags,
            description=description or " ".join(tags),
            meta={
                "price_original": f"{price:g} {currency.upper()}",
                "source_domain": urlparse(url).netloc,
                "web_query": query,
            },
        )
        return item

    @staticmethod
    def _relevance(item: ProductItem, query: str) -> float:
        """Локальная релевантность находки запросу (для порядка в выдаче)."""
        tokens = [token for token in lexicon.tokenize(query.lower().replace("ё", "е")) if len(token) >= 3]
        if not tokens:
            return float(item.confidence or 0.6)
        text = item.searchable_text()
        card_tokens = set(lexicon.tokenize(text))
        score = 0.0
        for token in tokens:
            if token in card_tokens:
                score += 12.0
            elif any(lexicon.matches_token(token, other) for other in card_tokens):
                score += 9.0
            elif token in text:
                score += 6.0
        item.meta["query_match"] = max(float(item.meta.get("query_match") or 0.0), score)
        return score
