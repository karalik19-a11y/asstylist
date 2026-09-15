"""Архитектура образа: сборка, оценка, критик."""

from __future__ import annotations

from .architect import OutfitArchitect
from .critic import CriticVerdict, FashionCritic
from .scorer import OutfitScorer, OutfitScore

__all__ = ["CriticVerdict", "FashionCritic", "OutfitArchitect", "OutfitScore", "OutfitScorer"]
