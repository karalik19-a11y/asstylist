"""AvitoSnapshotProvider — снимок выдачи Авито с реальными объявлениями.

Зачем нужен. Авито — единственный источник вещей asStylist, но доступ к нему
не гарантирован: с дата-центров и «шумных» IP сайт отдаёт капчу, без сети он
недоступен вовсе. Тогда сервис не имеет права показывать «дефолтные» вещи или
подменять объявление поисковой ссылкой — пользователь должен видеть конкретную
вещь с фото и ценой.

Решение: в поставку входит **снимок выдачи** — реальные объявления Авито
(название, цена, ссылка на объявление, фото с CDN Авито, описание и состояние),
сохранённые в ``app/data/avito_listings.json`` и обновляемые скриптом
``scripts/refresh_avito_snapshot.py`` (он ходит на Авито живым провайдером).

Провайдер честно помечает такие карточки (``meta.live = False``,
``meta.snapshot_captured_at``) — интерфейс показывает дату снимка, а не делает
вид, что объявление только что найдено.

Поиск внутри снимка идёт тем же слоем, что и живой: ``listing_intel`` —
ключевые слова, описание, внешний вид (фото/палитра/состояние).
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from ...helpers import stable_id
from ...types import ProductItem
from ..listing_intel import analyze_listing, appearance_match, looks_like_listing_url, query_match
from ..provider import SearchContext, SearchProvider, ValidationOutcome

#: Путь по умолчанию: снимок лежит рядом с кодом, в поставке приложения.
DEFAULT_SNAPSHOT_PATH = Path(__file__).resolve().parents[3] / "catalog" / "avito_listings.json"

#: Предел «устаревания» снимка: старше — считаем данные справочными и
#: предупреждаем в UI (сами объявления всё равно остаются конкретными).
DEFAULT_MAX_AGE_DAYS = 120


def _parse_captured_at(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and value:
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def _slug_city(url: str) -> str:
    """Город из ссылки объявления: ``/moskva/odezhda_obuv_aksessuary/slug_id``."""
    match = re.search(r"avito\.ru/([a-z0-9_-]+)/", (url or "").lower())
    return match.group(1) if match else ""


def _to_rub(value: Any) -> float | None:
    try:
        price = float(str(value).replace(" ", "").replace("\u00a0", ""))
    except (TypeError, ValueError):
        return None
    if price <= 0 or price > 10_000_000:
        return None
    return price


class AvitoSnapshotProvider(SearchProvider):
    """Поиск по снимку реальных объявлений. Никогда не бросает исключений."""

    name = "avito-snapshot"

    def __init__(
        self,
        path: str | Path | None = None,
        *,
        max_results: int = 12,
        max_age_days: int = DEFAULT_MAX_AGE_DAYS,
        options: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(self.name, options)
        self.path = Path(path) if path else DEFAULT_SNAPSHOT_PATH
        self.max_results = max(1, int(max_results or 12))
        self.max_age_days = max(1, int(max_age_days or DEFAULT_MAX_AGE_DAYS))
        self._listings: list[dict[str, Any]] | None = None
        self._captured_at: date | None = None
        self.last_error: str | None = None

    # ─── данные ───────────────────────────────────────────────────────────

    @property
    def captured_at(self) -> date | None:
        self.listings()
        return self._captured_at

    @property
    def is_stale(self) -> bool:
        captured = self.captured_at
        if captured is None:
            return True
        return (datetime.now(timezone.utc).date() - captured).days > self.max_age_days

    def listings(self) -> list[dict[str, Any]]:
        """Снимок выдачи: список реальных объявлений (в порядке файла)."""
        if self._listings is not None:
            return self._listings
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            self.last_error = f"снимок Авито недоступен: {type(exc).__name__}"
            self._listings = []
            return self._listings

        if isinstance(raw, dict):
            entries = raw.get("listings") or []
            self._captured_at = _parse_captured_at(raw.get("captured_at"))
        else:
            entries = raw if isinstance(raw, list) else []
            self._captured_at = None

        prepared: list[dict[str, Any]] = []
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            item = self._normalise(entry)
            if item is None:
                continue
            key = str(item["id"])
            if key in seen:
                continue
            seen.add(key)
            prepared.append(item)
        self._listings = prepared
        return prepared

    def _normalise(self, entry: dict[str, Any]) -> dict[str, Any] | None:
        url = str(entry.get("url") or "").strip()
        title = str(entry.get("title") or "").strip()
        price = _to_rub(entry.get("price"))
        if len(title) < 3 or not url or price is None:
            return None
        if "avito.ru" not in url:
            return None
        listing_id = str(entry.get("id") or "").strip() or stable_id(url, prefix="")
        description = str(entry.get("description") or "").strip()
        params = str(entry.get("params") or "").strip()
        city = str(entry.get("city") or "").strip() or _slug_city(url)
        return {
            "id": listing_id,
            "title": title,
            "price": price,
            "url": url.split("?")[0],
            "image": str(entry.get("image") or "").strip(),
            "description": description,
            "params": params,
            "city": city,
            "query": str(entry.get("query") or "").strip(),
            "captured_at": entry.get("captured_at") or (
                self._captured_at.isoformat() if self._captured_at else ""
            ),
        }

    # ─── SearchProvider ───────────────────────────────────────────────────

    def validate_item(self, item: ProductItem) -> ValidationOutcome:
        if not looks_like_listing_url(item.source_url):
            return ValidationOutcome(valid=False, confidence=0.2, reason="ссылка не ведёт на объявление")
        if not (item.price or 0) > 0:
            return ValidationOutcome(valid=False, confidence=0.3, reason="нет цены у объявления")
        return ValidationOutcome(valid=True, confidence=float(item.confidence or 0.7))

    def search(self, query: str, context: SearchContext) -> list[ProductItem]:
        try:
            return self._search_guarded(query, context)
        except Exception as exc:  # провайдер не имеет права ронять пайплайн
            self.last_error = f"{type(exc).__name__}: {exc}"
            return []

    def _search_guarded(self, query: str, context: SearchContext) -> list[ProductItem]:
        from ..providers.avito_provider import translate_query_to_ru  # локально: без циклов

        listings = self.listings()
        if not listings:
            return []

        ru_query = translate_query_to_ru(query)
        from ... import lexicon

        query_tokens = [token for token in lexicon.tokenize(f"{query} {ru_query}") if len(token) >= 3]
        limit = max(1, min(int(context.limit or 8), self.max_results))
        categories = [str(category).lower() for category in (context.categories or [])]
        profile = context.user_profile
        budget = float(getattr(profile, "budget_max", 0) or 0)

        scored: list[tuple[float, ProductItem]] = []
        for entry in listings:
            item = self._to_product(entry, ru_query, query_tokens, context)
            if item is None:
                continue
            scored.append((float(item.meta.get("selection_score") or 0.0), item))

        if budget > 0:
            affordable = [pair for pair in scored if pair[1].price is not None and pair[1].price <= budget * 1.25]
            if affordable:
                scored = affordable

        if categories:
            filtered = [pair for pair in scored if pair[1].category in categories]
            if filtered:  # fail-open: фильтр не должен давать пустую выдачу
                scored = filtered

        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        with_photo = [(score, item) for score, item in scored if item.image]
        if len(with_photo) >= min(3, limit):
            return [item for _score, item in with_photo[:limit]]
        return [item for _score, item in scored[:limit]]

    def _to_product(
        self,
        entry: dict[str, Any],
        ru_query: str,
        query_tokens: list[str],
        context: SearchContext,
    ) -> ProductItem | None:
        from ... import lexicon  # локально: модуль и так импортирован выше

        title = str(entry["title"])
        description = str(entry.get("description") or "")
        params = str(entry.get("params") or "")
        text = f"{title} · {params}" if params else title
        full_text = f"{title} {params} {description}".strip()

        traits = analyze_listing(title, description, params, str(entry.get("image") or ""))
        profile = context.user_profile
        match = appearance_match(
            traits,
            preferred_colors=list(getattr(profile, "colors", []) or []),
            # В профиле движка исключённые оттенки лежат в ``disliked_items``
            # (см. fashion_engine_service.build_profile) — это те же слова цветов.
            avoid_colors=[
                word for word in list(getattr(profile, "disliked_items", []) or []) if word
            ],
            silhouette_preference=(list(getattr(profile, "preferred_silhouette", []) or []) or [None])[0],
            style=None,
            season=None,
            presentation=str(getattr(profile, "gender", "unisex") or "unisex"),
            budget=float(getattr(profile, "budget_max", 0) or 0),
            price=float(entry["price"]),
            size=None,
        )
        lexical, hits = query_match(ru_query, query_tokens, title, f"{params} {description}")

        # Итоговый отбор: слова весят больше, внешний вид и описание — решают
        # между близкими по словам объявлениями.
        selection = lexical + 34.0 * match.score * 2.0
        if traits.photo_quality > 0:
            selection += traits.photo_quality
        if hits:
            selection += 3.0
        if not looks_like_listing_url(str(entry["url"])):  # подстраховка от поисковых ссылок
            return None

        category = lexicon.engine_category(full_text, "accessory")
        brand = str(entry.get("brand") or "").strip()
        if not brand:
            from .avito_provider import _extract_brand  # единый распознаватель бренда

            brand = _extract_brand(title)
        primary_color = traits.colors[0] if traits.colors else None
        listing_id = str(entry["id"])
        captured_at = str(entry.get("captured_at") or "")

        return ProductItem(
            id=stable_id("avito_snapshot", listing_id, title, prefix="avito_"),
            sku=f"avito_{listing_id}",
            name=title,
            brand=brand,
            category=category,
            price=float(entry["price"]),
            currency="RUB",
            image=str(entry.get("image") or ""),
            source_url=str(entry["url"]),
            source_type="marketplace",
            availability="available",
            confidence=round(min(0.95, max(0.6, 0.62 + match.score * 0.3)), 3),
            description=(description or text)[:280],
            color=primary_color,
            tags=list(
                dict.fromkeys(
                    traits.garments
                    + traits.materials
                    + traits.colors
                    + traits.silhouettes
                    + [token for token in lexicon.tokenize(title) if len(token) >= 4][:10]
                )
            ),
            meta={
                "live": False,
                "snapshot": True,
                "snapshot_captured_at": captured_at,
                "captured_at": captured_at,
                "selection_score": round(selection, 2),
                "query_match": round(lexical, 1),
                "query_hits": hits,
                "appearance": match.to_dict(),
                "traits": traits.to_dict(),
                "photo_score": round(traits.photo_quality, 1),
                "description_score": round(traits.text_richness, 1),
                "condition": traits.condition,
                "sizes": traits.size_tokens,
                "city": entry.get("city") or "",
                "source_domain": "avito.ru",
                "avito_id": listing_id,
                "listing_url_kind": "listing",
                "tier": "contemporary",
            },
        )


__all__ = ["AvitoSnapshotProvider", "DEFAULT_SNAPSHOT_PATH", "DEFAULT_MAX_AGE_DAYS"]
