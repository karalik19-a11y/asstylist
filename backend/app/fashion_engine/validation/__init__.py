"""Слой валидации: реальность товара, консистентность, дедупликация."""

from __future__ import annotations

from .identity_resolver import ProductIdentityResolver
from .image_matcher import ImageMatcher
from .item_validator import ItemValidation, ItemValidator

__all__ = ["ImageMatcher", "ItemValidation", "ItemValidator", "ProductIdentityResolver"]
