"""RankingEngine — порт ``src/ranking/RankingEngine.js``.

Финальный порядок образов и позиций внутри образа.
"""

from __future__ import annotations

from .types import OutfitCandidate, ProductItem


class RankingEngine:
    def rank_outfits(self, outfits: list[OutfitCandidate]) -> list[OutfitCandidate]:
        def final_score(outfit: OutfitCandidate) -> float:
            # Отличие порта: образ, собранный вокруг тезиса из формулировки
            # пользователя, получает небольшой приоритет. Иначе на большом
            # каталоге побеждал бы образ, лучше подходящий вещам, но не запросу.
            return (
                float(outfit.outfit_score or 0) * 0.7
                + float(outfit.critic_score_adjustment or 0)
                + outfit.item_count() * 2
                + (6.0 if outfit.thesis_from_query else 0.0)
            )

        ranked = list(outfits)
        for outfit in ranked:
            outfit.styling_logic.setdefault("finalRankScore", round(final_score(outfit), 3))
        # Тай-брейк — порядок построения: тезисы из запроса пользователя идут
        # первыми, поэтому при равной оценке выигрывает более точный по запросу.
        ranked.sort(key=lambda outfit: -final_score(outfit))
        return ranked

    def rank_items(self, items: list[ProductItem]) -> list[ProductItem]:
        def key(item: ProductItem) -> float:
            interesting = float(getattr(item.fashion_attributes, "interesting_trend_score", 0) or 0)
            return float(item.fashion_score or 0) * 0.5 + float(item.confidence or 0) * 30 + interesting * 20

        ranked = list(items)
        ranked.sort(key=lambda item: (-key(item), item.id))
        return ranked
