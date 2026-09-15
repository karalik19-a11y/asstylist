"""Fashion Intelligence: анализ вещи, вкус, тренды."""

from __future__ import annotations

from .fashion_intelligence import FashionIntelligence
from .taste_engine import TasteEngine, TasteResult
from .trend_engine import TrendEngine

__all__ = ["FashionIntelligence", "TasteEngine", "TasteResult", "TrendEngine"]
