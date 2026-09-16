"""ORM models."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class _JSONMixin:
    @staticmethod
    def loads(value: str | None, default):
        if not value:
            return default
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default

    @staticmethod
    def dumps(value) -> str:
        return json.dumps(value, ensure_ascii=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    signature_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    looks: Mapped[list["Look"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserMemory(_JSONMixin, Base):
    """Память о пользователе: рост, вес и настройки подбора.

    Человек вводит данные один раз; в следующий раз сервис предлагает выбор —
    собрать образ по сохранённым параметрам, поправить только рост и вес или
    пройти настройку заново (``POST /api/profile/reset``).
    """

    __tablename__ = "user_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    def data(self) -> dict:
        return self.loads(self.payload, {})
