"""asStylist API application."""

from __future__ import annotations

import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import catalog as catalog_api
from .api import engine as engine_api
from .api import health as health_api
from .api import looks as looks_api
from .api import telegram as telegram_api
from .config import settings
from .db import SessionLocal, init_db
from .engine.look_builder import LookGenerationError
from .services.catalog_service import seed_catalog
from .telegram.botapi import configure_bot


def _autoconfigure_telegram() -> None:
    """Attach the Mini App to the bot (menu button + commands + webhook).

    Runs in a daemon thread on boot so a slow/unreachable Telegram API can
    never delay or break startup. All failures are swallowed: the app must
    always start, with or without Telegram.
    """
    try:
        if not settings.telegram_autoconfigure or settings.app_env == "test":
            return
        token = settings.telegram_bot_token
        # Render injects RENDER_EXTERNAL_URL (https://<service>.onrender.com),
        # so an explicit TELEGRAM_WEB_APP_URL is optional there.
        base = (settings.telegram_web_app_url or os.environ.get("RENDER_EXTERNAL_URL") or "").rstrip("/")
        if not token or not base:
            return
        result = configure_bot(
            token,
            base,
            webhook_url=f"{base}{telegram_api.WEBHOOK_PATH}",
            webhook_secret=settings.admin_token,
        )
        if not settings.telegram_web_app_url:
            settings.telegram_web_app_url = result["web_app_url"]
        print(f"[telegram] bot autoconfigured: {'; '.join(result['actions'])}", flush=True)
    except Exception as exc:  # noqa: BLE001 — boot must never fail because of Telegram
        print(f"[telegram] autoconfigure skipped: {exc}", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.data_dir, exist_ok=True)
    init_db()
    session = SessionLocal()
    try:
        stats = seed_catalog(session)
        app.state.catalog_stats = stats
    finally:
        session.close()
    threading.Thread(target=_autoconfigure_telegram, name="telegram-autoconfigure", daemon=True).start()
    yield


app = FastAPI(
    title="asStylist API",
    version=settings.version,
    description="Personal stylist as a Telegram Mini App",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_api.router)
app.include_router(telegram_api.router)
app.include_router(looks_api.router)
app.include_router(catalog_api.router)
app.include_router(engine_api.router)


@app.exception_handler(LookGenerationError)
async def look_generation_error(_request: Request, exc: LookGenerationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc), "code": "look_generation_failed"})


@app.get("/api", include_in_schema=False)
def api_root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
        "meta": "/api/meta",
    }


# --- static SPA -------------------------------------------------------------
DIST_DIR = os.path.abspath(settings.static_dir)
ASSETS_DIR = os.path.join(DIST_DIR, "assets")
if os.path.isdir(DIST_DIR):
    if os.path.isdir(ASSETS_DIR):
        app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        candidate = os.path.abspath(os.path.join(DIST_DIR, full_path))
        if full_path and candidate.startswith(DIST_DIR) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
