"""Shared test fixtures.

Environment is configured *before* importing the app, because settings and the
SQLAlchemy engine are created at import time.
"""

from __future__ import annotations

import os
import pathlib
import sys

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

TEST_DB = ROOT_DIR / "data" / "test_asstylist.db"
TEST_DB.parent.mkdir(parents=True, exist_ok=True)
for suffix in ("", "-wal", "-shm"):
    path = pathlib.Path(str(TEST_DB) + suffix)
    if path.exists():
        path.unlink()

os.environ["APP_ENV"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["STATIC_DIR"] = str(ROOT_DIR / "frontend" / "dist")
os.environ["DATA_DIR"] = str(ROOT_DIR / "data")
os.environ["AI_PROVIDER"] = "local"
os.environ["VERIFICATION_NETWORK_ENABLED"] = "false"
# Детерминированные тесты без сети: живой поиск Авито выключен, движок
# работает по локальному каталогу. Живой провайдер покрыт отдельно
# (test_avito_provider.py) через фикстуры HTML без единого HTTP-запроса.
os.environ["AVITO_ENABLED"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import SessionLocal, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services.catalog_service import seed_catalog  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _database():
    init_db()
    session = SessionLocal()
    try:
        seed_catalog(session, force=True)
    finally:
        session.close()
    yield


@pytest.fixture()
def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
