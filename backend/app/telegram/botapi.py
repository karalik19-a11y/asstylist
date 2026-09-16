"""Telegram Bot API client — just enough to wire a Mini App to a bot.

Everything is one small function so it can be unit-tested with a mocked
transport, and so a failure here never takes the API down.
"""

from __future__ import annotations

from typing import Any

import httpx

BOT_API_BASE = "https://api.telegram.org"
TIMEOUT_SEC = 15.0

DEFAULT_COMMANDS = [
    {"command": "start", "description": "Собрать образ"},
    {"command": "looks", "description": "Мои образы"},
    {"command": "help", "description": "Как это работает"},
]


class BotApiError(RuntimeError):
    """Raised when the Bot API rejects the token or the request."""


def _call(
    method: str,
    token: str,
    payload: dict[str, Any] | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    if not token or ":" not in token:
        raise BotApiError("Токен бота выглядит некорректно (ожидается вид 123456:ABC-...)")
    url = f"{BOT_API_BASE}/bot{token}/{method}"
    try:
        with httpx.Client(timeout=TIMEOUT_SEC, transport=transport) as client:
            response = client.post(url, json=payload or {})
    except httpx.HTTPError as exc:
        raise BotApiError(f"Не удалось связаться с Telegram: {type(exc).__name__}") from exc

    if response.status_code != 200:
        raise BotApiError(f"Telegram вернул HTTP {response.status_code}")
    try:
        body = response.json()
    except ValueError as exc:
        raise BotApiError("Telegram вернул не-JSON ответ") from exc
    if not body.get("ok"):
        raise BotApiError(str(body.get("description") or "Telegram отклонил запрос"))
    return body.get("result")


def get_me(token: str, *, transport: httpx.BaseTransport | None = None) -> dict[str, Any]:
    return _call("getMe", token, transport=transport)


def set_chat_menu_button(
    token: str,
    web_app_url: str,
    *,
    label: str = "asStylist",
    transport: httpx.BaseTransport | None = None,
) -> bool:
    payload = {
        "menu_button": {
            "type": "web_app",
            "text": label,
            "web_app": {"url": web_app_url},
        }
    }
    return bool(_call("setChatMenuButton", token, payload, transport=transport))


def set_my_commands(
    token: str,
    commands: list[dict[str, str]] | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> bool:
    return bool(_call("setMyCommands", token, {"commands": commands or DEFAULT_COMMANDS}, transport=transport))


def set_webhook(
    token: str,
    url: str,
    *,
    secret_token: str | None = None,
    transport: httpx.BaseTransport | None = None,
) -> bool:
    """Point the bot's updates at our ``POST /api/telegram/webhook`` endpoint."""
    payload: dict[str, Any] = {"url": url, "allowed_updates": ["message"]}
    if secret_token:
        payload["secret_token"] = secret_token
    return bool(_call("setWebhook", token, payload, transport=transport))


def delete_webhook(token: str, *, transport: httpx.BaseTransport | None = None) -> bool:
    return bool(_call("deleteWebhook", token, {"drop_pending_updates": True}, transport=transport))


def send_message(
    token: str,
    chat_id: int,
    text: str,
    *,
    reply_markup: dict[str, Any] | None = None,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    """Send a plain-text reply. ``reply_markup`` carries the web_app button."""
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    return _call("sendMessage", token, payload, transport=transport)


def validate_web_app_url(url: str, *, what: str = "Web App URL") -> str:
    """Telegram only accepts absolute HTTPS URLs for a Mini App (and webhooks)."""
    from urllib.parse import urlparse

    parsed = urlparse(url or "")
    if parsed.scheme != "https":
        raise BotApiError(f"{what} должен быть абсолютным и начинаться с https://")
    if not parsed.hostname:
        raise BotApiError(f"В {what} нет хоста")
    if parsed.hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
        raise BotApiError("Telegram не откроет localhost — нужен публичный https-адрес")
    return url.rstrip("/")


def configure_bot(
    token: str,
    web_app_url: str,
    *,
    webhook_url: str | None = None,
    webhook_secret: str | None = None,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    """Validate the token, attach the Mini App, set commands and (optionally) the webhook."""
    url = validate_web_app_url(web_app_url)
    bot = get_me(token, transport=transport)
    actions: list[str] = []

    set_chat_menu_button(token, url, transport=transport)
    actions.append(f"кнопка меню → {url}")

    try:
        set_my_commands(token, transport=transport)
        actions.append("команды /start /looks /help")
    except BotApiError as exc:  # commands are a nice-to-have, the Mini App is not
        actions.append(f"команды не установлены ({exc})")

    if webhook_url:
        try:
            hook = validate_web_app_url(webhook_url, what="Webhook URL")
            set_webhook(token, hook, secret_token=webhook_secret, transport=transport)
            actions.append(f"webhook → {hook}")
        except BotApiError as exc:  # the Mini App works via the menu button even without it
            actions.append(f"webhook не установлен ({exc})")

    return {
        "bot": {
            "id": bot.get("id"),
            "username": bot.get("username"),
            "first_name": bot.get("first_name"),
        },
        "web_app_url": url,
        "actions": actions,
    }
