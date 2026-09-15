"""FashionIntelligence — порт ``src/intelligence/FashionIntelligence.js``.

Разбирает вещь глубже названия и категории: силуэт, материал, фактуру,
визуальный вес, культурную отсылку. Результат — ``FashionAttributes``,
которые используют TasteEngine и OutfitArchitect.
"""

from __future__ import annotations

from .. import keywords as kw
from .. import lexicon
from ..helpers import clamp, int_clamp
from ..types import FashionAttributes, ProductItem


class FashionIntelligence:
    """Вся эвристика детерминированная: один и тот же товар → одни атрибуты."""

    def analyze(self, raw: ProductItem) -> FashionAttributes:
        text = f"{raw.name or ''} {raw.description or ''} {raw.brand or ''}".lower().replace("ё", "е")
        tokens = lexicon.tokenize(text)

        materials = self._detect_materials(text, tokens)
        silhouette = self._detect_silhouette(text, tokens)
        aesthetics = self._detect_aesthetics(text, tokens)
        color = self._extract_color(text, raw)
        category = (raw.category or "").lower()

        return FashionAttributes(
            silhouette=silhouette,
            proportions=self._infer_proportions(silhouette, category),
            fit=self._infer_fit(text, silhouette),
            construction=self._infer_construction(text),
            material=materials["primary"] or "unknown",
            materials=list(materials["all"]),
            texture=materials["texture"],
            color=color,
            color_temperature=self._color_temp(color),
            finish=self._infer_finish(text),
            visual_weight=self._estimate_visual_weight(silhouette, materials["all"], category),
            volume="high" if ({"oversized", "voluminous"} & set(silhouette)) else "medium",
            length=self._infer_length(text, category),
            layering_potential=self._estimate_layering(category, materials["all"], silhouette),
            historical_reference=self._detect_historical(text),
            designer_language=self._infer_designer_language(raw.brand, text),
            cultural_reference=aesthetics,
            subculture=self._detect_subculture(text),
            aesthetic=aesthetics[0] if aesthetics else "contemporary",
            season=self._infer_season(text, materials["all"]),
            styling_potential=self._score_styling_potential(silhouette, materials["all"], aesthetics),
            rarity=self._estimate_rarity(raw, text),
            fashion_relevance=0.7,
            current_relevance=0.6,
            editorial_relevance=0.85 if {"editorial", "avantgarde"} & set(aesthetics) else 0.4,
        )

    # ─── определение признаков ────────────────────────────────────────
    def _detect_silhouette(self, text: str, tokens: list[str]) -> list[str]:
        found = [
            key
            for key, words in kw.SILHOUETTE_KEYWORDS.items()
            if kw.any_keyword(text, tokens, words)
        ]
        return found or ["regular"]

    def _detect_materials(self, text: str, tokens: list[str]) -> dict[str, object]:
        found: list[str] = []
        primary: str | None = None
        texture = "smooth"
        for key, words in kw.MATERIAL_KEYWORDS.items():
            if kw.any_keyword(text, tokens, words):
                found.append(key)
                if primary is None:
                    primary = key
                if key in ("textured", "heavy"):
                    texture = key
        return {"primary": primary, "all": found, "texture": texture}

    def _detect_aesthetics(self, text: str, tokens: list[str]) -> list[str]:
        return [
            key
            for key, words in kw.AESTHETIC_MAP.items()
            if kw.any_keyword(text, tokens, words)
        ]

    def _extract_color(self, text: str, raw: ProductItem) -> str:
        if raw.color:
            return str(raw.color).lower()
        for candidate in kw.COLOR_KEYWORDS:
            if candidate in text:
                return "grey" if candidate == "gray" else candidate
        russian = lexicon.detect_colors(text)
        return russian[0] if russian else "unknown"

    def _color_temp(self, color: str) -> str:
        if color in kw.COOL_COLORS:
            return "cool"
        if color in kw.WARM_COLORS:
            return "warm"
        return "neutral"

    def _estimate_visual_weight(self, silhouette: list[str], materials: list[str], category: str) -> int:
        score = 50
        if {"oversized", "structured"} & set(silhouette):
            score += 20
        if {"heavy", "leather"} & set(materials):
            score += 25
        if {"sheer", "fluid"} & set(materials):
            score -= 15
        if "coat" in category or "jacket" in category:
            score += 15
        return int(clamp(score, 10, 100))

    def _estimate_layering(self, category: str, materials: list[str], silhouette: list[str]) -> str:
        if any(word in category for word in ("coat", "jacket", "cardigan", "blazer")):
            return "high"
        if {"sheer", "mesh"} & set(materials):
            return "high"
        if "oversized" in silhouette:
            return "medium"
        return "low"

    def _detect_historical(self, text: str) -> str | None:
        if any(word in text for word in ("archive", "vintage", "90s", "00s", "архив", "винтаж")):
            return "archive/vintage"
        if any(word in text for word in ("runway", " ss", " fw")):
            return "runway"
        return None

    def _infer_proportions(self, silhouette: list[str], category: str) -> str:
        if "oversized" in silhouette and any(word in category for word in ("top", "shirt", "blouse", "sweater", "knit")):
            return "voluminous upper"
        if "cropped" in silhouette:
            return "shortened"
        return "balanced"

    def _infer_fit(self, text: str, silhouette: list[str]) -> str:
        if "fitted" in silhouette or "slim" in text or "притал" in text:
            return "slim"
        if "oversized" in silhouette or "relaxed" in text or "свободн" in text:
            return "relaxed"
        return "regular"

    def _infer_construction(self, text: str) -> str:
        if any(word in text for word in ("deconstructed", "raw", "unfinished", "деконстру", "асимметр", "потерт")):
            return "deconstructed"
        if any(word in text for word in ("tailored", "structured", "структур", "классическ", "двубортн")):
            return "tailored"
        return "standard"

    def _infer_finish(self, text: str) -> str:
        if "matte" in text or "мат" in text:
            return "matte"
        if any(word in text for word in ("gloss", "satin", "shiny", "атлас", "глянц")):
            return "glossy"
        if any(word in text for word in ("washed", "faded", "потерт", "варен")):
            return "washed"
        return "natural"

    def _infer_length(self, text: str, category: str) -> str:
        if any(word in text for word in ("maxi", "floor", "longline", "макси", "удлинен", "длин")):
            return "long"
        if any(word in text for word in ("crop", "short", "мини", "коротк")):
            return "short"
        if "coat" in category or "dress" in category:
            return "long"
        return "regular"

    def _infer_designer_language(self, brand: str, text: str) -> str:
        lowered = (brand or "").lower()
        for key, value in kw.DESIGNER_LANGUAGE.items():
            if key in lowered or key in text:
                return value
        return "contemporary"

    def _detect_subculture(self, text: str) -> str | None:
        if any(word in text for word in ("punk", "goth", "готич", "панк")):
            return "post-punk/goth"
        if any(word in text for word in ("skate", "street", "уличн", "стрит")):
            return "street"
        if any(word in text for word in ("workwear", "utilitarian", "индустриальн", "утилитарн")):
            return "workwear"
        return None

    def _infer_season(self, text: str, materials: list[str]) -> str:
        if "heavy" in materials or any(word in text for word in ("wool", "coat", "шерст", "пуховик", "пальто")):
            return "fall/winter"
        if "sheer" in materials or any(word in text for word in ("linen", "cotton", "лен", "хлопок")):
            return "spring/summer"
        return "all-season"

    def _score_styling_potential(self, silhouette: list[str], materials: list[str], aesthetics: list[str]) -> int:
        score = 50
        if {"deconstructed", "oversized"} & set(silhouette):
            score += 20
        if {"sheer", "textured"} & set(materials):
            score += 15
        if len(aesthetics) > 1:
            score += 10
        if {"editorial", "avantgarde"} & set(aesthetics):
            score += 15
        return int_clamp(score)

    def _estimate_rarity(self, raw: ProductItem, text: str) -> int:
        if any(word in text for word in ("archive", "rare", "limited", "deadstock", "архив", "лимит")):
            return 85
        if raw.source_type in ("resale", "vintage"):
            return 70
        if any(word in text for word in ("independent", "emerging", "нишев")):
            return 65
        return 40
