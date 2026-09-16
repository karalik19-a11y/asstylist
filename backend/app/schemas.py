"""API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .config import BUDGET_CEILING_RUB
from .engine.colors import COLORS


def _clean_color_list(value: list[str] | None) -> list[str]:
    if not value:
        return []
    return [v.strip().lower() for v in value if isinstance(v, str) and v.strip().lower() in COLORS]


class AuthRequest(BaseModel):
    init_data: str | None = None
    demo_user_id: str | None = None
    first_name: str | None = None
    username: str | None = None


class UserOut(BaseModel):
    id: int
    telegram_id: str
    username: str | None = None
    first_name: str | None = None
    is_demo: bool = False
    signature_color: str | None = None
    registered: bool = False


class AuthResponse(BaseModel):
    user: UserOut
    demo: bool
    mode: str
    web_app_url: str | None = None


class LookRequest(BaseModel):
    style: str = "minimal"
    mood: str = "calm"
    occasion: str = "everyday"
    season: str = "all"
    presentation: str = "unisex"
    height_cm: float = 172
    weight_kg: float = 68
    budget_rub: float = 50_000
    preferred_colors: list[str] = Field(default_factory=list)
    avoid_colors: list[str] = Field(default_factory=list)
    size: str | None = None
    plan: str | None = None
    query: str | None = None
    niche_level: int | None = None
    telegram_id: str | None = None
    init_data: str | None = None
    demo_user_id: str | None = None
    save: bool = True

    @field_validator("preferred_colors", "avoid_colors", mode="before")
    @classmethod
    def _colors(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            value = [part.strip() for part in value.split(",") if part.strip()]
        return _clean_color_list(value if isinstance(value, list) else None)

    @field_validator("budget_rub")
    @classmethod
    def _budget(cls, value: float) -> float:
        return min(float(value), float(BUDGET_CEILING_RUB))


class ProductImportRequest(BaseModel):
    products: list[dict[str, Any]]
