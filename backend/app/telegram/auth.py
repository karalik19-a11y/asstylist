"""Telegram Mini App auth.

Implements the standard `initData` HMAC check described in the Telegram Mini
Apps docs. In demo mode (no bot token configured) it issues a local demo user
instead, so the whole flow is testable outside Telegram.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl

from ..config import settings


class TelegramAuthError(RuntimeError):
    pass


@dataclass
class TelegramUser:
    telegram_id: str
    username: str | None
    first_name: str | None
    is_demo: bool


def validate_init_data(init_data: str, bot_token: str, max_age_sec: int | None = None) -> dict[str, Any]:
    """Validate `window.Telegram.WebApp.initData`. Raises TelegramAuthError."""
    if not init_data:
        raise TelegramAuthError("empty init_data")
    try:
        pairs = parse_qsl(init_data, strict_parsing=True)
    except ValueError as exc:
        raise TelegramAuthError("malformed init_data") from exc
    data = dict(pairs)

    received_hash = data.pop("hash", None)
    if not received_hash:
        raise TelegramAuthError("missing hash")

    max_age = settings.telegram_auth_max_age_sec if max_age_sec is None else max_age_sec
    auth_date = int(data.get("auth_date", 0))
    if max_age > 0 and auth_date and time.time() - auth_date > max_age:
        raise TelegramAuthError("init_data is too old")

    data_check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, received_hash):
        raise TelegramAuthError("hash mismatch")

    user_raw = data.get("user")
    if not user_raw:
        raise TelegramAuthError("no user in init_data")
    return json.loads(user_raw)


def authenticate(init_data: str | None, demo_user_id: str | None = None) -> TelegramUser:
    """Resolve the caller. Falls back to a demo identity in demo mode."""
    if init_data and settings.telegram_bot_token:
        try:
            payload = validate_init_data(init_data, settings.telegram_bot_token)
            return TelegramUser(
                telegram_id=str(payload.get("id")),
                username=payload.get("username"),
                first_name=payload.get("first_name"),
                is_demo=False,
            )
        except TelegramAuthError:
            if not settings.demo_mode:
                raise
    if settings.demo_mode:
        raw = demo_user_id or init_data or "demo"
        digest = hashlib.sha256(raw.encode()).hexdigest()[:8]
        return TelegramUser(
            telegram_id=f"demo-{digest}",
            username="demo_user",
            first_name="Гость",
            is_demo=True,
        )
    raise TelegramAuthError("Telegram bot token is not configured")


def build_init_data(bot_token: str, user_id: int = 1, username: str = "test", max_age_sec: int = 0) -> str:
    """Helper for tests: produce a valid signed initData string."""
    from urllib.parse import urlencode

    auth_date = int(time.time()) if max_age_sec == 0 else int(time.time()) - max_age_sec
    user_json = json.dumps({"id": user_id, "username": username, "first_name": "Test"}, separators=(",", ":"))
    data = {"user": user_json, "auth_date": str(auth_date), "query_id": "test-query"}
    check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    data["hash"] = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(data)
