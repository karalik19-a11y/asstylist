"""Query expansion v2.1: translate editorial intent into searchable marketplace language.

The important rule is *specificity before volume*: a dozen near-identical generic
queries are worse than a handful of distinct silhouettes/material/construction
queries. Avito is primarily Russian, so every expansion carries real RU garment
terms rather than relying on English editorial filler.
"""

from __future__ import annotations

from ..types import UserStyleProfile

_GARMENTS: tuple[str, ...] = (
    "пальто", "куртка", "жакет", "пиджак", "тренч", "бомбер", "рубашка", "свитер",
    "кардиган", "футболка", "топ", "жилет", "брюки", "джинсы", "юбка", "платье",
    "ботинки", "кеды", "кроссовки", "лоферы", "сумка", "ремень", "цепь", "браслет",
    "coat", "jacket", "shirt", "sweater", "cardigan", "pants", "trousers", "jeans",
    "boots", "sneakers", "loafers", "bag", "belt", "chain",
)

# Words which carry visual information on a marketplace listing.
_DESCRIPTORS: tuple[str, ...] = (
    "кож", "замш", "шерст", "вельвет", "бархат", "твид", "сетк", "прозрач",
    "драп", "асимметр", "деконстру", "необработ", "потерт", "выцветш", "варен",
    "оверсайз", "объемн", "удлин", "укороч", "притал", "широк", "прямой",
    "архив", "винтаж", "deadstock", "reworked", "raw", "distressed", "vintage",
    "leather", "suede", "wool", "velvet", "tweed", "mesh", "sheer", "deconstructed",
)

# Style intent -> marketplace language. This is deliberately concrete rather than
# aesthetic-name spam because sellers rarely title an Avito listing "Neo-Gothic".
STYLE_MARKET_TERMS: dict[str, tuple[str, ...]] = {
    "modern_craftsman": ("рабочая куртка", "chore coat", "field jacket", "выцветший деним", "замша", "barn jacket"),
    "leather_weather": ("косуха", "байкерская куртка", "винтажная кожа", "потертая кожа", "замшевая куртка", "мото"),
    "broken_down_prep": ("оксфорд", "регби", "кардиган", "лоферы", "поло", "винтажная рубашка", "ivy"),
    "romantic_menswear": ("драпированная рубашка", "полупрозрачная рубашка", "сетка", "кружево", "удлиненный пиджак", "широкие брюки"),
    "military_romance": ("полевая куртка", "милитари", "френч", "мундир", "бархатный пиджак", "винтажная брошь"),
    "archive_reconstruction": ("архив", "reworked", "деконструкция", "асимметричная куртка", "deadstock", "редкая винтажная вещь"),
    "technical_romantic": ("техническая куртка", "нейлон", "utility", "модульная куртка", "сетка", "асимметричный слой"),
    "americana_90s": ("винтаж 90s", "фланель", "клетчатая рубашка", "прямые джинсы", "регби", "винтажная спортивная куртка"),
    "accessory_first": ("серебряная цепь", "массивная цепь", "кафф", "брелок", "винтажный ремень", "серебряная фурнитура"),
    "pink_accent": ("пыльно-розовый", "выцветший розовый", "розовая рубашка", "розовый трикотаж", "розовый акцент"),
    "sport_couture": ("винтажная футбольная форма", "регби", "трековая куртка", "спортивный трикотаж", "широкие брюки", "ретро кроссовки"),
    "neo_gothic_editorial": ("черная кожа", "длинное пальто", "бархат", "серебряная фурнитура", "удлиненный силуэт", "готика"),
    "post_punk_archive": ("потертая кожа", "рваный деним", "архивная вещь", "панк", "асимметрия", "винтажная фурнитура"),
    "minimal_precision": ("архитектурный крой", "нестандартный крой", "асимметричный пиджак", "плотная шерсть", "удлиненный силуэт", "монохром"),
}


class QueryExpander:
    def expand(self, user_query: str, user_profile: UserStyleProfile | dict | None = None) -> list[str]:
        profile = user_profile or UserStyleProfile()
        if isinstance(profile, dict):
            profile = UserStyleProfile.from_dict(profile)

        base = (user_query or "").strip().lower().replace("ё", "е")
        ordered: dict[str, None] = {}

        def add(value: str) -> None:
            value = " ".join(value.split()).strip()
            if value and len(value) > 3:
                ordered.setdefault(value, None)

        add(base)

        style_terms: list[str] = []
        for aesthetic in profile.aesthetics:
            style_terms.extend(STYLE_MARKET_TERMS.get(aesthetic, ()))

        # Infer a v2 style from explicit seed vocabulary even when the profile's
        # legacy aesthetic list is still "minimal" for backwards compatibility.
        for style_id, terms in STYLE_MARKET_TERMS.items():
            if any(term.lower() in base for term in terms):
                style_terms.extend(terms)
                break

        style_terms = list(dict.fromkeys(style_terms))
        garments = [word for word in _GARMENTS if word in base]
        descriptors = [word for word in _DESCRIPTORS if word in base]
        anchor = garments[0] if garments else "вещь"

        # Primary queries: each one changes a material/silhouette/marketplace noun.
        for term in style_terms[:6]:
            add(f"{term} {anchor}")
        if descriptors:
            for descriptor in descriptors[:4]:
                add(f"{descriptor} {anchor}")

        # Russian-only fallbacks. Do not add generic "fashion/styling" queries:
        # those produce the same mass-market cards again and again.
        if not style_terms:
            add(f"{' '.join(descriptors[:2])} {anchor}".strip())
            add(f"винтаж {anchor}")
            add(f"редкая вещь {anchor}")

        # Niche users get explicit resale/archive language, but only when it can
        # change the marketplace result.
        if profile.niche_level >= 75:
            for term in ("архив", "deadstock", "reworked", "редкая винтажная"):
                add(f"{term} {anchor}")

        # Preserve one exact user query and cap the total number of network calls.
        return list(ordered)[:12]

    @staticmethod
    def _extract(vocabulary: tuple[str, ...], text: str) -> list[str]:
        return [word for word in vocabulary if word in text]
