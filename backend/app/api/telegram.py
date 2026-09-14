"""Telegram auth endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_session
from ..schemas import AuthRequest, AuthResponse, UserOut
from ..services.look_service import get_or_create_user
from ..telegram.auth import TelegramAuthError, authenticate

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.post("/auth", response_model=AuthResponse)
def auth(payload: AuthRequest, session: Session = Depends(get_session)) -> AuthResponse:
    try:
        identity = authenticate(payload.init_data, payload.demo_user_id)
    except TelegramAuthError as exc:
        raise HTTPException(status_code=401, detail=f"Telegram auth failed: {exc}") from exc

    if payload.first_name:
        identity.first_name = payload.first_name
    if payload.username:
        identity.username = payload.username

    user = get_or_create_user(session, identity)
    return AuthResponse(
        user=UserOut(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            is_demo=user.is_demo,
        ),
        demo=settings.demo_mode,
        mode="demo" if settings.demo_mode else "telegram",
        web_app_url=settings.telegram_web_app_url,
    )
