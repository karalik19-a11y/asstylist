"""Анализ фотографии объявления — «что видно на снимке вещи».

Движку нужно не только название вещи, но и её внешний вид. Живая выдача Авито
приносит ссылку на фото с CDN; здесь снимок скачивается и измеряется локально
(Pillow, без ключей и внешних моделей):

* доминирующие оттенки → ближайшие цвета палитры приложения;
* яркость, насыщенность и контраст — светлая вещь или тёмная, «кричащая» или нет;
* однородность фона — студийный кадр или «вещь на диване»;
* соотношение сторон и разрешение — качество снимка.

Модуль полностью необязательный: без сети, при блокировке CDN или на битом
файле он возвращает ``None``, и подбор продолжается по описанию и названию.
Никакое исключение не выходит наружу — пайплайн не имеет права падать из-за
картинки.
"""

from __future__ import annotations

import io
import threading
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

#: Хосты фотографий Авито (подстраховка от SSRF: качаем только снимки с CDN).
ALLOWED_PHOTO_HOSTS: tuple[str, ...] = ("img.avito.st", "avito.ru")

#: Сколько живёт результат измерения (секунды).
DEFAULT_TTL_SEC = 3600

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_LOCK = threading.Lock()


@dataclass
class PhotoTraits:
    """Измеренные признаки фотографии объявления."""

    app_colors: list[str] = field(default_factory=list)
    colors_hex: list[str] = field(default_factory=list)
    dominant_hex: str = ""
    brightness: float = 0.0
    saturation: float = 0.0
    contrast: float = 0.0
    background_flat: bool = False
    width: int = 0
    height: int = 0
    shots: int = 1

    @property
    def is_dark(self) -> bool:
        return self.brightness < 0.35

    def to_dict(self) -> dict[str, Any]:
        return {
            "colors": list(self.app_colors),
            "colors_hex": list(self.colors_hex),
            "dominant_hex": self.dominant_hex,
            "brightness": round(self.brightness, 3),
            "saturation": round(self.saturation, 3),
            "contrast": round(self.contrast, 3),
            "background_flat": self.background_flat,
            "width": self.width,
            "height": self.height,
            "shots": self.shots,
        }


def _host_allowed(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return any(host == allowed or host.endswith("." + allowed) for allowed in ALLOWED_PHOTO_HOSTS)


def _nearest_app_colors(rgb: tuple[int, int, int], limit: int = 3) -> tuple[list[str], list[str]]:
    """Ближайшие цвета палитры приложения к измеренному оттенку."""
    from ..engine.colors import COLORS  # локальный импорт: модуль опционален

    def to_rgb(value: str) -> tuple[int, int, int]:
        value = value.lstrip("#")
        return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)

    target = rgb
    ordered = sorted(
        COLORS.values(),
        key=lambda spec: sum((a - b) ** 2 for a, b in zip(to_rgb(spec.hex), target)),
    )
    return [spec.id for spec in ordered[:limit]], [spec.hex for spec in ordered[:limit]]


def analyze_bytes(data: bytes, *, shots: int = 1) -> PhotoTraits | None:
    """Измерить признаки фотографии. ``None`` — если разобрать не удалось."""
    try:
        from PIL import Image, ImageStat
    except Exception:  # Pillow не установлен — фича мягко выключается
        return None
    try:
        with Image.open(io.BytesIO(data)) as image:
            image = image.convert("RGB")
            width, height = image.size
            thumb = image.copy()
            thumb.thumbnail((96, 96))
            stat = ImageStat.Stat(thumb)
            r, g, b = (channel / 255.0 for channel in stat.mean[:3])
            brightness = (0.299 * r + 0.587 * g + 0.114 * b)
            highest, lowest = max(r, g, b), min(r, g, b)
            saturation = 0.0 if highest <= 0 else (highest - lowest) / highest
            contrast = sum(stat.stddev[:3]) / (3 * 255.0)

            # Доминирующие оттенки: квантование до 6 цветов и веса по пикселям.
            quantized = thumb.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
            palette = quantized.getpalette() or []
            counts = sorted(quantized.getcolors() or [], reverse=True)
            colors: list[str] = []
            hexes: list[str] = []
            for _count, index in counts[:4]:
                base = index * 3
                rgb = tuple(palette[base : base + 3]) if len(palette) >= base + 3 else (128, 128, 128)
                near_ids, near_hex = _nearest_app_colors(rgb, limit=1)  # type: ignore[arg-type]
                if near_ids and near_ids[0] not in colors:
                    colors.append(near_ids[0])
                    hexes.append(near_hex[0])

            # Однородный фон (студийная съёмка): первые два оттенка занимают
            # почти весь кадр и различаются незначительно.
            total = sum(count for count, _index in counts) or 1
            background_flat = bool(counts) and (counts[0][0] / total) > 0.62
            dominant = "#%02x%02x%02x" % tuple(stat.mean[:3])  # type: ignore[assignment]
            return PhotoTraits(
                app_colors=colors[:3],
                colors_hex=hexes[:3],
                dominant_hex=dominant,
                brightness=brightness,
                saturation=saturation,
                contrast=contrast,
                background_flat=background_flat,
                width=width,
                height=height,
                shots=shots,
            )
    except Exception:
        return None


def traits_for_url(
    url: str,
    *,
    timeout: float = 3.0,
    ttl_sec: int = DEFAULT_TTL_SEC,
    client: Any | None = None,
) -> dict[str, Any] | None:
    """Скачать снимок и измерить его. Никогда не бросает исключений.

    Кэш в памяти процесса: один и тот же снимок измеряется один раз, поэтому
    подбор образа не превращается в десятки сетевых запросов.
    """
    if not url or not _host_allowed(url):
        return None
    now = time.monotonic()
    with _LOCK:
        cached = _CACHE.get(url)
        if cached is not None and now - cached[0] < ttl_sec:
            return cached[1] or None

    traits: PhotoTraits | None = None
    try:
        if client is not None:
            response = client.get(url, timeout=timeout)
            data = response.content
        else:
            import httpx

            response = httpx.get(
                url,
                timeout=httpx.Timeout(timeout, connect=min(2.0, timeout)),
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
                    ),
                    "Accept": "image/avif,image/webp,image/jpeg,image/png,*/*;q=0.8",
                },
            )
            if response.status_code != 200:
                raise RuntimeError(f"http {response.status_code}")
            data = response.content
        if data:
            traits = analyze_bytes(data)
    except Exception:
        traits = None

    payload = traits.to_dict() if traits is not None else None
    with _LOCK:
        _CACHE[url] = (now, payload or {})
        if len(_CACHE) > 400:
            oldest = sorted(_CACHE, key=lambda key: _CACHE[key][0])[:200]
            for key in oldest:
                _CACHE.pop(key, None)
    return payload


def clear_cache() -> None:
    with _LOCK:
        _CACHE.clear()


__all__ = ["ALLOWED_PHOTO_HOSTS", "PhotoTraits", "analyze_bytes", "clear_cache", "traits_for_url"]
