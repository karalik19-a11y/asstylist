"""Память пользователя: рост и вес.

Человек вводит рост и вес один раз. При следующем входе сервис предлагает
выбор — «использовать сохранённые данные» или «ввести новые». Хранится ровно
то, о чём просили: рост и вес; стиль, настроение и бюджет спрашиваются каждый
раз заново (иначе образ застынет на одном вкусе).

Данные лежат в SQLite рядом с образами (таблица ``user_memory``), поэтому
память работает и в Telegram, и в браузере: идентификация та же, что у образов
(``init_data`` мини-приложения или демо-идентификатор клиента).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import User, UserMemory
from .signature_color import signature_color_for

MEMORY_FIELDS: tuple[str, ...] = ("height_cm", "weight_kg")
HEIGHT_RANGE = (120.0, 230.0)
WEIGHT_RANGE = (30.0, 250.0)


def _clamp(value: Any, bounds: tuple[float, float]) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    low, high = bounds
    if number < low or number > high:
        return None
    return round(number, 1)


def sanitize(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    clean: dict[str, Any] = {}
    problems: list[str] = []
    for key, bounds, label in (
        ("height_cm", HEIGHT_RANGE, "Рост"),
        ("weight_kg", WEIGHT_RANGE, "Вес"),
    ):
        if key not in payload or payload.get(key) in (None, ""):
            continue
        value = _clamp(payload.get(key), bounds)
        if value is None:
            problems.append(f"{label}: допустимо от {int(bounds[0])} до {int(bounds[1])}")
            continue
        clean[key] = value
    return clean, problems


def profile_complete(data: dict[str, Any]) -> bool:
    return bool(data.get("height_cm") and data.get("weight_kg"))


def get_memory(session: Session, user: User) -> UserMemory | None:
    return session.execute(select(UserMemory).where(UserMemory.user_id == user.id)).scalar_one_or_none()


def user_card(user: User) -> dict[str, Any]:
    color = user.signature_color
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "is_demo": user.is_demo,
        "signature_color": color,
        "registered": bool(color),
    }


def register_signature(session: Session, user: User) -> dict[str, Any]:
    if user.signature_color:
        return {"ok": True, "already_registered": True, "user": user_card(user)}
    user.signature_color = signature_color_for(user.id, user.telegram_id)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"ok": True, "already_registered": False, "user": user_card(user)}


def get_profile(session: Session, user: User) -> dict[str, Any]:
    card = user_card(user)
    memory = get_memory(session, user)
    if memory is None:
        return {"saved": False, "profile": {}, "updated_at": None, "used_count": 0, "user": card}
    data = memory.data()
    return {
        "saved": profile_complete(data),
        "profile": {key: data.get(key) for key in MEMORY_FIELDS if key in data},
        "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
        "used_count": int(memory.used_count or 0),
        "user": card,
    }


def save_profile(
    session: Session,
    user: User,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    clean, problems = sanitize(payload)
    if not clean:
        return get_profile(session, user), problems or ["Нечего сохранять: нужны рост и вес"]

    memory = get_memory(session, user)
    if memory is None:
        memory = UserMemory(user_id=user.id, payload="{}")
        session.add(memory)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            memory = get_memory(session, user)
            if memory is None:
                raise
    data = memory.data()
    data.update(clean)
    memory.payload = UserMemory.dumps(data)
    memory.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(memory)
    return get_profile(session, user), problems


def remember_body(session: Session, user: User, height_cm: Any, weight_kg: Any) -> None:
    payload: dict[str, Any] = {}
    if height_cm is not None:
        payload["height_cm"] = height_cm
    if weight_kg is not None:
        payload["weight_kg"] = weight_kg
    if not payload:
        return
    try:
        save_profile(session, user, payload)
    except Exception:
        session.rollback()


def mark_used(session: Session, user: User) -> None:
    memory = get_memory(session, user)
    if memory is None:
        return
    memory.used_count = int(memory.used_count or 0) + 1
    session.commit()


def forget_profile(session: Session, user: User) -> dict[str, Any]:
    memory = get_memory(session, user)
    if memory is not None:
        session.delete(memory)
        session.commit()
    return get_profile(session, user)


__all__ = [
    "HEIGHT_RANGE",
    "MEMORY_FIELDS",
    "WEIGHT_RANGE",
    "forget_profile",
    "get_memory",
    "get_profile",
    "mark_used",
    "profile_complete",
    "register_signature",
    "remember_body",
    "sanitize",
    "save_profile",
    "user_card",
]
