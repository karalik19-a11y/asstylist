"""CatalogSearchProvider — провайдер поверх проверенного каталога asStylist.

Это ключевая адаптация: движок из репозитория ищет «настоящие» вещи через
``SearchProvider``; здесь этот интерфейс реализован над каталогом приложения
(SQLite, только позиции, прошедшие слой верификации). Поэтому весь пайплайн
движка — расширение запроса, Fashion Intelligence, Taste, anti-generic,
архитектор образа — работает на реальных товарах с ценами в ₽.

Особенности:
* поиск идёт и по английским терминам движка, и по русским основам каталога;
* ``backfill`` добирает лучшие по confidence позиции, если расширенные
  запросы дали меньше ``limit`` совпадений — иначе архитектору не хватило бы
  материала на целый образ;
* тир бренда (``meta["tier"]``) усиливает нишевые позиции при
  ``nicheLevel >= 75``, как дефолтный mock-провайдер усиливал archive/cult.
"""

from __future__ import annotations

import zlib

from ... import lexicon
from ...types import ProductItem
from ..provider import SearchContext, SearchProvider, ValidationOutcome

#: Тиры брендов, которые «интересны» движку при высокой нише.
_PREMIUM_TIERS = ("designer", "niche", "archive", "cult", "independent")


class CatalogSearchProvider(SearchProvider):
    name = "app-catalog"

    def __init__(
        self,
        cards: list[ProductItem],
        *,
        name: str | None = None,
        min_score: float = 8.0,
        backfill: bool = True,
        options: dict | None = None,
    ) -> None:
        super().__init__(name or self.name, options)
        self._cards = list(cards)
        self.min_score = float(min_score)
        self.backfill = bool(backfill)
        self._index: dict[str, tuple[list[str], str]] = {}
        for card in self._cards:
            text = card.searchable_text()
            self._index[card.id] = (lexicon.tokenize(text), text)
        # Порядок добора: категории по кругу, внутри — по уверенности. Так
        # backfill отдаёт целый «гардероб» (верх/низ/обувь/сумка/аксессуар),
        # а не шесть аксессуаров с лучшим confidence.
        self._order = self._backfill_order()

    def _backfill_order(self) -> list[str]:
        buckets: dict[str, list[str]] = {}
        for card in sorted(self._cards, key=lambda entry: (-(entry.confidence or 0), entry.id)):
            buckets.setdefault(card.category or "accessory", []).append(card.id)
        ordered: list[str] = []
        while any(buckets.values()):
            for category in sorted(buckets):
                if buckets[category]:
                    ordered.append(buckets[category].pop(0))
        return ordered

    def search(self, query: str, context: SearchContext) -> list[ProductItem]:
        normalized = (query or "").lower().replace("ё", "е")
        tokens = [token for token in lexicon.tokenize(normalized) if len(token) >= 3]
        limit = max(1, int(context.limit or 8))
        niche = context.niche_level
        categories = set(context.categories or [])

        scored: list[tuple[float, ProductItem]] = []
        for card in self._cards:
            if categories and card.category not in categories:
                continue
            score = self._score_card(card, normalized, tokens, niche)
            if score > 0:
                scored.append((score, card))

        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        for score, card in scored:
            # Релевантность запросу: движок использует её при выборе ключевой
            # вещи (см. OutfitArchitect._relevance).
            card.meta["query_match"] = max(float(card.meta.get("query_match") or 0.0), float(score))
        results = [card for score, card in scored if score > self.min_score][:limit]

        if self.backfill and len(results) < limit:
            chosen = {card.id for card in results}
            # Добор идёт по кругу со сдвигом, зависящим от запроса: иначе все
            # расширенные запросы возвращали бы один и тот же «хвост» каталога
            # и пул движка схлопывался бы до десятка позиций.
            start = self._rotation(query) if self._order else 0
            for offset in range(len(self._order)):
                if len(results) >= limit:
                    break
                card_id = self._order[(start + offset) % len(self._order)]
                if card_id in chosen:
                    continue
                if categories and self._card(card_id).category not in categories:
                    continue
                results.append(self._card(card_id))
                chosen.add(card_id)
        return results

    def validate_item(self, item: ProductItem) -> ValidationOutcome:
        return ValidationOutcome(valid=True, confidence=float(item.confidence or 0.7))

    # ─── внутреннее ───────────────────────────────────────────────────
    def _score_card(self, card: ProductItem, query: str, tokens: list[str], niche: int) -> float:
        card_tokens, text = self._index[card.id]
        token_set = set(card_tokens)
        score = 0.0

        for token in tokens:
            if token in token_set:
                score += 12
            elif any(lexicon.matches_token(token, other) for other in card_tokens):
                score += 9
            elif token in text:
                score += 6

        for tag in card.tags:
            tag_text = str(tag).lower()
            if len(tag_text) > 2 and tag_text in query:
                score += 18

        tier = str((card.meta or {}).get("tier") or "contemporary")
        if niche >= 75 and tier in _PREMIUM_TIERS:
            score += 15
        if niche < 45 and tier == "mass":
            score += 8

        category = (card.category or "").lower()
        if category and category in query:
            score += 10
        return score

    @staticmethod
    def _rotation(query: str) -> int:
        """Стабильный сдвиг для добора (никакой случайности)."""
        return zlib.crc32(query.encode("utf-8"))

    def _card(self, card_id: str) -> ProductItem:
        for card in self._cards:
            if card.id == card_id:
                return card
        raise KeyError(card_id)
