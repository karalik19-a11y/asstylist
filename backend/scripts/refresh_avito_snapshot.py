"""Обновление снимка выдачи Авито (реальные объявления в поставке).

Скрипт ходит на Авито тем же провайдером, что и приложение
(:class:`AvitoSearchProvider`), собирает конкретные объявления — название,
цену, ссылку на объявление, фотографию с CDN, состояние и описание — и
складывает их в ``backend/app/catalog/avito_listings.json``.

Зачем: живой поиск остаётся основным путём, но Авито закрывает доступ с
дата-центров и «шумных» IP капчей. Снимок гарантирует, что даже тогда сервис
показывает **конкретные вещи с фото и ссылкой на объявление**, а не подборку и
не «дефолтную» позицию каталога.

Запуск (там, где сеть до Авито открыта — локально или на раннере GitHub
Actions, см. ``.github/workflows/avito-snapshot.yml``)::

    make refresh-avito
    python backend/scripts/refresh_avito_snapshot.py --per-query 6 --delay 4

Ключи: ``--queries`` (свой список), ``--path`` (куда писать),
``--keep-days`` (сколько дней хранить старые находки).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from app.fashion_engine.search.listing_intel import looks_like_listing_url  # noqa: E402
from app.fashion_engine.search.providers.avito_provider import (  # noqa: E402
    AvitoSearchProvider,
    translate_query_to_ru,
)

DEFAULT_PATH = BACKEND_DIR / "app" / "catalog" / "avito_listings.json"

#: Запросы покрывают все слоты образа (и женские, и мужские подачи).
DEFAULT_QUERIES: tuple[str, ...] = (
    "пальто женское",
    "куртка мужская",
    "свитер женский",
    "рубашка мужская",
    "футболка базовая",
    "джинсы женские",
    "брюки мужские",
    "юбка женская",
    "платье женское",
    "кроссовки мужские",
    "ботинки женские кожаные",
    "сумка женская кожаная",
    "шарф шерстяной",
    "ремень кожаный",
)

#: Минимальный набор полей, без которого объявление бесполезно интерфейсу.
REQUIRED_FIELDS = ("title", "price", "url", "image")

#: Стоп-слова Авито: такие «объявления» не ведут на конкретную вещь.
BAD_URL_MARKS = ("/favorites", "?q=", "/additem")


def _load(path: pathlib.Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"captured_at": "", "source": "avito.ru", "queries": [], "listings": []}
    if isinstance(payload, list):  # поддерживаем «плоский» формат
        return {"captured_at": "", "source": "avito.ru", "queries": [], "listings": payload}
    payload.setdefault("listings", [])
    payload.setdefault("queries", [])
    payload.setdefault("source", "avito.ru")
    return payload


def _normalise(raw: dict[str, Any], *, query: str, captured: str) -> dict[str, Any] | None:
    """Сырое объявление провайдера → запись снимка."""
    title = str(raw.get("title") or "").strip()
    url = str(raw.get("url") or "").split("?")[0]
    price = raw.get("price")
    image = str(raw.get("image") or "").strip()
    if not title or not url or not isinstance(price, (int, float)) or price <= 0:
        return None
    if not looks_like_listing_url(url) or any(mark in url for mark in BAD_URL_MARKS):
        # Только конкретные объявления: подборки и служебные ссылки не годятся.
        return None
    if not image:
        return None  # вещь без фото не показываем как «конкретную»
    listing_id = str(raw.get("avito_id") or url.rsplit("_", 1)[-1])
    return {
        "id": listing_id,
        "title": title,
        "price": float(price),
        "url": url,
        "image": image,
        "params": str(raw.get("params") or "")[:220],
        "description": str(raw.get("description") or raw.get("params") or "")[:400],
        "brand": str(raw.get("brand") or ""),
        "city": str(raw.get("city") or ""),
        "gender": str(raw.get("gender") or ""),
        "captured_at": captured,
        "query": query,
    }


def _city_from_url(url: str) -> str:
    parts = url.split("/")
    return parts[3] if len(parts) > 4 else ""


def collect(
    queries: list[str],
    *,
    per_query: int,
    delay: float,
    provider: AvitoSearchProvider,
    verbose: bool = True,
) -> list[dict[str, Any]]:
    """Собрать реальные объявления по списку запросов."""
    captured = datetime.now(timezone.utc).date().isoformat()
    found: list[dict[str, Any]] = []
    for index, query in enumerate(queries):
        ru_query = translate_query_to_ru(query)
        if verbose:
            print(f"[{index + 1}/{len(queries)}] {query} → {ru_query}", flush=True)
        try:
            raw_items = provider._raw_results(ru_query)  # noqa: SLF001 — внутренний сбор выдачи
        except Exception as exc:  # сеть/капча — продолжаем с остальными запросами
            print(f"    ! {type(exc).__name__}: {exc}", flush=True)
            continue
        taken = 0
        for raw in raw_items:
            entry = _normalise(raw, query=query, captured=captured)
            if entry is None:
                continue
            if not entry["city"]:
                entry["city"] = _city_from_url(entry["url"])
            found.append(entry)
            taken += 1
            if taken >= per_query:
                break
        if verbose:
            print(f"    + {taken} объявлений", flush=True)
        if delay and index < len(queries) - 1:
            time.sleep(delay)  # вежливая пауза: Авито не любит частые запросы
    return found


def merge(
    old: list[dict[str, Any]],
    new: list[dict[str, Any]],
    *,
    keep_days: int,
) -> list[dict[str, Any]]:
    """Свежие находки важнее; старые храним, пока не устарели."""
    by_id: dict[str, dict[str, Any]] = {}
    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=max(1, keep_days))).isoformat()
    for entry in old:
        entry_id = str(entry.get("id") or "")
        captured = str(entry.get("captured_at") or "")
        if entry_id and (not captured or captured >= cutoff):
            by_id[entry_id] = entry
    for entry in new:  # новые перекрывают старые записи того же объявления
        by_id[str(entry["id"])] = entry
    return list(by_id.values())


def main() -> int:
    parser = argparse.ArgumentParser(description="Обновить снимок выдачи Авито")
    parser.add_argument("--queries", nargs="*", default=list(DEFAULT_QUERIES))
    parser.add_argument("--per-query", type=int, default=5, help="сколько объявлений брать на запрос")
    parser.add_argument("--delay", type=float, default=3.0, help="пауза между запросами, сек")
    parser.add_argument("--path", type=pathlib.Path, default=DEFAULT_PATH)
    parser.add_argument("--keep-days", type=int, default=45, help="сколько дней хранить старые находки")
    parser.add_argument("--city", default=settings.avito_city, help="регион Авито (rossiya, moskva, …)")
    parser.add_argument("--dry-run", action="store_true", help="не писать файл, только показать итог")
    args = parser.parse_args()

    provider = AvitoSearchProvider(
        city=args.city,
        timeout=max(10.0, settings.avito_timeout_sec),
        max_results=max(10, args.per_query * 2),
        cache_ttl_sec=0,
        negative_ttl_sec=30,
    )
    payload = _load(args.path)
    before = len(payload.get("listings") or [])
    fresh = collect(list(args.queries), per_query=args.per_query, delay=args.delay, provider=provider)
    print(f"\nсобрано объявлений: {len(fresh)} (было {before})")
    if not fresh:
        print("Авито не отдал объявления (капча/сеть). Файл не меняем.")
        return 1

    listings = merge(payload.get("listings") or [], fresh, keep_days=args.keep_days)
    queries_meta = [
        {"query": query, "captured_at": datetime.now(timezone.utc).date().isoformat()}
        for query in args.queries
    ]
    out = {
        "captured_at": datetime.now(timezone.utc).date().isoformat(),
        "source": "avito.ru",
        "note": (
            "Снимок реальной выдачи Авито: конкретные объявления с фото, ценами и ссылками. "
            "Обновляется скриптом backend/scripts/refresh_avito_snapshot.py."
        ),
        "queries": queries_meta,
        "listings": sorted(listings, key=lambda entry: (str(entry.get("query") or ""), -float(entry.get("price") or 0))),
    }
    if args.dry_run:
        print(json.dumps(out["listings"][:5], ensure_ascii=False, indent=2))
        return 0
    args.path.parent.mkdir(parents=True, exist_ok=True)
    args.path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"записано: {args.path} ({len(out['listings'])} объявлений)")
    _ = date  # noqa: B018 — date нужен для аннотаций выше
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
