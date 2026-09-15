"""OutfitArchitect — порт ``src/outfit/OutfitArchitect.js``.

Собирает цельные образы вокруг стилистического тезиса: ключевая вещь,
база, слой, обувь, аксессуар. Если бюджет «взрывается» (больше 1.4× лимита) —
первым уходит аксессуар, как в оригинале.
"""

from __future__ import annotations

from dataclasses import replace

from ..intelligence import TrendEngine
from ..types import OutfitCandidate, ProductItem, UserStyleProfile

#: Триггеры тезисов (EN из оригинала + RU для каталога asStylist).
_THESIS_RULES: tuple[tuple[tuple[str, ...], tuple[tuple[str, ...], float], ...], ...] = (
    (
        ("industrial", "utilitarian", "индустриальн", "утилитарн"),
        (("leather", "cargo", "military", "workwear", "кож"), 30.0),
        (("black", "industrial", "черн"), 15.0),
    ),
    (
        ("romantic", "sheer", "transparent", "романтичн", "прозрачн"),
        (("sheer", "mesh", "organza", "transparent", "прозрач", "сетк", "шифон"), 35.0),
        (("romantic", "drape", "романтичн", "драпиров"), 10.0),
    ),
    (
        ("deconstructed", "90s", "minimal", "деконстру", "минимал"),
        (("deconstructed", "asymmetric", "margiela", "archive", "асимметр", "деконстру"), 30.0),
    ),
    (
        ("gothic", "punk", "dark", "готич", "панк", "темн"),
        (("black", "leather", "velvet", "combat", "черн", "кож", "бархат"), 25.0),
    ),
    (
        ("archive", "revival", "архив"),
        (("archive", "90s", "vintage", "архив", "винтаж"), 30.0),
    ),
    (
        ("volume", "oversized", "объем", "оверсайз"),
        (("oversized", "volume", "оверсайз", "объемн"), 25.0),
    ),
)


class OutfitArchitect:
    def __init__(self) -> None:
        self.trend = TrendEngine()

    def build(
        self,
        products: list[ProductItem],
        user_query: str,
        user_profile: UserStyleProfile | dict | None = None,
        options: dict | None = None,
    ) -> list[OutfitCandidate]:
        options = options or {}
        profile = user_profile or UserStyleProfile()
        if isinstance(profile, dict):
            profile = UserStyleProfile.from_dict(profile)
        max_outfits = int(options.get("max_outfits", 3))

        theses = self.trend.suggest_theses(products, user_query)
        outfits: list[OutfitCandidate] = []
        for thesis in theses[: max_outfits + 1]:
            candidate = self._build_around_thesis(products, thesis, profile, user_query)
            if candidate and candidate.item_count() >= 3:
                outfits.append(candidate)

        if not outfits and len(products) >= 3:
            fallback = self._build_around_thesis(products, "Contemporary Editorial", profile, user_query)
            if fallback:
                outfits.append(fallback)
        return outfits

    # ─── сборка одного образа ─────────────────────────────────────────
    def _build_around_thesis(
        self,
        products: list[ProductItem],
        thesis: str,
        profile: UserStyleProfile,
        user_query: str,
    ) -> OutfitCandidate | None:
        thesis_lower = thesis.lower()
        scored = [(self._relevance(item, thesis_lower, thesis), item) for item in products]
        scored.sort(key=lambda pair: (-pair[0], pair[1].id))

        used: set[str] = set()
        selected: list[ProductItem] = []

        def take(predicate, role: str) -> None:
            for _relevance, item in scored:
                if item.id in used:
                    continue
                if predicate((item.category or "").lower()):
                    selected.append(replace(item, role=role))
                    used.add(item.id)
                    return

        take(lambda category: any(word in category for word in ("jacket", "coat", "blazer", "top", "shirt")), "hero")
        take(lambda category: any(word in category for word in ("trouser", "jean", "pant", "skirt", "short")), "base")
        if len(selected) < 3:
            take(lambda category: any(word in category for word in ("top", "shirt", "cardigan", "knit", "sweater")), "layer")
        take(lambda category: any(word in category for word in ("boot", "sneaker", "shoe")), "footwear")

        # Аксессуар берём только если он сам по себе сильный (как в оригинале)
        for _relevance, item in scored:
            if item.id in used or len(selected) >= 5:
                continue
            category = (item.category or "").lower()
            if any(word in category for word in ("belt", "scarf", "bag", "cap", "accessor")) and item.fashion_score > 70:
                selected.append(replace(item, role="accessory"))
                used.add(item.id)
                break

        if len(selected) < 3:
            return None

        budget = profile.budget_max
        if budget:
            total = sum(item.price or 0 for item in selected)
            if total > budget * 1.4:
                for index, item in enumerate(selected):
                    if item.role == "accessory":
                        selected.pop(index)
                        break

        return OutfitCandidate(
            styling_thesis=thesis,
            aesthetic=self._derive_aesthetic(thesis, selected),
            items=selected,
            roles=[item.role or "" for item in selected],
        )

    @staticmethod
    def _relevance(item: ProductItem, thesis_lower: str, thesis: str) -> float:
        text = f"{item.name} {item.brand} {' '.join(item.tags or [])}".lower().replace("ё", "е")
        attributes = item.fashion_attributes
        relevance = 0.0
        for rule in _THESIS_RULES:
            triggers, boosts = rule[0], rule[1:]
            if not any(trigger in thesis_lower for trigger in triggers):
                continue
            for words, weight in boosts:
                if any(word in text for word in words):
                    relevance += weight
        if any(word in text for word in (thesis_lower.split(" ")[0],)):
            relevance += 5
        if attributes is not None and attributes.material in thesis_lower:
            relevance += 10
        # Релевантность запросу, которую вернул провайдер (в оригинале её роль
        # играл внешний поиск). Для провайдеров без этой метрики — 0.
        relevance += min(30.0, float((item.meta or {}).get("query_match") or 0.0) * 0.5)
        relevance += float(item.fashion_score or 50) * 0.25
        return relevance

    @staticmethod
    def _derive_aesthetic(thesis: str, items: list[ProductItem]) -> str:
        colors = [item.fashion_attributes.color for item in items if item.fashion_attributes]
        dominant = colors[0] if colors else "black"
        return f"{thesis} — {dominant} dominant palette"


__all__ = ["OutfitArchitect"]
