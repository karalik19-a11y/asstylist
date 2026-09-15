"""Провайдеры товаров."""

from __future__ import annotations

from .catalog_provider import CatalogSearchProvider
from .mock_real_product_provider import MockRealProductProvider
from .web_search_provider import WebSearchProvider

__all__ = ["CatalogSearchProvider", "MockRealProductProvider", "WebSearchProvider"]
