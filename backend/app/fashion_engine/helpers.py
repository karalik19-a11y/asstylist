"""Небольшие утилиты (порт ``src/utils/helpers.js``).

``uid()`` из оригинала использовал ``Math.random()``; здесь он заменён на
детерминированный ``stable_id`` — приложение обещает, что «одинаковый вход →
одинаковый образ», а случайные идентификаторы ломали бы это обещание.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_id(*parts: Any, prefix: str = "id_") -> str:
    """Детерминированный аналог ``uid()``: одинаковый вход → одинаковый id."""
    payload = "|".join("" if part is None else str(part) for part in parts)
    return prefix + hashlib.sha1(payload.encode("utf-8")).hexdigest()[:14]


def deep_clone(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def clamp(num: float, low: float, high: float) -> float:
    return max(low, min(high, num))


def int_clamp(num: float, low: int = 0, high: int = 100) -> int:
    return int(max(low, min(high, round(num))))


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
