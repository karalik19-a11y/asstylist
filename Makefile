.PHONY: setup build run dev test test-backend test-frontend test-engine typecheck clean seed connect-tg help agent-check

VENV ?= .venv
PY   := $(VENV)/bin/python

help:  ## list common targets (agent-friendly entrypoint)
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?##"}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

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

test-backend:  ## backend pytest suite
	cd backend && ../$(PY) -m pytest

test-engine:  ## fashion_engine + ranking/budget focused tests (safe zone for agents)
	cd backend && ../$(PY) -m pytest -q tests/test_fashion_engine.py tests/test_fashion_engine_boundary.py tests/test_fashion_engine_service.py -k "engine or fashion or ranking or budget or verification or look_builder or boundary" --tb=short || ../$(PY) -m pytest -q -k "engine or fashion or ranking or budget or verification or look_builder or boundary" --tb=short

test-frontend:  ## frontend vitest
	npm --prefix frontend run test

typecheck:  ## TypeScript noEmit
	cd frontend && npx tsc --noEmit -p tsconfig.json

agent-check: test-engine typecheck  ## minimal gate before opening a safe-core PR
	@echo "agent-check OK — still run full make test before merge"

connect-tg:  ## подключить бота: make connect-tg BOT_TOKEN=123:ABC WEB_APP_URL=https://your.app
	@test -n "$(BOT_TOKEN)" || (echo "Нужен BOT_TOKEN от @BotFather" && exit 1)
	@test -n "$(WEB_APP_URL)" || (echo "Нужен WEB_APP_URL (публичный https-адрес)" && exit 1)
	$(PY) backend/scripts/connect_bot.py --token "$(BOT_TOKEN)" --url "$(WEB_APP_URL)"

refresh-avito:  ## обновить снимок реальной выдачи Авито (нужна сеть до avito.ru)
	$(PY) backend/scripts/refresh_avito_snapshot.py --per-query 5 --delay 4

seed:  ## re-seed and re-verify the demo catalog
	$(PY) -c "import sys; sys.path.insert(0,'backend'); from app.db import SessionLocal, init_db; from app.services.catalog_service import seed_catalog; init_db(); s=SessionLocal(); print(seed_catalog(s, force=True)); s.close()"

clean:  ## remove local build/cache artifacts
	rm -rf data frontend/dist .pytest_cache backend/.pytest_cache
