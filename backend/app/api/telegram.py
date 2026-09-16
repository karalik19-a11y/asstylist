"""Telegram auth + one-click bot wiring."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import persist_env, settings
from ..db import get_session
from ..schemas import AuthRequest, AuthResponse, UserOut
from ..services.look_service import get_or_create_user
from ..telegram.auth import TelegramAuthError, authenticate
from ..telegram.botapi import BotApiError, configure_bot, get_me, send_message

router = APIRouter(prefix="/api/telegram", tags=["telegram"])

#: Path Telegram POSTs bot updates to (registered via setWebhook).
WEBHOOK_PATH = "/api/telegram/webhook"


class SetupRequest(BaseModel):
    bot_token: str = Field(min_length=10, max_length=200)
    web_app_url: str = Field(min_length=8, max_length=500)
    #: When true the browser demo identity keeps working next to real Telegram auth.
    keep_demo_access: bool = True
    persist: bool = True


class SetupResponse(BaseModel):
    ok: bool
    bot: dict[str, Any]
    web_app_url: str
    actions: list[str]
    persisted_keys: list[str]
    demo_mode: bool
    next_step: str


@router.post("/auth", response_model=AuthResponse)
def auth(payload: AuthRequest, session: Session = Depends(get_session)) -> AuthResponse:
    try:
        identity = authenticate(payload.init_data, payload.demo_user_id)
    except TelegramAuthError as exc:
        raise HTTPException(status_code=401, detail=f"Telegram auth failed: {exc}") from exc

    if payload.first_name:
        identity.first_name = payload.first_name
    if payload.username:
        identity.username = payload.username

    user = get_or_create_user(session, identity)
    return AuthResponse(
        user=UserOut(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            is_demo=user.is_demo,
        ),
        demo=settings.demo_mode,
        mode="demo" if settings.demo_mode else "telegram",
        web_app_url=settings.telegram_web_app_url,
    )


@router.get("/status")
def status() -> dict[str, Any]:
    """Is a bot connected? Safe to call: never returns the token itself."""
    configured = bool(settings.telegram_bot_token)
    bot: dict[str, Any] | None = None
    error: str | None = None
    if configured:
        try:
            info = get_me(settings.telegram_bot_token)
            bot = {"id": info.get("id"), "username": info.get("username"), "first_name": info.get("first_name")}
        except BotApiError as exc:
            error = str(exc)
    return {
        "configured": configured,
        "bot": bot,
        "bot_link": f"https://t.me/{bot['username']}" if bot and bot.get("username") else None,
        "web_app_url": settings.telegram_web_app_url,
        "demo_mode": settings.demo_mode,
        "init_data_expected": configured,
        "error": error,
    }


@router.post("/setup", response_model=SetupResponse)
def setup(
    payload: SetupRequest,
    x_admin_token: str | None = Header(default=None),
) -> SetupResponse:
    """Attach this Mini App to a bot: validates the token and sets the menu button.

    Allowed while no bot is configured yet (so the owner can self-serve), or with
    the admin token once the app is live.
    """
    already_configured = bool(settings.telegram_bot_token)
    if already_configured and not settings.demo_mode and x_admin_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Бот уже подключён: требуется ADMIN_TOKEN")

    try:
        base = payload.web_app_url.rstrip("/")
        result = configure_bot(
            payload.bot_token,
            base,
            webhook_url=f"{base}{WEBHOOK_PATH}",
            webhook_secret=settings.admin_token,
        )
    except BotApiError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    settings.telegram_bot_token = payload.bot_token
    settings.telegram_web_app_url = result["web_app_url"]
    if not payload.keep_demo_access:
        settings.demo_mode = False

    persisted: list[str] = []
    if payload.persist:
        persisted = persist_env(
            {
                "TELEGRAM_BOT_TOKEN": payload.bot_token,
                "TELEGRAM_WEB_APP_URL": result["web_app_url"],
                "DEMO_MODE": "true" if settings.demo_mode else "false",
            }
        )

    return SetupResponse(
        ok=True,
        bot=result["bot"],
        web_app_url=result["web_app_url"],
        actions=result["actions"],
        persisted_keys=persisted,
        demo_mode=settings.demo_mode,
        next_step=(
            f"Откройте https://t.me/{result['bot'].get('username')} в Telegram — "
            "кнопка меню слева от поля ввода уже открывает asStylist."
            if result["bot"].get("username")
            else "Бот подключён."
        ),
    )


# --- bot webhook: /start answers with a Mini App button ----------------------


def web_app_button_markup(web_app_url: str) -> dict[str, Any]:
    return {"inline_keyboard": [[{"text": "✨ Открыть asStylist", "web_app": {"url": web_app_url}}]]}


START_TEXT = (
    "👋 <b>asStylist</b> — персональный стилист.\n\n"
    "Соберу образ под ваш стиль, фигуру и бюджет — вещи подберу "
    "на <b>Авито</b> с фото, ценами и ссылками.\n\n"
    "Нажмите кнопку ниже, чтобы начать 👇"
)

HELP_TEXT = (
    "<b>Как это работает</b>\n\n"
    "1️⃣ Откройте приложение кнопкой ниже\n"
    "2️⃣ Ответьте на 5 вопросов (стиль, настроение, параметры)\n"
    "3️⃣ Получите образ с вещами с Авито\n\n"
    "Команды: /start — начать заново, /looks — мои образы (в приложении)."
)

LOOKS_TEXT = "🧥 Ваши образы живут в приложении — откройте его кнопкой ниже 👇"

FALLBACK_TEXT = "Нажмите кнопку ниже — подберём вам образ ✨"


def build_update_reply(update: dict[str, Any], web_app_url: str | None) -> tuple[int | None, str, dict | None]:
    """Pure decision: which (chat_id, text, markup) answers an incoming update."""
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return None, "", None
    text = str(message.get("text") or "").strip().split()[0:1]
    command = text[0].lower().split("@")[0] if text else ""
    markup = web_app_button_markup(web_app_url) if web_app_url else None
    if command == "/start":
        return chat_id, START_TEXT, markup
    if command == "/help":
        return chat_id, HELP_TEXT, markup
    if command == "/looks":
        return chat_id, LOOKS_TEXT, markup
    return chat_id, FALLBACK_TEXT, markup


def _send_update_reply(token: str, chat_id: int, text: str, markup: dict | None) -> None:
    try:
        send_message(token, chat_id, text, reply_markup=markup)
    except BotApiError:
        pass  # send failures must never crash the webhook; Telegram retries


@router.post("/webhook")
def webhook(
    update: dict[str, Any],
    background: BackgroundTasks,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """Receive bot updates from Telegram. Always 200s: retries are Telegram's job."""
    if x_telegram_bot_api_secret_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="bad webhook secret")
    token = settings.telegram_bot_token
    if not token:
        return {"ok": True, "handled": False}
    chat_id, text, markup = build_update_reply(update, settings.telegram_web_app_url)
    if chat_id is None:
        return {"ok": True, "handled": False}
    background.add_task(_send_update_reply, token, chat_id, text, markup)
    return {"ok": True, "handled": True}
