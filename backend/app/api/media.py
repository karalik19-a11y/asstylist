"""Фото объявлений Авито через наш сервер.

Зачем. Страницы объявлений и их фотографии лежат на CDN Авито
(``*.img.avito.st``), который отвечает браузеру не всегда: мешает защита от
hotlink-запросов, регион и заголовок Referer. Тогда в карточке вещи вместо
фото оставался чёрный прямоугольник — а вещь без фото нам не нужна.

Решение: браузер просит снимок у нас (``/api/media/photo?u=...``), а сервер
идёт за ним на Авито уже с «правильными» заголовками и отдаёт файл со своего
домена. Заодно это даёт кэш: повторные показы образа не дёргают CDN.

Эндпоинт ходит только по белому списку хостов (``img.avito.st``, ``avito.ru``),
никогда не бросает 500 и не отдаёт ничего, кроме изображений.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, Response

from ..config import settings

router = APIRouter(prefix="/api/media", tags=["media"])

#: Хосты, у которых разрешено забирать фотографии объявлений.
ALLOWED_HOSTS: tuple[str, ...] = ("img.avito.st", "avito.ru", "www.avito.ru")

#: Больше этого размера картинку не принимаем (объявления весят десятки КБ).
MAX_BYTES = 8 * 1024 * 1024

#: Сколько держать файл у себя: снимок выдачи обновляется, но не ежечасно.
CACHE_SECONDS = 7 * 24 * 60 * 60

_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/avif": ".avif",
}

#: Заголовки, с которыми браузер Авито идёт за своими же картинками.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://www.avito.ru/",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}


def host_allowed(url: str) -> bool:
    """Ссылка ведёт на фотографию объявления Авито (и никуда больше)."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in ALLOWED_HOSTS)


def _snapshot_photo_path(url: str) -> pathlib.Path | None:
    """Фото, уже сохранённое рядом со снимком выдачи (стороной скрипта refresh).

    Если файл есть — отдаём его, вообще не выходя в сеть: снимок тогда
    работает и на закрытом Авито, и офлайн.
    """
    snapshot = pathlib.Path(settings.avito_snapshot_path or "").expanduser() if settings.avito_snapshot_path else (
        pathlib.Path(__file__).resolve().parents[1] / "catalog" / "avito_listings.json"
    )
    try:
        raw = json.loads(snapshot.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    entries = raw.get("listings") if isinstance(raw, dict) else raw
    for entry in entries or []:
        if not isinstance(entry, dict) or str(entry.get("image") or "") != url:
            continue
        relative = str(entry.get("photo_path") or "").strip()
        if not relative:
            continue
        candidate = (snapshot.parent / relative).resolve()
        try:
            if candidate.is_file() and candidate.stat().st_size > 0:
                return candidate
        except OSError:
            return None
    return None


def _cache_path(url: str, extension: str) -> pathlib.Path:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()  # noqa: S324 — не про безопасность
    return pathlib.Path(settings.data_dir) / "photo_cache" / f"{digest}{extension}"


def _read_cache(url: str) -> tuple[bytes, str] | None:
    for media_type, extension in _EXTENSIONS.items():
        path = _cache_path(url, extension)
        try:
            if path.is_file():
                return path.read_bytes(), media_type
        except OSError:
            continue
    return None


async def fetch_photo(url: str) -> tuple[bytes, str]:
    """Скачать фотографию объявления. Бросает HTTPException, если не вышло."""
    if not host_allowed(url):
        raise HTTPException(status_code=400, detail="Фотографию можно брать только с Авито")

    local = _snapshot_photo_path(url)
    if local is not None:
        media_type = _EXTENSIONS.get(f"image/{local.suffix.lstrip('.').lower()}", "image/jpeg")
        try:
            return local.read_bytes(), media_type
        except OSError:
            pass  # файл пропал — идём в сеть

    cached = _read_cache(url)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient(
            timeout=settings.avito_photo_timeout_sec + 6.0,
            follow_redirects=True,
            headers=_BROWSER_HEADERS,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            media_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
            payload = response.content
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Авито не отдал фото: {exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Фото недоступно: {type(exc).__name__}") from exc

    if media_type not in _EXTENSIONS:
        raise HTTPException(status_code=502, detail="Ответ Авито — не изображение")
    if not payload:
        raise HTTPException(status_code=502, detail="Пустой файл изображения")
    if len(payload) > MAX_BYTES:
        raise HTTPException(status_code=502, detail="Изображение слишком большое")

    try:
        path = _cache_path(url, _EXTENSIONS[media_type])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    except OSError:
        pass  # кэш — приятный бонус, без него просто ходим на Авито каждый раз

    return payload, media_type


@router.get("/photo")
async def photo(request: Request, u: str = Query(..., min_length=10, description="ссылка на фото объявления")) -> Response:
    """Отдать фотографию объявления Авито со своего домена (и закэшировать)."""
    payload, media_type = await fetch_photo(u)
    return Response(
        content=payload,
        media_type=media_type,
        headers={
            "Cache-Control": f"public, max-age={CACHE_SECONDS}, immutable",
            "X-Photo-Source": "avito",
        },
    )
