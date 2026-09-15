"""Интерфейс провайдера товаров (порт ``src/search/SearchProvider.js``).

Оригинал был асинхронным (``Promise``); в Python-порте методы синхронные —
все провайдеры локальные и ответ дают мгновенно, сеть не используется.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..types import ProductItem, UserStyleProfile


@dataclass
class SearchContext:
    """Контекст запроса: профиль, ниша, лимит, категории."""

    user_profile: UserStyleProfile = field(default_factory=UserStyleProfile)
    limit: int = 8
    categories: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def niche_level(self) -> int:
        return self.user_profile.niche_level


@dataclass
class ValidationOutcome:
    valid: bool
    confidence: float
    reason: str | None = None


class SearchProvider:
    """Базовый провайдер. Наследники должны реализовать ``search``."""

    #: Человекочитаемое имя, попадает в ``ProductItem.provider``.
    name: str = "provider"

    def __init__(self, name: str | None = None, options: dict[str, Any] | None = None) -> None:
        if name:
            self.name = name
        self.options = options or {}

    def search(self, query: str, context: SearchContext) -> list[ProductItem]:
        raise NotImplementedError(f"search() not implemented in {self.name}")

    def validate_item(self, item: ProductItem) -> ValidationOutcome:
        return ValidationOutcome(valid=True, confidence=0.5)

    @property
    def source_type(self) -> str:
        return self.name
