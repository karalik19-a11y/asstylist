"""Провайдеры товаров."""

from __future__ import annotations

from .avito_provider import AvitoSearchProvider, avito_search_url, translate_query_to_ru
from .avito_snapshot_provider import AvitoSnapshotProvider
from .catalog_provider import CatalogSearchProvider
from .mock_real_product_provider import MockRealProductProvider
from .web_search_provider import WebSearchProvider

__all__ = [
    "AvitoSearchProvider",
    "AvitoSnapshotProvider",
    "CatalogSearchProvider",
    "MockRealProductProvider",
    "WebSearchProvider",
    "avito_search_url",
    "translate_query_to_ru",
]
