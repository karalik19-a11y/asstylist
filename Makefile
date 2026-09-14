.PHONY: setup build run dev test test-backend test-frontend typecheck clean seed

VENV ?= .venv
PY   := $(VENV)/bin/python

setup:  ## install python + node dependencies
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	npm --prefix frontend install

build:  ## build the Mini App bundle
	npm --prefix frontend run build

run: build  ## serve API + built Mini App on :8000
	$(PY) -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000

dev:  ## backend with reload (frontend dev server runs on :5173 separately)
	$(PY) -m uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000

test: test-backend test-frontend  ## run the whole suite

test-backend:
	cd backend && ../$(PY) -m pytest

test-frontend:
	npm --prefix frontend run test

typecheck:
	cd frontend && npx tsc --noEmit -p tsconfig.json

seed:  ## re-seed and re-verify the demo catalog
	$(PY) -c "import sys; sys.path.insert(0,'backend'); from app.db import SessionLocal, init_db; from app.services.catalog_service import seed_catalog; init_db(); s=SessionLocal(); print(seed_catalog(s, force=True)); s.close()"

clean:
	rm -rf data frontend/dist .pytest_cache backend/.pytest_cache
