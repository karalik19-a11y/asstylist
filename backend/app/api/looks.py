"""Look endpoints: generate, history, swap, favourite."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_session
from ..engine.look_builder import LookGenerationError
from ..schemas import LookRequest
from ..services import look_service, profile_service
from ..telegram.auth import TelegramAuthError, authenticate
from ..vision import ai as vision_ai
from ..vision.analyzer import VisionError

router = APIRouter(prefix="/api/looks", tags=["looks"])


def _as_color_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(v) for v in raw]
    text = str(raw).strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            return [str(v) for v in parsed] if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return [part.strip() for part in text.split(",") if part.strip()]


def _form_to_payload(form: Any) -> dict[str, Any]:
    def value(key: str, default: Any = None) -> Any:
        raw = form.get(key)
        return default if raw is None or raw == "" else raw

    payload: dict[str, Any] = {
        "style": value("style", "minimal"),
        "mood": value("mood", "calm"),
        "occasion": value("occasion", "everyday"),
        "season": value("season", "all"),
        "presentation": value("presentation", "unisex"),
        "height_cm": float(value("height_cm", 172)),
        "weight_kg": float(value("weight_kg", 68)),
        "budget_rub": float(value("budget_rub", 50_000)),
        "preferred_colors": _as_color_list(value("preferred_colors")),
        "avoid_colors": _as_color_list(value("avoid_colors")),
        "size": value("size"),
        "plan": value("plan"),
        "query": value("query"),
        "niche_level": value("niche_level"),
        "telegram_id": value("telegram_id"),
        "init_data": value("init_data"),
        "demo_user_id": value("demo_user_id"),
        "save": str(value("save", "true")).lower() not in ("false", "0", "no"),
    }
    return payload


async def _read_photo(form: Any) -> tuple[bytes | None, str]:
    upload = form.get("photo")
    # Duck-typed on purpose: starlette hands us its own UploadFile, which is the
    # *parent* of fastapi.UploadFile, so an isinstance() check would miss it.
    if upload is None or isinstance(upload, str) or not hasattr(upload, "read"):
        return None, ""
    if not getattr(upload, "filename", None):
        return None, ""
    content_type = (upload.content_type or "").lower()
    if content_type and content_type not in settings.allowed_upload_types:
        raise HTTPException(status_code=415, detail=f"Неподдерживаемый тип файла: {content_type}")
    data = await upload.read()
    if len(data) > settings.upload_max_bytes:
        raise HTTPException(status_code=413, detail="Файл слишком большой (максимум 10 МБ)")
    return data, content_type


def _resolve_user(session: Session, payload: dict[str, Any]):
    try:
        identity = authenticate(payload.get("init_data"), payload.get("demo_user_id") or payload.get("telegram_id"))
    except TelegramAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return look_service.get_or_create_user(session, identity)


@router.post("/generate")
async def generate(request: Request, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Generate a look. Accepts multipart/form-data (with photo) or JSON."""
    content_type = request.headers.get("content-type", "")
    vision: dict[str, Any] | None = None
    photo_digest = ""
    photo_path = ""

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        payload = _form_to_payload(form)
        data, _ctype = await _read_photo(form)
        if data:
            try:
                vision = vision_ai.analyze(data)
            except VisionError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            photo_digest = vision.get("sha256", hashlib.sha256(data).hexdigest())
            if settings.store_photos:
                os.makedirs(os.path.join(settings.data_dir, "uploads"), exist_ok=True)
                photo_path = os.path.join(settings.data_dir, "uploads", f"{photo_digest[:24]}.img")
                with open(photo_path, "wb") as handle:
                    handle.write(data)
    else:
        try:
            raw = await request.json()
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Некорректный JSON") from exc
        if not isinstance(raw, dict):
            raise HTTPException(status_code=400, detail="Ожидался JSON-объект")
        payload = dict(raw)

    try:
        validated = LookRequest(**payload).model_dump()
    except Exception as exc:  # pydantic.ValidationError and friends
        raise HTTPException(status_code=422, detail=f"Некорректные параметры: {exc}") from exc

    user = _resolve_user(session, payload)
    try:
        look = look_service.generate_and_save(
            session,
            user,
            validated,
            vision,
            save=bool(validated.get("save", True)),
            photo_digest=photo_digest,
            photo_path=photo_path,
            ai_provider=settings.effective_ai_provider,
        )
    except LookGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Рост и вес запоминаем автоматически: в следующий раз их не придётся
    # вводить заново — сервис предложит выбор «сохранённые / новые».
    profile_service.remember_body(
        session, user, validated.get("height_cm"), validated.get("weight_kg")
    )

    payload_out = look_service.serialize_look(look)
    memory = profile_service.get_profile(session, user)
    payload_out["profile"] = memory
    return payload_out


@router.get("")
def history(request: Request, session: Session = Depends(get_session), limit: int = 50) -> dict[str, Any]:
    user = _resolve_user(session, _query_payload(request))
    return {"items": look_service.list_looks(session, user.id, limit=min(max(limit, 1), 100))}


@router.get("/{look_id}")
def get_one(look_id: int, request: Request, session: Session = Depends(get_session)) -> dict[str, Any]:
    user = _resolve_user(session, _query_payload(request))
    look = look_service.get_look(session, look_id, user.id)
    if look is None:
        raise HTTPException(status_code=404, detail="Образ не найден")
    return look_service.serialize_look(look)


@router.post("/{look_id}/swap")
def swap(look_id: int, request_body: dict[str, Any], request: Request, session: Session = Depends(get_session)):
    user = _resolve_user(session, _query_payload(request))
    look = look_service.get_look(session, look_id, user.id)
    if look is None:
        raise HTTPException(status_code=404, detail="Образ не найден")
    slot = str(request_body.get("slot", ""))
    try:
        updated = look_service.swap_slot(session, look, slot, request_body.get("exclude_skus") or [])
    except LookGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return look_service.serialize_look(updated)


@router.post("/{look_id}/favorite")
def favorite(look_id: int, request: Request, session: Session = Depends(get_session)) -> dict[str, Any]:
    user = _resolve_user(session, _query_payload(request))
    look = look_service.get_look(session, look_id, user.id)
    if look is None:
        raise HTTPException(status_code=404, detail="Образ не найден")
    look.is_favorite = not look.is_favorite
    session.commit()
    return {"id": look.id, "is_favorite": look.is_favorite}


def _query_payload(request: Request) -> dict[str, Any]:
    params = request.query_params
    return {
        "init_data": params.get("init_data"),
        "demo_user_id": params.get("demo_user_id"),
        "telegram_id": params.get("telegram_id"),
    }
