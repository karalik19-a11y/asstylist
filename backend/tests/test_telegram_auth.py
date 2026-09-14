"""Tests for Telegram Mini App auth."""

from __future__ import annotations

import pytest

from app.config import settings
from app.telegram.auth import TelegramAuthError, authenticate, build_init_data, validate_init_data

TOKEN = "123456:TEST-TOKEN"


@pytest.fixture()
def with_bot_token(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", TOKEN)
    return TOKEN


def test_valid_init_data_is_accepted(with_bot_token):
    init_data = build_init_data(with_bot_token, user_id=42, username="anna")
    payload = validate_init_data(init_data, with_bot_token)
    assert payload["id"] == 42
    assert payload["username"] == "anna"


def test_tampered_hash_is_rejected(with_bot_token):
    init_data = build_init_data(with_bot_token)
    tampered = init_data.replace(init_data[-8:], "00000000")
    with pytest.raises(TelegramAuthError):
        validate_init_data(tampered, with_bot_token)


def test_wrong_token_is_rejected(with_bot_token):
    init_data = build_init_data(with_bot_token)
    with pytest.raises(TelegramAuthError):
        validate_init_data(init_data, "999:WRONG")


def test_stale_init_data_is_rejected(with_bot_token):
    init_data = build_init_data(with_bot_token, max_age_sec=settings.telegram_auth_max_age_sec + 100)
    with pytest.raises(TelegramAuthError):
        validate_init_data(init_data, with_bot_token)


def test_missing_hash_is_rejected(with_bot_token):
    with pytest.raises(TelegramAuthError):
        validate_init_data("user=%7B%7D&auth_date=1", with_bot_token)


def test_authenticate_uses_telegram_identity(with_bot_token):
    init_data = build_init_data(with_bot_token, user_id=7, username="oleg")
    identity = authenticate(init_data)
    assert identity.telegram_id == "7"
    assert identity.username == "oleg"
    assert identity.is_demo is False


def test_demo_mode_issues_local_identity(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    monkeypatch.setattr(settings, "demo_mode", True)
    identity = authenticate(None, "guest-123")
    assert identity.telegram_id.startswith("demo-")
    assert identity.is_demo is True


def test_demo_identity_is_stable_for_the_same_input(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    monkeypatch.setattr(settings, "demo_mode", True)
    assert authenticate(None, "same").telegram_id == authenticate(None, "same").telegram_id
    assert authenticate(None, "a").telegram_id != authenticate(None, "b").telegram_id


def test_without_token_and_demo_off_auth_fails(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    monkeypatch.setattr(settings, "demo_mode", False)
    with pytest.raises(TelegramAuthError):
        authenticate(None, None)
