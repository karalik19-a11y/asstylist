"""WebSearchProvider — порт ``src/search/providers/WebSearchProvider.js``.

Заглушка для реальных источников (Google Shopping / SerpAPI / бренд-сайты /
ресеил-платформы). В оригинале она возвращает пустой список сознательно, чтобы
движок никогда не выдумывал товары; здесь поведение сохранено.
"""

from __future__ import annotations

from ...types import ProductItem
from ..provider import SearchContext, SearchProvider, ValidationOutcome


class WebSearchProvider(SearchProvider):
    name = "web-search"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__("web-search", {"apiKey": api_key})

    def search(self, query: str, context: SearchContext) -> list[ProductItem]:
        # Реализация в проде: Google Custom Search, SerpAPI, API брендов,
        # ресейл-платформы. Пока пусто, чтобы исключить выдуманные товары.
        return []

    def validate_item(self, item: ProductItem) -> ValidationOutcome:
        return ValidationOutcome(valid=False, confidence=0.3, reason="no live web validation")
