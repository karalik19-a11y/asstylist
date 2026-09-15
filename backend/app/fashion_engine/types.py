"""Core types (порт ``src/core/types.js`` + ``UserStyleProfile.js``).

Оригинал работал с обычными объектами; здесь — dataclass'ы, чтобы пайплайн
оставался типизованным. ``to_dict()`` отдаёт ровно те camelCase-ключи, которые
описаны в контракте движка (``README.md`` репозитория), поэтому ответы
``POST /api/engine/outfit`` совместимы с оригинальным API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .helpers import int_clamp

#: ``typedef {'generic'|'interesting'|...} TasteCategory`` из оригинала.
TASTE_CATEGORIES: tuple[str, ...] = (
    "generic",
    "interesting",
    "niche",
    "designer",
    "archive",
    "editorial",
    "cult",
    "exceptional",
)

DEFAULT_USER_PROFILE: dict[str, Any] = {
    "aesthetics": [],
    "preferredSilhouette": [],
    "dislikedItems": [],
    "colors": [],
    "budget": {},
    "nicheLevel": 60,
    "occasion": "everyday",
    "fitPreference": "regular",
    "gender": "unisex",
}


@dataclass
class FashionAttributes:
    """Structured fashion attributes — порт объекта из ``FashionIntelligence``."""

    silhouette: list[str] = field(default_factory=lambda: ["regular"])
    proportions: str = "balanced"
    fit: str = "regular"
    construction: str = "standard"
    material: str = "unknown"
    materials: list[str] = field(default_factory=list)
    texture: str = "smooth"
    color: str = "unknown"
    color_temperature: str = "neutral"
    finish: str = "natural"
    visual_weight: int = 50
    volume: str = "medium"
    length: str = "regular"
    layering_potential: str = "low"
    historical_reference: str | None = None
    designer_language: str = "contemporary"
    cultural_reference: list[str] = field(default_factory=list)
    subculture: str | None = None
    aesthetic: str = "contemporary"
    season: str = "all-season"
    styling_potential: int = 50
    rarity: int = 40
    fashion_relevance: float = 0.7
    current_relevance: float = 0.6
    editorial_relevance: float = 0.4
    # заполняется TrendEngine.enrich()
    trend_relevance: float = 0.4
    interesting_trend_score: float = 0.3
    popular_trend_score: float = 0.3

    def to_dict(self) -> dict[str, Any]:
        return {
            "silhouette": list(self.silhouette),
            "proportions": self.proportions,
            "fit": self.fit,
            "construction": self.construction,
            "material": self.material,
            "materials": list(self.materials),
            "texture": self.texture,
            "color": self.color,
            "colorTemperature": self.color_temperature,
            "finish": self.finish,
            "visualWeight": self.visual_weight,
            "volume": self.volume,
            "length": self.length,
            "layeringPotential": self.layering_potential,
            "historicalReference": self.historical_reference,
            "designerLanguage": self.designer_language,
            "culturalReference": list(self.cultural_reference),
            "subculture": self.subculture,
            "aesthetic": self.aesthetic,
            "season": self.season,
            "stylingPotential": self.styling_potential,
            "rarity": self.rarity,
            "fashionRelevance": round(self.fashion_relevance, 3),
            "currentRelevance": round(self.current_relevance, 3),
            "editorialRelevance": round(self.editorial_relevance, 3),
            "trendRelevance": round(self.trend_relevance, 3),
            "interestingTrendScore": round(self.interesting_trend_score, 3),
            "popularTrendScore": round(self.popular_trend_score, 3),
        }


@dataclass
class ProductItem:
    """Продукт, прошедший провайдер (порт ``ProductItem`` typedef).

    ``sku``/``product_id``/``meta`` — расширения asStylist: они позволяют
    вернуть вещь из движка обратно в каталог приложения без потери связи.
    """

    id: str
    name: str
    brand: str
    category: str
    price: float | None
    currency: str
    image: str
    source_url: str
    source_type: str
    availability: str
    confidence: float
    description: str = ""
    color: str | None = None
    tags: list[str] = field(default_factory=list)
    sku: str | None = None
    product_id: int | None = None
    provider: str = ""
    original_query: str = ""
    item_type: str = "product"

    # заполняются пайплайном
    fashion_score: int = 0
    taste_category: str = "interesting"
    generic_score: int = 0
    taste_components: dict[str, float] = field(default_factory=dict)
    role: str | None = None
    fashion_attributes: FashionAttributes | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    # --- удобства -----------------------------------------------------
    def searchable_text(self) -> str:
        return " ".join(
            filter(
                None,
                [
                    self.name,
                    self.brand,
                    self.description,
                    " ".join(self.tags),
                    self.category,
                    self.color or "",
                ],
            )
        ).lower()

    def to_dict(self) -> dict[str, Any]:
        attributes = self.fashion_attributes.to_dict() if self.fashion_attributes else {}
        return {
            "id": self.id,
            "sku": self.sku or self.id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "price": self.price,
            "currency": self.currency,
            "image": self.image,
            "sourceUrl": self.source_url,
            "sourceType": self.source_type,
            "availability": self.availability,
            "confidence": round(float(self.confidence or 0.7), 2),
            "fashionScore": int(self.fashion_score or 0),
            "tasteCategory": self.taste_category or "interesting",
            "role": self.role,
            "tags": list(self.tags),
            "description": self.description,
            "fashionAttributes": {
                key: attributes.get(key)
                for key in (
                    "silhouette",
                    "material",
                    "materials",
                    "color",
                    "aesthetic",
                    "layeringPotential",
                    "trendRelevance",
                    "interestingTrendScore",
                    "rarity",
                    "construction",
                    "texture",
                    "season",
                    "culturalReference",
                )
            },
        }


@dataclass
class StyleReference:
    """STYLE REFERENCE — никогда не товар (в оригинале ``StyleReference``)."""

    id: str
    source: str
    aesthetic: str
    detected_patterns: list[str] = field(default_factory=list)
    image: str = ""
    url: str = ""
    item_type: str = "reference"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "itemType": self.item_type,
            "source": self.source,
            "aesthetic": self.aesthetic,
            "detectedPatterns": list(self.detected_patterns),
            "image": self.image,
            "url": self.url,
        }


@dataclass
class UserStyleProfile:
    """Порт ``UserStyleProfile``: ниша, эстетики, бюджет, повод, посадка."""

    niche_level: int = 60
    aesthetics: list[str] = field(default_factory=list)
    budget_min: float | None = None
    budget_max: float | None = None
    currency: str = "RUB"
    occasion: str = "everyday"
    fit_preference: str = "regular"
    gender: str = "unisex"
    colors: list[str] = field(default_factory=list)
    preferred_silhouette: list[str] = field(default_factory=list)
    disliked_items: list[str] = field(default_factory=list)
    favorite_brands: list[str] = field(default_factory=list)
    disliked_brands: list[str] = field(default_factory=list)
    height_cm: float | None = None
    #: свободные подсказки из фото-анализа (колорит, силуэт) — используются
    #: при построении запроса, движок их только логирует.
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.niche_level = int_clamp(float(self.niche_level or 60), 0, 100)
        for attr in (
            "aesthetics",
            "colors",
            "preferred_silhouette",
            "disliked_items",
            "favorite_brands",
            "disliked_brands",
            "notes",
        ):
            value = getattr(self, attr)
            if not isinstance(value, list):
                setattr(self, attr, [value] if value else [])

    # --- поведение из оригинала ---------------------------------------
    def prefers_niche(self) -> bool:
        return self.niche_level >= 70

    def is_within_budget(self, price: float | None) -> bool:
        if price is None:
            return True
        if self.budget_min is not None and price < self.budget_min:
            return False
        if self.budget_max is not None and price > self.budget_max:
            return False
        return True

    def matches_aesthetic(self, aesthetic_tags: list[str] | None = None) -> bool:
        if not self.aesthetics:
            return True
        tags = [str(tag).lower() for tag in (aesthetic_tags or [])]
        if not tags:
            return False
        return any(
            wanted.lower() in tag or tag in wanted.lower()
            for tag in tags
            for wanted in self.aesthetics
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "nicheLevel": self.niche_level,
            "aesthetics": list(self.aesthetics),
            "budget": {
                "min": self.budget_min,
                "max": self.budget_max,
                "currency": self.currency,
            },
            "occasion": self.occasion,
            "fitPreference": self.fit_preference,
            "gender": self.gender,
            "colors": list(self.colors),
            "preferredSilhouette": list(self.preferred_silhouette),
            "dislikedItems": list(self.disliked_items),
            "favoriteBrands": list(self.favorite_brands),
            "dislikedBrands": list(self.disliked_brands),
            "heightCm": self.height_cm,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "UserStyleProfile":
        """Терпимый к формату конструктор: принимает и camelCase, и snake_case."""
        raw = dict(raw or {})
        budget = raw.get("budget") if isinstance(raw.get("budget"), dict) else {}
        return cls(
            niche_level=int(raw.get("nicheLevel", raw.get("niche_level", 60)) or 60),
            aesthetics=list(raw.get("aesthetics") or []),
            budget_min=raw.get("budgetMin", raw.get("budget_min", budget.get("min"))),
            budget_max=raw.get("budgetMax", raw.get("budget_max", budget.get("max"))),
            currency=str(raw.get("currency", budget.get("currency", "RUB")) or "RUB"),
            occasion=str(raw.get("occasion", "everyday") or "everyday"),
            fit_preference=str(raw.get("fitPreference", raw.get("fit_preference", "regular")) or "regular"),
            gender=str(raw.get("gender", "unisex") or "unisex"),
            colors=list(raw.get("colors") or []),
            preferred_silhouette=list(raw.get("preferredSilhouette", raw.get("preferred_silhouette")) or []),
            disliked_items=list(raw.get("dislikedItems", raw.get("disliked_items")) or []),
            favorite_brands=list(raw.get("favoriteBrands", raw.get("favorite_brands")) or []),
            disliked_brands=list(raw.get("dislikedBrands", raw.get("disliked_brands")) or []),
            height_cm=raw.get("heightCm", raw.get("height_cm")),
        )


@dataclass
class OutfitCandidate:
    """Результат ``OutfitArchitect`` — образ вокруг тезиса."""

    styling_thesis: str
    aesthetic: str
    items: list[ProductItem] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    outfit_score: float = 0.0
    score_breakdown: dict[str, float] = field(default_factory=dict)
    critic_decision: str = ""
    critic_feedback: list[str] = field(default_factory=list)
    critic_score_adjustment: float = 0.0
    styling_logic: dict[str, Any] = field(default_factory=dict)

    def item_count(self) -> int:
        return len(self.items)


@dataclass
class OutfitResult:
    """Финальный ответ движка (контракт §24 из оригинала)."""

    aesthetic: str
    styling_thesis: str
    outfit_score: float
    items: list[ProductItem] = field(default_factory=list)
    styling_logic: dict[str, Any] = field(default_factory=dict)
    references: list[StyleReference] = field(default_factory=list)
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    critic_feedback: list[str] = field(default_factory=list)
    critic_decision: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "aesthetic": self.aesthetic,
            "stylingThesis": self.styling_thesis,
            "outfitScore": self.outfit_score,
            "items": [item.to_dict() for item in self.items],
            "stylingLogic": self.styling_logic,
            "references": [reference.to_dict() for reference in self.references],
            "alternatives": self.alternatives,
            "criticFeedback": self.critic_feedback,
            "criticDecision": self.critic_decision,
            "meta": self.meta,
        }

    @classmethod
    def empty(cls, query: str, reason: str) -> "OutfitResult":
        """``_emptyResponse`` из оригинала."""
        return cls(
            aesthetic="unknown",
            styling_thesis="unable to form thesis",
            outfit_score=0.0,
            items=[],
            styling_logic={},
            references=[],
            alternatives=[],
            critic_feedback=[reason],
            critic_decision="REBUILD",
            meta={"error": True, "query": query},
        )
