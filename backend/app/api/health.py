"""Health + runtime info."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_session
from ..models import Look, Product, User

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health(session: Session = Depends(get_session)) -> dict:
    products = session.execute(select(func.count(Product.id))).scalar_one()
    eligible = session.execute(select(func.count(Product.id)).where(Product.active.is_(True))).scalar_one()
    looks = session.execute(select(func.count(Look.id))).scalar_one()
    users = session.execute(select(func.count(User.id))).scalar_one()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.version,
        "env": settings.app_env,
        "demo_mode": settings.demo_mode,
        "ai_provider": settings.effective_ai_provider,
        "budget_max_rub": settings.budget_max_rub,
        "telegram_configured": bool(settings.telegram_bot_token),
        "web_app_url": settings.telegram_web_app_url,
        "verification": {
            "network_enabled": settings.verification_network_enabled,
            "min_score": settings.verification_min_score,
            "ttl_days": settings.verification_ttl_days,
        },
        "db": {
            "url": settings.database_url.split("://")[0],
            "products": int(products),
            "eligible_products": int(eligible),
            "looks": int(looks),
            "users": int(users),
        },
    }
