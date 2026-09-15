"""TrendEngine — порт ``src/intelligence/TrendEngine.js``.

Отличает «популярное» от «модно-интересного» и предлагает тезисы образа.
"""

from __future__ import annotations

from .. import keywords as kw
from .. import lexicon
from ..types import ProductItem

#: Слова, по которым тезис узнаётся в тексте (RU + EN).
#:
#: Первыми идут тезисы, которыми пользуются стили asStylist (тихая роскошь,
#: минимализм, техно, романтика, бохо, спорт, деловой крой): каталог приложения
#: русскоязычный, поэтому «кашемир» или «кружево» должны давать свой тезис, а не
#: подбираться по названиям вещей из общего пула. Ниже — тезисы оригинала.
_THESIS_TRIGGERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Quiet Luxury Tailoring", ("cashmere", "кашемир", "wool", "шерст", "quiet luxury", "тих", "tailoring", "прямые силуэт")),
    ("Minimal Precision", ("minimal", "минимал", "clean lines", "лаконич", "monochrome", "монохром")),
    ("Technical Utility", ("techwear", "техно", "nylon", "нейлон", "membrane", "мембран", "utility", "утилитар")),
    ("Soft Romanticism", ("romantic", "романт", "lace", "кружев", "chiffon", "шифон", "floral", "цветоч")),
    ("Craft Bohemia", ("boho", "бохо", "crochet", "fringe", "бахром", "этно", "лён", "льнян")),
    ("Sport Couture", ("athleisure", "спортивн", "jersey", "джерси", "leggings", "леггинс")),
    ("Sharp Tailoring", ("business", "делов", "suit", "костюм", "blazer", "пиджак", "office", "офис")),
    ("Industrial Romanticism", ("sheer", "прозрач", "сетк", "industrial", "индустриальн")),
    ("Transparent Layering", ("sheer", "прозрач", "сетк", "mesh")),
    ("Deconstructed 90s Minimalism", ("deconstructed", "деконстру", "асимметр", "raw", "90s")),
    ("Post-Structural Tailoring", ("asymmetric", "асимметр", "tailored", "крой")),
    ("Neo-Gothic Editorial", ("black", "черн", "leather", "кож", "velvet", "бархат", "gothic", "готич")),
    ("Post-Punk Archive", ("black", "черн", "punk", "панк", "archive", "архив")),
    ("Archive Revival", ("archive", "архив", "vintage", "винтаж")),
    ("Exaggerated Volume", ("oversized", "оверсайз", "volume", "объемн")),
)


class TrendEngine:
    def __init__(self) -> None:
        self.emerging_aesthetics = list(kw.EMERGING_AESTHETICS)
        self.rising_silhouettes = list(kw.RISING_SILHOUETTES)
        self.recurring_materials = list(kw.RECURRING_MATERIALS)

    def enrich(self, item: ProductItem) -> ProductItem:
        """Дополняет вещь оценками трендовой релевантности."""
        attributes = item.fashion_attributes
        if attributes is None:
            return item
        text = f"{item.name or ''} {item.brand or ''} {attributes.aesthetic or ''}".lower().replace("ё", "е")

        trend_relevance = 0.4
        interesting = 0.3
        popular = 0.3

        for name, strength, kind in self.emerging_aesthetics:
            first_word = name.split(" ")[0]
            cultural = list(getattr(attributes, "cultural_reference", []) or [])
            if first_word in text or any(name in f"{reference} {name}" for reference in cultural):
                if kind == "interesting":
                    interesting = max(interesting, strength)
                else:
                    popular = max(popular, strength)

        for silhouette in self.rising_silhouettes:
            if silhouette.split(" ")[0] in text:
                trend_relevance += 0.15
                interesting += 0.1

        for material in self.recurring_materials:
            if material.split(" ")[0] in text:
                trend_relevance += 0.1

        if getattr(attributes, "historical_reference", None) or item.source_type == "archive":
            interesting += 0.2

        attributes.trend_relevance = min(1.0, round(trend_relevance, 3))
        attributes.interesting_trend_score = min(1.0, round(interesting, 3))
        attributes.popular_trend_score = min(1.0, round(popular, 3))
        attributes.current_relevance = min(1.0, round(interesting * 0.7 + popular * 0.3, 3))
        return item

    def suggest_theses(self, items: list[ProductItem], user_query: str) -> list[str]:
        """Кандидаты в стилистические тезисы (порт + русские триггеры).

        Отличие порта: сначала идут тезисы, которые узнаются в самом запросе
        пользователя, и только потом — тезисы, найденные по вещам пула. У
        провайдера поверх всего каталога (``CatalogSearchProvider``) пул содержит
        почти весь ассортимент, поэтому без этого шага тезис выбирался бы по
        случайной вещи каталога, а не по запросу.
        """
        query_theses = set(self.theses_from_query(user_query))
        pool_text = " ".join(f"{item.name} {item.brand} {' '.join(item.tags)}" for item in items)
        pool_text = f"{pool_text} {(user_query or '')}".lower().replace("ё", "е")

        from_query: list[str] = []
        from_pool: list[str] = []
        for thesis, triggers in _THESIS_TRIGGERS:
            if thesis in query_theses:
                from_query.append(thesis)
            elif any(trigger in pool_text for trigger in triggers):
                from_pool.append(thesis)

        theses = from_query + from_pool
        if not theses:
            theses = ["Contemporary Editorial", "Refined Utilitarian"]
        return list(dict.fromkeys(theses))

    def theses_from_query(self, user_query: str) -> list[str]:
        """Тезисы, которые узнаются в самом запросе пользователя (RU + EN)."""
        query_text = (user_query or "").lower().replace("ё", "е")
        tokens = lexicon.tokenize(query_text)
        found: list[str] = []
        for thesis, triggers in _THESIS_TRIGGERS:
            if any(kw.keyword_hit(query_text, tokens, trigger) for trigger in triggers):
                found.append(thesis)
        return found
