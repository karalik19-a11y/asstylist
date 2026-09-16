"""Память пользователя: рост и вес вводятся один раз."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..db import get_session
from ..services import look_service, profile_service
from ..telegram.auth import TelegramAuthError, authenticate

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _resolve_user(session: Session, payload: dict[str, Any]):
    try:
        identity = authenticate(
            payload.get("init_data"),
            payload.get("demo_user_id") or payload.get("telegram_id"),
        )
    except TelegramAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return look_service.get_or_create_user(session, identity)


def _query_payload(request: Request) -> dict[str, Any]:
    params = request.query_params
    return {
        "init_data": params.get("init_data"),
        "demo_user_id": params.get("demo_user_id"),
        "telegram_id": params.get("telegram_id"),
    }


async def _body_payload(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        return dict(form)
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Ожидался JSON-объект")
    return payload


@router.get("")
def read_profile(request: Request, session: Session = Depends(get_session)) -> dict[str, Any]:
    user = _resolve_user(session, _query_payload(request))
    return profile_service.get_profile(session, user)


@router.put("")
async def write_profile(request: Request, session: Session = Depends(get_session)) -> dict[str, Any]:
    payload = await _body_payload(request)
    user = _resolve_user(session, {**_query_payload(request), **payload})
    return profile_service.save_profile(session, user, payload)


@router.post("/used")
async def mark_used(request: Request, session: Session = Depends(get_session)) -> dict[str, Any]:
    payload = await _body_payload(request)
    user = _resolve_user(session, {**_query_payload(request), **payload})
    return profile_service.mark_used(session, user)


@router.post("/reset")
async def reset_profile(request: Request, session: Session = Depends(get_session)) -> dict[str, Any]:
    payload = await _body_payload(request)
    user = _resolve_user(session, {**_query_payload(request), **payload})
    return profile_service.forget_profile(session, user)


@router.delete("")
async def delete_profile(request: Request, session: Session = Depends(get_session)) -> dict[str, Any]:
    payload = await _body_payload(request)
    user = _resolve_user(session, {**_query_payload(request), **payload})
    return profile_service.forget_profile(session, user)


@router.post("/register")
async def register_profile(request: Request, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Assign immutable signature colour (personal ID). Idempotent."""
    payload = await _body_payload(request)
    user = _resolve_user(session, {**_query_payload(request), **payload})
    return profile_service.register_signature(session, user)


__all__ = ["router"]
