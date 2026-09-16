"""QueryExpander — расширяет свободный запрос пользователя в набор поисковых направлений.

Учитывает русскоязычные формулировки, силуэты, ткани, настроение и нишевость.
"""

from __future__ import annotations

from ..types import UserStyleProfile

_GARMENTS: tuple[str, ...] = (
    "top", "shirt", "blouse", "jacket", "coat", "pants", "trousers", "jeans", "skirt", "dress",
    "boots", "shoes", "sneaker", "sneakers", "sweater", "knit", "hoodie", "blazer", "cardigan",
    "пальто", "куртка", "брюки", "джинсы", "юбка", "платье", "рубашка", "футболка", "свитер",
    "худи", "ботинки", "кроссовки", "сумка", "топ", "жилет", "кардиган", "свитшот", "блуза", "шорты",
    "пиджак", "тренч", "плащ", "сарафан", "лонгслив", "водолазка", "ботильоны", "лоферы",
)

_DESCRIPTORS: tuple[str, ...] = (
    "sheer", "transparent", "black", "oversized", "deconstructed", "leather", "wool", "mesh",
    "industrial", "romantic", "gothic", "minimal", "archive", "vintage",
    "прозрачн", "черн", "оверсайз", "деконструирован", "кожан", "шерстян", "индустриальн",
    "романтичн", "готич", "минималист", "архивн", "винтажн", "объёмн", "свободн", "притален",
    "структурн", "мягк", "жёстк", "матовый", "глянцев", "фактурн",
)

_INTENT_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "офис": ("smart casual blazer trousers", "деловой образ пиджак брюки", "office tailored look"),
    "работ": ("workwear field jacket denim", "офисный smart casual", "business casual outfit"),
    "свидан": ("date night elegant outfit", "романтичный вечерний образ", "soft tailored date look"),
    "вечерин": ("party statement outfit", "вечерний акцент образ", "going out elevated look"),
    "лет": ("summer linen light layers", "лёгкий летний образ", "breathable summer outfit"),
    "зим": ("winter wool coat layers", "зимний многослойный образ", "warm tailored winter look"),
    "уличн": ("streetwear oversized layers", "уличный кэжуал", "urban street outfit"),
    "минимал": ("precise minimal tailoring", "чистый минимализм", "quiet luxury minimal"),
    "кожа": ("leather jacket outfit", "кожаная куртка образ", "aged leather layering"),
    "джин": ("straight denim casual", "джинсовый образ", "denim workwear look"),
    "оверсайз": ("oversized volume silhouette", "объёмный оверсайз", "relaxed oversized layers"),
    "прозрач": ("sheer layering top", "прозрачный слой образ", "mesh sheer editorial"),
    "архив": ("archive designer piece", "архивная вещь", "deadstock runway archive"),
    "техно": ("technical shell utility", "техно-утилитарный образ", "gore-tex utility layers"),
    "романти": ("romantic soft draping", "мягкий романтичный образ", "fluid romantic tailoring"),
}


class QueryExpander:
    def expand(self, user_query: str, user_profile: UserStyleProfile | dict | None = None) -> list[str]:
        profile = user_profile or UserStyleProfile()
        if isinstance(profile, dict):
            profile = UserStyleProfile.from_dict(profile)

        base = (user_query or "").strip().lower().replace("ё", "е")
        if not base:
            return ["contemporary wardrobe essentials"]

        niche_boost = getattr(profile, "niche_level", 50) >= 70
        aesthetics = getattr(profile, "aesthetics", None) or []

        ordered: dict[str, None] = {}

        def add(expansion: str) -> None:
            text = expansion.strip()
            if text:
                ordered.setdefault(text, None)

        add(base)

        garments = self._extract(_GARMENTS, base)
        descriptors = self._extract(_DESCRIPTORS, base)
        anchor = garments[0] if garments else "образ"

        if descriptors or garments:
            add(f"{' '.join(descriptors[:3])} designer {anchor}")
            add(f"archive {base}")
            add(f"editorial {base}")
            add(f"contemporary {base}")
            add(f"independent designer {base}")
        else:
            add(f"{base} outfit")
            add(f"{base} lookbook")
            add(f"editorial {base}")

        for key, expansions in _INTENT_EXPANSIONS.items():
            if key in base:
                for exp in expansions:
                    add(exp)

        if niche_boost:
            add(f"archive rare {base}")
            add(f"runway {base}")
            add(f"avant garde {base}")
            add(f"designer deadstock {anchor}")
        else:
            add(f"wearable {base}")
            add(f"everyday {base}")

        for aesthetic in list(aesthetics)[:4]:
            token = str(aesthetic).strip().lower()
            if token:
                add(f"{token} {base}")
                add(f"{token} {anchor}")

        if any(w in base for w in ("sheer", "transparent", "mesh", "прозрач")):
            add("sheer viscose designer top")
            add("прозрачный слой поверх белья editorial")
        if any(w in base for w in ("leather", "кожан", "кожа")):
            add("aged leather jacket")
            add("кожаная куртка винтаж")
        if any(w in base for w in ("oversized", "оверсайз", "объём")):
            add("oversized wool coat")
            add("объёмное пальто оверсайз")

        add(f"{base} купить")
        add(f"{base} авито")

        return list(ordered.keys())[:24]

    @staticmethod
    def _extract(vocabulary: tuple[str, ...], text: str) -> list[str]:
        found: list[str] = []
        for token in vocabulary:
            if token in text and token not in found:
                found.append(token)
        return found
