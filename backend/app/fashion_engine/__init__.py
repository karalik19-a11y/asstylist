"""ASSTYLIST Fashion Discovery & Outfit Intelligence Engine — Python port.

Порт движка из репозитория https://github.com/karalik19-a11y/- (каталог
``fashion-engine``, MIT). Здесь он живёт внутри backend'а как чистый Python:
ноль сетевых вызовов, ноль внешних зависимостей, детерминированный результат.

Пайплайн (как в оригинале):

    USER INTENT → AESTHETIC DNA → FASHION RESEARCH → ITEM DISCOVERY
    → ITEM VALIDATION → OUTFIT ARCHITECTURE → COMPATIBILITY SCORING → FINAL LOOK

Пример::

    from app.fashion_engine import create_outfit

    result = create_outfit(
        "industrial romantic look with sheer top",
        {"nicheLevel": 80, "aesthetics": ["industrial", "dark"]},
        providers=[CatalogSearchProvider(cards)],
    )
    print(result.styling_thesis, result.outfit_score)

Отличия от JS-версии (все задокументированы в ``README.md`` пакета):
промисы заменены на синхронные вызовы (все провайдеры локальные), ``uid()``
на ``Math.random`` заменён на детерминированный ``stable_id``, таблицы
ключевых слов расширены русскими основами, исправлен вызов
``_is_mass_market`` в ``TasteEngine``.
"""

from __future__ import annotations

from .engine import ENGINE_VERSION, EngineOptions, FashionEngine, create_outfit
from .search.provider import SearchContext, SearchProvider
from .search.providers.avito_provider import AvitoSearchProvider, avito_search_url
from .search.providers.avito_snapshot_provider import AvitoSnapshotProvider
from .search.providers.catalog_provider import CatalogSearchProvider
from .search.providers.mock_real_product_provider import MockRealProductProvider
from .search.providers.web_search_provider import WebSearchProvider
from .types import (
    DEFAULT_USER_PROFILE,
    TASTE_CATEGORIES,
    FashionAttributes,
    OutfitResult,
    ProductItem,
    StyleReference,
    UserStyleProfile,
)
from .tool_schema import TOOL_SCHEMA

__all__ = [
    "AvitoSearchProvider",
    "AvitoSnapshotProvider",
    "CatalogSearchProvider",
    "DEFAULT_USER_PROFILE",
    "ENGINE_VERSION",
    "EngineOptions",
    "FashionAttributes",
    "FashionEngine",
    "MockRealProductProvider",
    "OutfitResult",
    "ProductItem",
    "SearchContext",
    "SearchProvider",
    "StyleReference",
    "TASTE_CATEGORIES",
    "TOOL_SCHEMA",
    "UserStyleProfile",
    "WebSearchProvider",
    "avito_search_url",
    "create_outfit",
]
