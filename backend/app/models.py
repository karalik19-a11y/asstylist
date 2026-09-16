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
    category: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str] = mapped_column(String(120))
    price_rub: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="RUB")
    fit: Mapped[str] = mapped_column(String(32), default="regular")
    formality: Mapped[int] = mapped_column(Integer, default=2)
    colors: Mapped[str] = mapped_column(Text, default="[]")
    color_hexes: Mapped[str] = mapped_column(Text, default="[]")
    styles: Mapped[str] = mapped_column(Text, default="[]")
    moods: Mapped[str] = mapped_column(Text, default="[]")
    silhouettes: Mapped[str] = mapped_column(Text, default="[]")
    gendered: Mapped[str] = mapped_column(Text, default="[]")
    seasons: Mapped[str] = mapped_column(Text, default="[]")
    sizes: Mapped[str] = mapped_column(Text, default="[]")
    materials: Mapped[str] = mapped_column(Text, default="[]")
    url: Mapped[str] = mapped_column(String(500), default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    source: Mapped[str] = mapped_column(String(64), default="demo")
    rating: Mapped[float] = mapped_column(Float, default=4.3)
    reviews_count: Mapped[int] = mapped_column(Integer, default=0)

    # verification layer
    verification_status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    verification_score: Mapped[float] = mapped_column(Float, default=0.0)
    verification_issues: Mapped[str] = mapped_column(Text, default="[]")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    def colors_list(self) -> list[str]:
        return self.loads(self.colors, [])

    def color_hexes_list(self) -> list[str]:
        return self.loads(self.color_hexes, [])

    def styles_list(self) -> list[str]:
        return self.loads(self.styles, [])

    def moods_list(self) -> list[str]:
        return self.loads(self.moods, [])

    def silhouettes_list(self) -> list[str]:
        return self.loads(self.silhouettes, [])

    def gendered_list(self) -> list[str]:
        return self.loads(self.gendered, [])

    def seasons_list(self) -> list[str]:
        return self.loads(self.seasons, [])

    def sizes_list(self) -> list[str]:
        return self.loads(self.sizes, [])

    def issues_list(self) -> list[str]:
        return self.loads(self.verification_issues, [])


class Look(_JSONMixin, Base):
    __tablename__ = "looks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    style: Mapped[str] = mapped_column(String(48))
    mood: Mapped[str] = mapped_column(String(48))
    occasion: Mapped[str] = mapped_column(String(48), default="everyday")
    season: Mapped[str] = mapped_column(String(24), default="all")
    presentation: Mapped[str] = mapped_column(String(24), default="unisex")

    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    budget_rub: Mapped[float] = mapped_column(Float)
    total_rub: Mapped[float] = mapped_column(Float, default=0.0)

    body_json: Mapped[str] = mapped_column(Text, default="{}")
    palette_json: Mapped[str] = mapped_column(Text, default="{}")
    ranking_json: Mapped[str] = mapped_column(Text, default="{}")
    tips_json: Mapped[str] = mapped_column(Text, default="[]")
    summary: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    photo_digest: Mapped[str] = mapped_column(String(64), default="")
    photo_path: Mapped[str] = mapped_column(String(300), default="")
    ai_provider: Mapped[str] = mapped_column(String(32), default="local")
    engine_version: Mapped[str] = mapped_column(String(32), default="")

    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)

    user: Mapped[User] = relationship(back_populates="looks")
    items: Mapped[list["LookItem"]] = relationship(
        back_populates="look", cascade="all, delete-orphan", order_by="LookItem.position"
    )


class LookItem(Base):
    __tablename__ = "look_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    look_id: Mapped[int] = mapped_column(ForeignKey("looks.id"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    slot: Mapped[str] = mapped_column(String(32), index=True)
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sku: Mapped[str] = mapped_column(String(64), default="")
    category: Mapped[str] = mapped_column(String(32), default="")
    name: Mapped[str] = mapped_column(String(200), default="")
    brand: Mapped[str] = mapped_column(String(120), default="")
    price_rub: Mapped[float] = mapped_column(Float, default=0.0)
    url: Mapped[str] = mapped_column(String(500), default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    colors: Mapped[str] = mapped_column(Text, default="[]")
    color_hexes: Mapped[str] = mapped_column(Text, default="[]")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    breakdown_json: Mapped[str] = mapped_column(Text, default="{}")
    reasons_json: Mapped[str] = mapped_column(Text, default="[]")
    verification_status: Mapped[str] = mapped_column(String(16), default="verified")
    verification_score: Mapped[float] = mapped_column(Float, default=0.0)
    alternatives_json: Mapped[str] = mapped_column(Text, default="[]")

    look: Mapped[Look] = relationship(back_populates="items")

    def colors_list(self) -> list[str]:
        return _JSONMixin.loads(self.colors, [])

    def color_hexes_list(self) -> list[str]:
        return _JSONMixin.loads(self.color_hexes, [])

    def reasons(self) -> list[str]:
        return _JSONMixin.loads(self.reasons_json, [])

    def breakdown(self) -> dict[str, float]:
        return _JSONMixin.loads(self.breakdown_json, {})

    def alternatives(self) -> list[dict]:
        return _JSONMixin.loads(self.alternatives_json, [])

