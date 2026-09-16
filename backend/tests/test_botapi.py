"""Tests for the Telegram Bot API client and the one-click bot wiring."""

from __future__ import annotations

import json

import httpx
import pytest

from app.config import settings
from app.telegram.botapi import (
    BotApiError,
    configure_bot,
    get_me,
    set_chat_menu_button,
    set_my_commands,
    validate_web_app_url,
)

TOKEN = "123456:TEST-BOT-TOKEN"
URL = "https://asstylist.example.com"

BOT_INFO = {"id": 42, "is_bot": True, "first_name": "asStylist", "username": "asstylist_bot"}


def transport_for(handler) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def ok_transport(result) -> httpx.MockTransport:
    return transport_for(lambda request: httpx.Response(200, json={"ok": True, "result": result}))


def test_get_me_returns_bot_info():
    bot = get_me(TOKEN, transport=ok_transport(BOT_INFO))
    assert bot["username"] == "asstylist_bot"


def test_set_chat_menu_button_sends_a_web_app_button():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True, "result": True})

    assert set_chat_menu_button(TOKEN, URL, transport=transport_for(handler)) is True
    assert seen["url"].endswith(f"/bot{TOKEN}/setChatMenuButton")
    assert seen["body"]["menu_button"]["type"] == "web_app"
    assert seen["body"]["menu_button"]["web_app"]["url"] == URL


def test_set_my_commands_sends_the_menu():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True, "result": True})

    assert set_my_commands(TOKEN, transport=transport_for(handler)) is True
    assert [c["command"] for c in seen["body"]["commands"]] == ["start", "looks", "help"]


def test_malformed_token_is_rejected_before_any_request():
    with pytest.raises(BotApiError):
        get_me("not-a-token", transport=ok_transport(BOT_INFO))


def test_telegram_error_description_is_surfaced():
    transport = transport_for(lambda request: httpx.Response(200, json={"ok": False, "description": "Unauthorized"}))
    with pytest.raises(BotApiError, match="Unauthorized"):
        get_me(TOKEN, transport=transport)


def test_http_error_is_wrapped():
    transport = transport_for(lambda request: httpx.Response(404, json={"ok": False}))
    with pytest.raises(BotApiError, match="HTTP 404"):
        get_me(TOKEN, transport=transport)


def test_network_error_is_wrapped_not_raised():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no network")

    with pytest.raises(BotApiError, match="не удалось связаться|Не удалось связаться"):
        get_me(TOKEN, transport=transport_for(handler))


@pytest.mark.parametrize(
    "url",
    ["http://asstylist.example.com", "localhost:8000", "https://localhost:8000", "https://127.0.0.1", "ftp://x.example", ""],
)
def test_invalid_web_app_urls_are_rejected(url):
    with pytest.raises(BotApiError):
        validate_web_app_url(url)


def test_valid_web_app_url_is_normalised():
    assert validate_web_app_url("https://asstylist.example.com/") == "https://asstylist.example.com"


def test_configure_bot_sets_menu_and_commands():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        method = str(request.url).rsplit("/", 1)[-1]
        calls.append(method)
        result = BOT_INFO if method == "getMe" else True
        return httpx.Response(200, json={"ok": True, "result": result})

    outcome = configure_bot(TOKEN, URL, transport=transport_for(handler))
    assert outcome["bot"]["username"] == "asstylist_bot"
    assert outcome["web_app_url"] == URL
    assert calls == ["getMe", "setChatMenuButton", "setMyCommands"]


def test_configure_bot_survives_a_commands_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        method = str(request.url).rsplit("/", 1)[-1]
        if method == "setMyCommands":
            return httpx.Response(200, json={"ok": False, "description": "commands are disabled"})
        result = BOT_INFO if method == "getMe" else True
        return httpx.Response(200, json={"ok": True, "result": result})

    outcome = configure_bot(TOKEN, URL, transport=transport_for(handler))
    assert outcome["bot"]["username"] == "asstylist_bot"
    assert any("команды не установлены" in action for action in outcome["actions"])


def test_status_endpoint_reports_unconfigured(client):
    body = client.get("/api/telegram/status").json()
    assert body["configured"] is False
    assert body["demo_mode"] is True
    assert body["bot"] is None


def test_setup_endpoint_connects_the_bot(client, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    monkeypatch.setattr(settings, "telegram_web_app_url", None)
    monkeypatch.setattr(settings, "demo_mode", True)

    import app.api.telegram as telegram_api

    monkeypatch.setattr(
        telegram_api,
        "configure_bot",
        lambda token, url, **kwargs: {"bot": BOT_INFO, "web_app_url": url, "actions": ["кнопка меню", "команды"]},
    )

    response = client.post(
        "/api/telegram/setup",
        json={"bot_token": TOKEN, "web_app_url": URL, "persist": False, "keep_demo_access": True},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True
    assert body["bot"]["username"] == "asstylist_bot"
    assert "asstylist_bot" in body["next_step"]
    # settings are updated in place, so no restart is needed
    assert settings.telegram_bot_token == TOKEN
    assert settings.telegram_web_app_url == URL
    assert settings.demo_mode is True


def test_setup_endpoint_reports_telegram_errors_as_422(client, monkeypatch):
    import app.api.telegram as telegram_api

    def boom(token, url, **kwargs):
        raise BotApiError("Unauthorized")

    monkeypatch.setattr(telegram_api, "configure_bot", boom)
    response = client.post("/api/telegram/setup", json={"bot_token": TOKEN, "web_app_url": URL, "persist": False})
    assert response.status_code == 422
    assert response.json()["detail"] == "Unauthorized"


def test_setup_endpoint_never_writes_the_env_when_persist_is_off(client, monkeypatch):
    import app.api.telegram as telegram_api

    monkeypatch.setattr(
        telegram_api,
        "configure_bot",
        lambda token, url, **kwargs: {"bot": BOT_INFO, "web_app_url": url, "actions": []},
    )
    written: dict = {}
    monkeypatch.setattr(telegram_api, "persist_env", lambda updates: written.update(updates) or [])

    client.post("/api/telegram/setup", json={"bot_token": TOKEN, "web_app_url": URL, "persist": False})
    assert written == {}


def test_persist_env_round_trip(tmp_path, monkeypatch):
    from app.config import persist_env

    env_file = tmp_path / ".env"
    env_file.write_text("# comment\nDEMO_MODE=true\nAI_PROVIDER=local\n", encoding="utf-8")

    updated = persist_env({"TELEGRAM_BOT_TOKEN": "1:abc", "DEMO_MODE": "false"}, env_file=str(env_file))
    assert updated == ["DEMO_MODE", "TELEGRAM_BOT_TOKEN"]

    content = env_file.read_text(encoding="utf-8")
    assert "# comment" in content, "unrelated lines must survive"
    assert "DEMO_MODE=false" in content
    assert "AI_PROVIDER=local" in content
    assert "TELEGRAM_BOT_TOKEN=1:abc" in content
