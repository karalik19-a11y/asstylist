"""Look service: создание пользователя и устойчивость к гонкам (демо-режим)."""

from __future__ import annotations

from sqlalchemy import select

from app.db import SessionLocal
from app.models import User
from app.services import look_service
from app.telegram.auth import TelegramUser


def test_get_or_create_user_is_idempotent(session):
    identity = TelegramUser(telegram_id="svc-demo", username="demo_user", first_name="Гость", is_demo=True)
    first = look_service.get_or_create_user(session, identity)
    assert first.id is not None

    updated = TelegramUser(telegram_id="svc-demo", username="demo_user", first_name="Пользователь", is_demo=True)
    again = look_service.get_or_create_user(session, updated)
    assert again.id == first.id
    assert again.first_name == "Пользователь"

    rows = session.execute(select(User).where(User.telegram_id == "svc-demo")).scalars().all()
    assert len(rows) == 1


def test_concurrent_demo_user_creation_does_not_fail(session):
    """Второй параллельный запрос вставил ту же строку — первый читает её, а не падает."""
    identity = TelegramUser(telegram_id="race-demo", username="demo_user", first_name="Гость", is_demo=True)

    other = SessionLocal()
    try:
        other.add(
            User(
                telegram_id="race-demo",
                username="demo_user",
                first_name="Гость",
                is_demo=True,
            )
        )
        other.commit()
    finally:
        other.close()

    # Сессия «первого запроса» ничего не знает о вставленной строке; раньше
    # здесь был IntegrityError (500 на /api/looks).
    resolved = look_service.get_or_create_user(session, identity)
    assert resolved.telegram_id == "race-demo"
    assert resolved.is_demo is True
