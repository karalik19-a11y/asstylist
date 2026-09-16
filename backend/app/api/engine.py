"""API движка ASSTYLIST Fashion Discovery & Outfit Intelligence Engine.

Три вещи:

* ``POST /api/engine/search`` — свободный текстовый поиск вещей только на
  Авито: движок расширяет запрос, ищет живые объявления, оценивает вкус и
  собирает образ;
* ``POST /api/engine/outfit`` — контракт оригинального движка
  (``{aesthetic, stylingThesis, outfitScore, items[], stylingLogic, …}``),
  удобно для агентов и внешних интеграций;
* ``GET /api/engine/health|schema|taxonomy`` — состояние, TOOL_SCHEMA и словари.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import BUDGET_CEILING_RUB, settings
from ..db import get_session
from ..engine.look_builder import LookGenerationError
from ..fashion_engine import (
    CatalogSearchProvider,
    EngineOptions,
    FashionEngine,
    MockRealProductProvider,
    TASTE_CATEGORIES,
    TOOL_SCHEMA,
)
from ..fashion_engine import keywords as engine_keywords
from ..fashion_engine.lexicon import ROLE_LABELS_RU, TASTE_LABELS_RU
from ..services import catalog_service, fashion_engine_service

router = APIRouter(prefix="/api/engine", tags=["engine"])


class EngineSearchRequest(BaseModel):
    """Запрос свободного поиска. Обязателен только текст."""

    query: str = Field(min_length=2, max_length=240)
    style: str = "minimal"
    mood: str = "calm"
    occasion: str = "everyday"
    season: str = "all"
    presentation: str = "unisex"
    height_cm: float = Field(default=172, ge=120, le=230)
    weight_kg: float = Field(default=68, ge=30, le=250)
    budget_rub: float = Field(default=50_000, ge=1_000, le=BUDGET_CEILING_RUB)
    preferred_colors: list[str] = Field(default_factory=list)
    avoid_colors: list[str] = Field(default_factory=list)
    size: str | None = None
    niche_level: int | None = Field(default=None, ge=0, le=100)
    limit: int = Field(default=8, ge=1, le=24)


class EngineOutfitRequest(BaseModel):
    """Контракт оригинального движка (camelCase-поля как в JS-версии)."""

    query: str = Field(min_length=2, max_length=240)
    nicheLevel: int | None = Field(default=None, ge=0, le=100)
    niche_level: int | None = Field(default=None, ge=0, le=100)
    budgetMax: float | None = Field(default=None, gt=0, le=BUDGET_CEILING_RUB)
    budget_max: float | None = Field(default=None, gt=0, le=BUDGET_CEILING_RUB)
    currency: str = "RUB"
    aesthetics: list[str] = Field(default_factory=list)
    occasion: str = "everyday"
    fitPreference: str | None = None
    fit_preference: str | None = None
    max_products: int = Field(default=40, ge=3, le=200)


def _cards(session: Session):
    return [fashion_engine_service.to_engine_card(item) for item in catalog_service.eligible_items(session)]


def _engine(cards, max_products: int) -> FashionEngine:
    providers: list[Any] = [CatalogSearchProvider(cards)]
    if settings.fashion_engine_enable_mock:
        providers.append(MockRealProductProvider())
    return FashionEngine(
        providers=providers,
        options=EngineOptions(
            max_products=max_products,
            limit_per_query=settings.fashion_engine_limit_per_query,
            min_confidence=settings.fashion_engine_min_confidence,
        ),
    )


@router.get("/health")
def health(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Состояние движка: версия, пайплайн, размер пула каталога."""
    from ..fashion_engine import ENGINE_VERSION

    items = catalog_service.eligible_items(session)
    avito = fashion_engine_service.avito_provider()
    return {
        "status": "ok",
        "engine": "ASSTYLIST Fashion Discovery & Outfit Intelligence Engine",
        "engine_version": ENGINE_VERSION,
        "pipeline": fashion_engine_service.PIPELINE,
        "enabled": settings.fashion_engine_enabled,
        "runtime_mode": settings.fashion_engine_mode,
        "allow_fallback": settings.fashion_engine_allow_fallback,
        "mock_provider": settings.fashion_engine_enable_mock,
        "score_weight": settings.fashion_engine_score_weight,
        "catalog": {
            "eligible_items": len(items),
            "currency": "RUB",
            "budget_max_rub": settings.budget_max_rub,
        },
        "avito": {
            "enabled": settings.avito_enabled,
            "city": settings.avito_city,
            "max_queries": settings.avito_max_queries,
            "max_results": settings.avito_max_results,
            "cache_entries": avito.cache_size,
            "last_live_ok": avito.last_live_ok,
            "last_error": avito.last_error,
        },
        "source": "https://github.com/karalik19-a11y/- (каталог fashion-engine, MIT)",
    }


@router.get("/schema")
def schema() -> dict[str, Any]:
    """TOOL_SCHEMA движка — для function-calling агентов."""
    return TOOL_SCHEMA


@router.get("/taxonomy")
def taxonomy() -> dict[str, Any]:
    """Словари движка, которые использует приложение."""
    return {
        "taste_categories": [
            {"id": key, "label": TASTE_LABELS_RU.get(key, key)} for key in TASTE_CATEGORIES
        ],
        "roles": [{"id": key, "label": value} for key, value in ROLE_LABELS_RU.items()],
        "theses": [
            {"id": key, "label": value} for key, value in engine_keywords.THESIS_LABELS_RU.items()
        ],
        "aesthetics": sorted(engine_keywords.AESTHETIC_MAP),
        "style_profiles": {
            key: {"niche_level": value["niche"], "aesthetics": value["aesthetics"]}
            for key, value in fashion_engine_service.STYLE_ENGINE.items()
        },
    }


@router.post("/search")
def search(body: EngineSearchRequest, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Свободный поиск вещей по движку (образ не сохраняется)."""
    payload = body.model_dump()
    limit = payload.pop("limit", 8)
    try:
        return fashion_engine_service.search(payload, catalog_service.eligible_items(session), limit=limit)
    except LookGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/outfit")
def outfit(body: EngineOutfitRequest, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Собрать образ движком и вернуть ответ в контракте оригинального API."""
    cards = _cards(session)
    engine = _engine(cards, body.max_products)
    profile = {
        "nicheLevel": body.nicheLevel if body.nicheLevel is not None else (body.niche_level or 60),
        "aesthetics": list(body.aesthetics),
        "budget": {"max": body.budgetMax if body.budgetMax is not None else body.budget_max, "currency": body.currency},
        "occasion": body.occasion,
        "fitPreference": body.fitPreference or body.fit_preference or "regular",
    }
    result = engine.create_outfit(body.query.strip(), profile)
    payload = result.to_dict()
    payload.setdefault("meta", {})
    if settings.avito_enabled:
        payload["meta"]["catalog"] = {
            "provider": "avito",
            "city": settings.avito_city,
            "currency": "RUB",
            "source": "live Avito listings",
        }
    else:
        payload["meta"]["catalog"] = {
            "provider": "app-catalog",
            "cards": len(cards),
            "currency": "RUB",
            "source": "verified asStylist catalog",
        }
    return payload
