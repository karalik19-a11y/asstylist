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


class Product(_JSONMixin, Base):
    """A verified fashion product offered by a source (marketplace/brand/demo)."""

    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("sku", "source", name="uq_product_sku_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(64), default="catalog")
    name: Mapped[str] = mapped_column(String(256))
    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    price_rub: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="RUB")
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    colors: Mapped[str] = mapped_column(Text, default="[]")
    styles: Mapped[str] = mapped_column(Text, default="[]")
    moods: Mapped[str] = mapped_column(Text, default="[]")
    seasons: Mapped[str] = mapped_column(Text, default="[]")
    formality: Mapped[int] = mapped_column(Integer, default=1)
    fit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    reviews: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="pending")
    verification_score: Mapped[float] = mapped_column(Float, default=0.0)
    verification_payload: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    def colors_list(self) -> list:
        return self.loads(self.colors, [])

    def styles_list(self) -> list:
        return self.loads(self.styles, [])

    def moods_list(self) -> list:
        return self.loads(self.moods, [])

    def seasons_list(self) -> list:
        return self.loads(self.seasons, [])


class Look(_JSONMixin, Base):
    __tablename__ = "looks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    style: Mapped[str] = mapped_column(String(64))
    mood: Mapped[str] = mapped_column(String(64))
    occasion: Mapped[str] = mapped_column(String(64), default="everyday")
    season: Mapped[str] = mapped_column(String(32), default="all")
    presentation: Mapped[str] = mapped_column(String(32), default="unisex")
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    budget_rub: Mapped[float] = mapped_column(Float)
    total_rub: Mapped[float] = mapped_column(Float, default=0)
    score: Mapped[float] = mapped_column(Float, default=0)
    plan: Mapped[str] = mapped_column(String(32), default="layered")
    summary: Mapped[str] = mapped_column(Text, default="")
    personal_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    tips: Mapped[str] = mapped_column(Text, default="[]")
    body_payload: Mapped[str] = mapped_column(Text, default="{}")
    palette_payload: Mapped[str] = mapped_column(Text, default="{}")
    verdict_payload: Mapped[str] = mapped_column(Text, default="{}")
    diagnostics_payload: Mapped[str] = mapped_column(Text, default="{}")
    engine_payload: Mapped[str] = mapped_column(Text, default="{}")
    engine_version: Mapped[str] = mapped_column(String(32), default="1")
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="looks")
    items: Mapped[list["LookItem"]] = relationship(back_populates="look", cascade="all, delete-orphan")

    def tips_list(self) -> list:
        return self.loads(self.tips, [])


class LookItem(_JSONMixin, Base):
    __tablename__ = "look_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    look_id: Mapped[int] = mapped_column(ForeignKey("looks.id"), index=True)
    slot: Mapped[str] = mapped_column(String(32))
    sku: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(256))
    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    price_rub: Mapped[float] = mapped_column(Float)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    color: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    breakdown: Mapped[str] = mapped_column(Text, default="{}")
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    look: Mapped["Look"] = relationship(back_populates="items")
