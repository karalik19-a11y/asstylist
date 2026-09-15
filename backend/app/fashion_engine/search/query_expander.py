"""QueryExpander — порт ``src/search/QueryExpander.js``.

Превращает запрос пользователя в набор поисковых направлений: designer,
archive, runway, independent, avant-garde и точечные расширения под
конкретную эстетику («sheer», «industrial», «raw»).
"""

from __future__ import annotations

from ..types import UserStyleProfile

_GARMENTS: tuple[str, ...] = (
    "top", "shirt", "blouse", "jacket", "coat", "pants", "trousers", "jeans", "skirt", "dress",
    "boots", "shoes", "sneaker", "sneakers", "sweater", "knit", "hoodie", "blazer", "cardigan",
    # RU-названия: каталог asStylist русскоязычный
    "пальто", "куртка", "брюки", "джинсы", "юбка", "платье", "рубашка", "футболка", "свитер",
    "худи", "ботинки", "кроссовки", "сумка", "топ", "жилет", "кардиган", "свитшот", "блуза", "шорты",
)

_DESCRIPTORS: tuple[str, ...] = (
    "sheer", "transparent", "black", "oversized", "deconstructed", "leather", "wool", "mesh",
    "industrial", "romantic", "gothic", "minimal", "archive", "vintage",
    # RU-дескрипторы
    "прозрачн", "черн", "оверсайз", "деконструирован", "кожан", "шерстян", "индустриальн",
    "романтичн", "готич", "минималист", "архивн", "винтажн",
)


class QueryExpander:
    def expand(self, user_query: str, user_profile: UserStyleProfile | dict | None = None) -> list[str]:
        profile = user_profile or UserStyleProfile()
        if isinstance(profile, dict):
            profile = UserStyleProfile.from_dict(profile)

        base = (user_query or "").strip().lower().replace("ё", "е")
        niche_boost = profile.niche_level >= 70
        aesthetics = profile.aesthetics

        ordered: dict[str, None] = {}

        def add(expansion: str) -> None:
            text = expansion.strip()
            if text:
                ordered.setdefault(text, None)

        add(base)

        garments = self._extract(_GARMENTS, base)
        descriptors = self._extract(_DESCRIPTORS, base)
        anchor = garments[0] if garments else "piece"

        if descriptors or garments:
            add(f"{' '.join(descriptors)} designer {anchor}")
            add(f"archive {base}")
            add(f"runway {base}")
            add(f"editorial {base}")
            add(f"independent designer {base}")
            add(f"avant garde {base}")
            add(f"contemporary {base}")

        if any(word in base for word in ("sheer", "transparent", "mesh", "прозрач")):
            for expansion in (
                "sheer viscose designer top",
                "archive sheer long sleeve",
                "deconstructed transparent top",
                "avant garde sheer menswear",
                "runway transparent layering",
                "archive fashion mesh top",
                "dark romantic sheer layering",
                "experimental sheer shirt",
            ):
                add(expansion)

        if any(word in base for word in ("industrial", "индустриальн")):
            for expansion in (
                "industrial fashion editorial",
                "utilitarian designer workwear",
                "deconstructed workwear jacket",
                "archive industrial fashion",
            ):
                add(expansion)

        if any(word in base for word in ("dirty", "грязн", "raw")):
            for expansion in (
                "raw edge deconstructed fashion",
                "distressed archive piece",
                "unfinished hem designer",
            ):
                add(expansion)

        if niche_boost:
            for template in (
                "emerging designer {}",
                "niche brand {}",
                "rare {}",
                "cult {}",
                "underground fashion {}",
            ):
                add(template.format(base))

        for aesthetic in aesthetics:
            add(f"{aesthetic} {anchor}")

        add(f"{base} fashion")
        add(f"{base} styling")

        return [query for query in ordered if len(query) > 3][:14]

    @staticmethod
    def _extract(vocabulary: tuple[str, ...], text: str) -> list[str]:
        return [word for word in vocabulary if word in text]
