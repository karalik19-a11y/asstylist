"""Tests for the Telegram bot webhook (answers /start with a Mini App button)."""

from __future__ import annotations

import json

import httpx

from app.api.telegram import build_update_reply, web_app_button_markup
from app.config import settings
from app.telegram.botapi import configure_bot, send_message, set_webhook

TOKEN = "123456:TEST-BOT-TOKEN"
URL = "https://asstylist.example.com"
HOOK = f"{URL}/api/telegram/webhook"
BOT_INFO = {"id": 42, "is_bot": True, "first_name": "asStylist", "username": "asstylist_bot"}


def ok_transport(result=True) -> httpx.MockTransport:
    return httpx.MockTransport(lambda request: httpx.Response(200, json={"ok": True, "result": result}))


def test_set_webhook_sends_url_and_secret():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True, "result": True})

    assert set_webhook(TOKEN, HOOK, secret_token="s3cret", transport=httpx.MockTransport(handler)) is True
    assert seen["url"].endswith(f"/bot{TOKEN}/setWebhook")
    assert seen["body"]["url"] == HOOK
    assert seen["body"]["secret_token"] == "s3cret"
    assert seen["body"]["allowed_updates"] == ["message"]


def test_send_message_carries_markup():
    seen: dict = {}
    markup = web_app_button_markup(URL)

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 7}})

    result = send_message(TOKEN, 99, "hi", reply_markup=markup, transport=httpx.MockTransport(handler))
    assert result["message_id"] == 7
    assert seen["body"]["chat_id"] == 99
    assert seen["body"]["reply_markup"]["inline_keyboard"][0][0]["web_app"]["url"] == URL


def test_configure_bot_sets_webhook_when_given():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        method = str(request.url).rsplit("/", 1)[-1]
        calls.append(method)
        result = BOT_INFO if method == "getMe" else True
        return httpx.Response(200, json={"ok": True, "result": result})

    outcome = configure_bot(
        TOKEN, URL, webhook_url=HOOK, webhook_secret="s3cret", transport=httpx.MockTransport(handler)
    )
    assert calls == ["getMe", "setChatMenuButton", "setMyCommands", "setWebhook"]
    assert any("webhook" in action for action in outcome["actions"])


def test_configure_bot_without_webhook_is_unchanged():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        method = str(request.url).rsplit("/", 1)[-1]
        calls.append(method)
        result = BOT_INFO if method == "getMe" else True
        return httpx.Response(200, json={"ok": True, "result": result})

    configure_bot(TOKEN, URL, transport=httpx.MockTransport(handler))
    assert calls == ["getMe", "setChatMenuButton", "setMyCommands"]


def test_build_update_reply_start_help_looks():
    chat_id, text, markup = build_update_reply({"message": {"chat": {"id": 5}, "text": "/start"}}, URL)
    assert chat_id == 5
    assert "asStylist" in text
    assert markup["inline_keyboard"][0][0]["web_app"]["url"] == URL

    _, help_text, _ = build_update_reply({"message": {"chat": {"id": 5}, "text": "/help"}}, URL)
    assert "Как это работает" in help_text

    _, looks_text, _ = build_update_reply({"message": {"chat": {"id": 5}, "text": "/looks"}}, URL)
    assert "приложении" in looks_text

    _, fallback, _ = build_update_reply({"message": {"chat": {"id": 5}, "text": "привет"}}, URL)
    assert "кнопку ниже" in fallback


def test_build_update_reply_ignores_updates_without_chat():
    assert build_update_reply({"edited_message": {}}, URL)[0] is None
    assert build_update_reply({}, URL)[0] is None


def test_webhook_rejects_bad_secret(client):
    response = client.post(
        "/api/telegram/webhook",
        json={"message": {"chat": {"id": 1}, "text": "/start"}},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
    )
    assert response.status_code == 403


def test_webhook_rejects_missing_secret(client):
    response = client.post("/api/telegram/webhook", json={"message": {"chat": {"id": 1}, "text": "/start"}})
    assert response.status_code == 403


def test_webhook_without_token_acks_but_handles_nothing(client, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    response = client.post(
        "/api/telegram/webhook",
        json={"message": {"chat": {"id": 1}, "text": "/start"}},
        headers={"X-Telegram-Bot-Api-Secret-Token": settings.admin_token},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "handled": False}


def test_webhook_start_sends_a_web_app_button(client, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", TOKEN)
    monkeypatch.setattr(settings, "telegram_web_app_url", URL)

    import app.api.telegram as telegram_api

    sent: dict = {}

    def fake_send(token, chat_id, text, *, reply_markup=None, transport=None):
        sent.update(token=token, chat_id=chat_id, text=text, reply_markup=reply_markup)
        return {"message_id": 1}

    monkeypatch.setattr(telegram_api, "send_message", fake_send)

    response = client.post(
        "/api/telegram/webhook",
        json={"message": {"chat": {"id": 77}, "text": "/start"}},
        headers={"X-Telegram-Bot-Api-Secret-Token": settings.admin_token},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "handled": True}
    # TestClient runs BackgroundTasks before returning, so the reply is sent.
    assert sent["chat_id"] == 77
    assert sent["token"] == TOKEN
    button = sent["reply_markup"]["inline_keyboard"][0][0]
    assert button["web_app"]["url"] == URL


def test_webhook_send_failure_still_acks(client, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", TOKEN)
    monkeypatch.setattr(settings, "telegram_web_app_url", URL)

    import app.api.telegram as telegram_api
    from app.telegram.botapi import BotApiError

    def boom(token, chat_id, text, *, reply_markup=None, transport=None):
        raise BotApiError("down")

    monkeypatch.setattr(telegram_api, "send_message", boom)

    response = client.post(
        "/api/telegram/webhook",
        json={"message": {"chat": {"id": 77}, "text": "/start"}},
        headers={"X-Telegram-Bot-Api-Secret-Token": settings.admin_token},
    )
    assert response.status_code == 200
    assert response.json()["handled"] is True


def test_setup_endpoint_registers_the_webhook(client, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    monkeypatch.setattr(settings, "telegram_web_app_url", None)
    monkeypatch.setattr(settings, "demo_mode", True)

    import app.api.telegram as telegram_api

    seen: dict = {}

    def fake_configure(token, url, **kwargs):
        seen.update(token=token, url=url, kwargs=kwargs)
        return {"bot": BOT_INFO, "web_app_url": url, "actions": []}

    monkeypatch.setattr(telegram_api, "configure_bot", fake_configure)

    response = client.post(
        "/api/telegram/setup",
        json={"bot_token": TOKEN, "web_app_url": URL, "persist": False, "keep_demo_access": True},
    )
    assert response.status_code == 200
    assert seen["kwargs"]["webhook_url"] == f"{URL}/api/telegram/webhook"
    assert seen["kwargs"]["webhook_secret"] == settings.admin_token
