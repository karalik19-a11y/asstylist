"""API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from .config import BUDGET_CEILING_RUB
from .engine.colors import COLORS


def _clean_color_list(value: list[str] | None) -> list[str]:
    if not value:
        return []
    return [v.strip().lower() for v in value if isinstance(v, str) and v.strip().lower() in COLORS]


# The public taxonomy is intentionally richer than the legacy service profile.
# Keep the selected v2 style in the request/DB, but inject a precise search thesis
# so the live Avito discovery layer cannot silently fall back to generic "minimal".
STYLE_INTENT_V21: dict[str, dict[str, Any]] = {
    "modern_craftsman": {"niche": 78, "seed": "modern craftsman worn workwear chore coat washed denim suede utility texture barn jacket"},
    "leather_weather": {"niche": 84, "seed": "worn leather moto biker jacket distressed suede burgundy soft knit long line"},
    "broken_down_prep": {"niche": 80, "seed": "broken down ivy prep surf tailoring relaxed oxford washed rugby cardigan loafers"},
    "romantic_menswear": {"niche": 88, "seed": "romantic menswear draped tailoring sheer mesh lace fluid shirt elongated trousers"},
    "military_romance": {"niche": 90, "seed": "military romance field jacket utility victorian floral brooch velvet structured"},
    "archive_reconstruction": {"niche": 94, "seed": "archive reworked reconstructed deconstructed asymmetry deadstock raw seam rare vintage"},
    "technical_romantic": {"niche": 87, "seed": "technical romantic nylon utility mesh drape modular pocket asymmetric layer"},
    "americana_90s": {"niche": 79, "seed": "90s americana vintage sportswear plaid straight denim frontier knit worn leather"},
    "accessory_first": {"niche": 86, "seed": "statement chain cuff charm belt silver hardware sculptural accessory"},
    "pink_accent": {"niche": 76, "seed": "dusty pink accent washed pink burgundy brown leather precise tailoring"},
    "sport_couture": {"niche": 82, "seed": "sport couture retro football rugby track jacket tailoring wide trousers technical sneaker"},
    "neo_gothic_editorial": {"niche": 92, "seed": "neo gothic editorial black leather velvet elongated silhouette silver hardware"},
    "post_punk_archive": {"niche": 93, "seed": "post punk archive distressed black leather raw denim asymmetry vintage hardware"},
    "minimal_precision": {"niche": 72, "seed": "minimal precision architectural cut unusual proportion premium fabric monochrome"},
}


class AuthRequest(BaseModel):
    init_data: str | None = None
    demo_user_id: str | None = None
    first_name: str | None = None
    username: str | None = None


class UserOut(BaseModel):
    id: int
    telegram_id: str
    username: str | None = None
    first_name: str | None = None
    is_demo: bool = False


class AuthResponse(BaseModel):
    user: UserOut
    demo: bool
    mode: str
    web_app_url: str | None = None


class LookRequest(BaseModel):
    """JSON variant of the generate request (multipart is also supported)."""

    style: str = Field(default="minimal", max_length=48)
    mood: str = Field(default="calm", max_length=48)
    occasion: str = Field(default="everyday", max_length=48)
    season: str = Field(default="all", max_length=24)
    presentation: str = Field(default="unisex", max_length=24)
    height_cm: float = Field(default=172, ge=120, le=230)
    weight_kg: float = Field(default=68, ge=30, le=250)
    budget_rub: float = Field(default=50_000, ge=1_000, le=BUDGET_CEILING_RUB)
    preferred_colors: list[str] = Field(default_factory=list)
    avoid_colors: list[str] = Field(default_factory=list)
    size: str | None = Field(default=None, max_length=8)
    plan: str | None = None
    query: str | None = Field(default=None, max_length=240)
    niche_level: int | None = Field(default=None, ge=0, le=100)
    user_id: int | None = None
    telegram_id: str | None = None
    save: bool = True

    _v_pref = field_validator("preferred_colors", mode="before")(lambda cls, v: _clean_color_list(v))
    _v_avoid = field_validator("avoid_colors", mode="before")(lambda cls, v: _clean_color_list(v))

    @model_validator(mode="after")
    def inject_v21_style_intent(self) -> "LookRequest":
        intent = STYLE_INTENT_V21.get(self.style)
        if intent:
            if self.niche_level is None:
                self.niche_level = int(intent["niche"])
            seed = str(intent["seed"])
            if self.query:
                # User wording stays first; the style thesis is an explicit second
                # signal instead of replacing what the user actually asked for.
                self.query = f"{self.query.strip()} · {seed}"[:240]
            else:
                self.query = seed[:240]
        return self


class SwapRequest(BaseModel):
    slot: str
    exclude_skus: list[str] = Field(default_factory=list)


class LookItemOut(BaseModel):
    position: int
    slot: str
    slot_label: str
    sku: str
    category: str
    name: str
    brand: str
    price_rub: float
    url: str
    image_url: str = ""
    colors: list[str] = Field(default_factory=list)
    color_hexes: list[str] = Field(default_factory=list)
    fit: str = "regular"
    score: float
    breakdown: dict[str, Any] = Field(default_factory=dict)
    engine: dict[str, Any] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    verification_status: str = "verified"
    verification_score: float = 0.0
    source: str = "demo"
    alternatives: list[dict[str, Any]] = Field(default_factory=list)


class LookOut(BaseModel):
    id: int | None = None
    created_at: datetime | None = None
    user_id: int | None = None
    style: str
    mood: str
    occasion: str
    season: str
    presentation: str
    height_cm: float
    weight_kg: float
    budget_rub: float
    total_rub: float
    budget_utilization: float
    score: float
    verdict: dict[str, str]
    cohesion: dict[str, float]
    summary: str
    tips: list[str]
    body: dict[str, Any]
    palette: dict[str, Any]
    plan: str
    engine_version: str
    engine: dict[str, Any] = Field(default_factory=dict)
    diagnostics: dict[str, Any]
    items: list[LookItemOut]
    is_favorite: bool = False
    version: int = 1
    ai_provider: str = "local"
    photo_digest: str = ""


class ProductOut(BaseModel):
    id: int
    sku: str
    category: str
    name: str
    brand: str
    price_rub: float
    url: str
    colors: list[str]
    color_hexes: list[str]
    styles: list[str]
    seasons: list[str]
    sizes: list[str]
    fit: str
    formality: int
    rating: float
    reviews_count: int
    source: str
    verification_status: str
    verification_score: float
    verification_issues: list[str]
    verified_at: datetime | None = None


class VerificationReport(BaseModel):
    total: int
    verified: int
    warning: int
    failed: int
    eligible: int
    network_enabled: bool
    ttl_days: int
    min_score: float
    items: list[dict[str, Any]]


class ProductImportRequest(BaseModel):
    products: list[dict[str, Any]]


class ErrorResponse(BaseModel):
    detail: str
    code: str = "error"
