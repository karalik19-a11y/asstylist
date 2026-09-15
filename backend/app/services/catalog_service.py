"""Catalog persistence + verification pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..catalog.products import seed_products
from ..config import settings
from ..engine.colors import hexes_for
from ..engine.ranking import CatalogItem
from ..models import Product
from ..verification.verifier import (
    STATUS_FAILED,
    STATUS_VERIFIED,
    STATUS_WARNING,
    compute_checksum,
    is_eligible,
    verify_product,
)


def _payload_from_model(product: Product) -> dict[str, Any]:
    return {
        "sku": product.sku,
        "category": product.category,
        "name": product.name,
        "brand": product.brand,
        "price_rub": product.price_rub,
        "currency": product.currency,
        "url": product.url,
        "source": product.source,
        "sizes": product.sizes_list(),
        "colors": product.colors_list(),
        "styles": product.styles_list(),
        "seasons": product.seasons_list(),
    }


def verify_and_persist(session: Session, payload: dict[str, Any], *, commit: bool = True) -> Product:
    """Run a product through the verification layer and upsert it."""
    outcome = verify_product(payload)
    colors = payload.get("colors") or []
    stmt = select(Product).where(Product.sku == payload.get("sku"), Product.source == payload.get("source", "demo"))
    product = session.execute(stmt).scalar_one_or_none()
    if product is None:
        product = Product(sku=payload.get("sku", ""), source=payload.get("source", "demo"))
        session.add(product)

    product.category = payload.get("category", "")
    product.name = payload.get("name", "")
    product.brand = payload.get("brand", "")
    product.price_rub = float(payload.get("price_rub") or 0)
    product.currency = payload.get("currency", "RUB")
    product.fit = payload.get("fit", "regular")
    product.formality = int(payload.get("formality", 2))
    product.colors = json.dumps(colors, ensure_ascii=False)
    product.color_hexes = json.dumps(payload.get("color_hexes") or hexes_for(colors), ensure_ascii=False)
    product.styles = json.dumps(payload.get("styles") or [], ensure_ascii=False)
    product.moods = json.dumps(payload.get("moods") or [], ensure_ascii=False)
    product.silhouettes = json.dumps(payload.get("silhouettes") or ["all"], ensure_ascii=False)
    product.gendered = json.dumps(payload.get("gendered") or [], ensure_ascii=False)
    product.seasons = json.dumps(payload.get("seasons") or ["all"], ensure_ascii=False)
    product.sizes = json.dumps(payload.get("sizes") or [], ensure_ascii=False)
    product.materials = json.dumps(payload.get("materials") or [], ensure_ascii=False)
    product.url = payload.get("url", "")
    product.image_url = payload.get("image_url", "")
    product.source = payload.get("source", "demo")
    product.rating = float(payload.get("rating", 4.0))
    product.reviews_count = int(payload.get("reviews_count", 0))

    product.verification_status = outcome.status
    product.verification_score = outcome.score
    product.verification_issues = json.dumps(outcome.issues, ensure_ascii=False)
    product.verified_at = datetime.fromisoformat(outcome.verified_at) if outcome.verified_at else None
    product.checksum = outcome.checksum
    product.active = is_eligible(outcome.status, outcome.score)

    if commit:
        session.commit()
    return product


def seed_catalog(session: Session, *, force: bool = False) -> dict[str, int]:
    """Seed the demo catalog (idempotent) and verify every row."""
    existing = session.execute(select(func.count(Product.id))).scalar_one()
    if existing and not force:
        return {"total": int(existing), "seeded": 0}

    rows = seed_products()
    for payload in rows:
        verify_and_persist(session, payload, commit=False)
    session.commit()
    return {"total": len(rows), "seeded": len(rows)}


def reverify_catalog(session: Session) -> dict[str, int]:
    products = session.execute(select(Product)).scalars().all()
    counts = {"verified": 0, "warning": 0, "failed": 0}
    for product in products:
        outcome = verify_product(_payload_from_model(product), expected_checksum=product.checksum)
        product.verification_status = outcome.status
        product.verification_score = outcome.score
        product.verification_issues = json.dumps(outcome.issues, ensure_ascii=False)
        product.verified_at = datetime.fromisoformat(outcome.verified_at) if outcome.verified_at else None
        product.active = is_eligible(outcome.status, outcome.score)
        counts[outcome.status] = counts.get(outcome.status, 0) + 1
    session.commit()
    return {"total": len(products), **counts}


def to_engine_item(product: Product) -> CatalogItem:
    return CatalogItem(
        product_id=product.id,
        sku=product.sku,
        category=product.category,
        name=product.name,
        brand=product.brand,
        price_rub=product.price_rub,
        url=product.url,
        image_url=product.image_url,
        colors=product.colors_list(),
        color_hexes=product.color_hexes_list() or hexes_for(product.colors_list()),
        styles=product.styles_list(),
        moods=product.moods_list(),
        silhouettes=product.silhouettes_list(),
        gendered=product.gendered_list(),
        seasons=product.seasons_list(),
        sizes=product.sizes_list(),
        fit=product.fit,
        formality=product.formality,
        rating=product.rating,
        reviews_count=product.reviews_count,
        verification_status=product.verification_status,
        verification_score=product.verification_score,
        source=product.source,
    )


def eligible_items(session: Session) -> list[CatalogItem]:
    """Only products the verification layer lets through."""
    products = session.execute(select(Product).where(Product.active.is_(True))).scalars().all()
    return [to_engine_item(p) for p in products]


def product_out(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "sku": product.sku,
        "category": product.category,
        "name": product.name,
        "brand": product.brand,
        "price_rub": product.price_rub,
        "url": product.url,
        "colors": product.colors_list(),
        "color_hexes": product.color_hexes_list() or hexes_for(product.colors_list()),
        "styles": product.styles_list(),
        "seasons": product.seasons_list(),
        "sizes": product.sizes_list(),
        "fit": product.fit,
        "formality": product.formality,
        "rating": product.rating,
        "reviews_count": product.reviews_count,
        "source": product.source,
        "verification_status": product.verification_status,
        "verification_score": product.verification_score,
        "verification_issues": product.issues_list(),
        "verified_at": product.verified_at,
    }


def verification_report(session: Session) -> dict[str, Any]:
    products = session.execute(select(Product)).scalars().all()
    by_status = {STATUS_VERIFIED: 0, STATUS_WARNING: 0, STATUS_FAILED: 0}
    items: list[dict[str, Any]] = []
    eligible = 0
    for product in products:
        by_status[product.verification_status] = by_status.get(product.verification_status, 0) + 1
        if product.active:
            eligible += 1
        items.append(
            {
                "sku": product.sku,
                "name": product.name,
                "source": product.source,
                "status": product.verification_status,
                "score": round(product.verification_score, 3),
                "issues": product.issues_list(),
                "checksum": product.checksum[:12],
            }
        )
    items.sort(key=lambda row: (row["score"], row["sku"]))
    return {
        "total": len(products),
        "verified": by_status.get(STATUS_VERIFIED, 0),
        "warning": by_status.get(STATUS_WARNING, 0),
        "failed": by_status.get(STATUS_FAILED, 0),
        "eligible": eligible,
        "network_enabled": settings.verification_network_enabled,
        "ttl_days": settings.verification_ttl_days,
        "min_score": settings.verification_min_score,
        "items": items,
    }


def checksum_of(product: Product) -> str:
    return compute_checksum(_payload_from_model(product))
