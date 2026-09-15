"""Catalog, taxonomy and verification endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_session
from ..engine.colors import COLORS, hexes_for
from ..engine.options import SLOT_PLANS, all_options
from ..catalog import generator
from ..models import Product
from ..schemas import ProductImportRequest
from ..services import catalog_service
from ..verification.sources import source_list

router = APIRouter(prefix="/api", tags=["catalog"])


def _require_admin(token: str | None) -> None:
    if settings.demo_mode and settings.admin_token == "asstylist-local-admin":
        return
    if token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Требуется ADMIN_TOKEN")


@router.get("/meta")
def meta() -> dict[str, Any]:
    """Everything the UI needs to render its selectors."""
    return {
        **all_options(),
        "colors": [
            {"id": cid, "label": spec.ru, "hex": spec.hex, "temperature": spec.temperature, "neutral": spec.neutral}
            for cid, spec in COLORS.items()
        ],
        "plans": [{"id": key, "description": value["description"]} for key, value in SLOT_PLANS.items()],
        "budget": {"min_rub": settings.budget_min_rub, "max_rub": settings.budget_max_rub, "currency": "RUB"},
        "ranking_weights": settings.resolved_ranking_weights(),
        "sources": source_list(),
        "demo_mode": settings.demo_mode,
        "telegram": {
            "configured": bool(settings.telegram_bot_token),
            "web_app_url": settings.telegram_web_app_url,
            "bot_link": None,
        },
        "ai_provider": settings.effective_ai_provider,
        "version": settings.version,
    }


@router.get("/catalog/feed")
def feed(cursor: int = Query(default=0, ge=0), count: int = Query(default=12, ge=1, le=48), style: str | None = Query(default=None)) -> dict[str, Any]:
    """An endless, deterministic trend feed (niche items + photo + working link)."""
    items, next_cursor = generator.generate_items(cursor, count)
    if style:
        items = [i for i in items if i["style"] == style]
    return {"cursor": next_cursor, "next": next_cursor, "items": items}


@router.get("/catalog/items")
def items(
    session: Session = Depends(get_session),
    category: str | None = Query(default=None),
    style: str | None = Query(default=None),
    max_price: float | None = Query(default=None, gt=0),
    verified_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    stmt = select(Product).order_by(Product.category, Product.price_rub)
    if category:
        stmt = stmt.where(Product.category == category)
    if max_price:
        stmt = stmt.where(Product.price_rub <= max_price)
    if verified_only:
        stmt = stmt.where(Product.active.is_(True))
    rows = session.execute(stmt.limit(limit)).scalars().all()
    products = [catalog_service.product_out(p) for p in rows]
    if style:
        products = [p for p in products if style in p["styles"]]
    return {"total": len(products), "items": products}


@router.get("/catalog/verification")
def verification(session: Session = Depends(get_session)) -> dict[str, Any]:
    return catalog_service.verification_report(session)


@router.post("/catalog/reverify")
def reverify(session: Session = Depends(get_session), x_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    _require_admin(x_admin_token)
    return catalog_service.reverify_catalog(session)


@router.post("/catalog/import")
def import_products(
    body: ProductImportRequest,
    session: Session = Depends(get_session),
    x_admin_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """Import external products. Every row goes through the verification layer."""
    _require_admin(x_admin_token)
    results: list[dict[str, Any]] = []
    for payload in body.products:
        product = catalog_service.verify_and_persist(session, payload)
        results.append(
            {
                "sku": product.sku,
                "status": product.verification_status,
                "score": round(product.verification_score, 3),
                "issues": product.issues_list(),
                "eligible": product.active,
            }
        )
    accepted = sum(1 for row in results if row["eligible"])
    return {"total": len(results), "accepted": accepted, "rejected": len(results) - accepted, "results": results}


@router.post("/catalog/seed")
def seed(session: Session = Depends(get_session), x_admin_token: str | None = Header(default=None), force: bool = False):
    _require_admin(x_admin_token)
    return catalog_service.seed_catalog(session, force=force)


@router.get("/catalog/colors")
def colors() -> dict[str, Any]:
    return {"items": [{"id": cid, "hex": spec.hex, "label": spec.ru} for cid, spec in COLORS.items()], "hexes": hexes_for(list(COLORS))}
