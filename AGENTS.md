# Guide for AI Agents working on asStylist

This document is the primary contract for **any AI agent** (or human) making changes to this repository.
Follow it strictly so improvements stay safe and the live site / Telegram Mini App keep working.

## Project in one paragraph

asStylist is a free AI fashion director delivered as a **Telegram Mini App**.
User flow: photo → height/weight → style → mood → budget → generate look.
Backend is FastAPI + SQLite; frontend is React + TypeScript + Vite.
Core intelligence lives in `backend/app/fashion_engine/` (search + outfit architecture) and `backend/app/engine/` (ranking, budget, body, colors).

## Non-negotiable rules

1. **Do not break public HTTP contracts** under `/api/*` without an explicit versioned endpoint or ADR.
2. **Do not change default ranking weights, budget algorithm, or verification thresholds** without an ADR in `docs/adr/` and tests.
3. **Prefer pure, testable functions** in engine modules over changes in API handlers or UI.
4. **Always add or update tests** for behavior you change.
5. **Never commit secrets**. Use `.env.example` only.
6. **Demo / local mode must keep working** without bot tokens or paid API keys.
7. **One concern per PR** when possible (engine vs API vs frontend vs docs).
8. **Fashion Engine dependency rule:** code under `backend/app/fashion_engine/` must not import `app.api`, `app.db`, or `app.services`. Adapters stay in services.

## Safe zones (preferred for agents)

| Path | What to change |
| --- | --- |
| `backend/app/fashion_engine/**` | Search, taste, architect, scorer, critic, providers — see package [README](backend/app/fashion_engine/README.md) and `pipeline.PIPELINE_STEPS` |
| `backend/app/engine/**` | Ranking factors, budget optimiser, body/color helpers (with tests + ADR if defaults change) |
| `backend/app/verification/**` | Product checks (add tests; critical checks need ADR) |
| `backend/tests/**` or `backend/**/test_*.py` | Tests |
| `docs/**` | Architecture, ADRs, how-to guides |
| `AGENTS.md`, `CONTRIBUTING.md` | Agent/human process |

## Dangerous zones (human review required)

| Path | Why |
| --- | --- |
| `backend/app/main.py` | App wiring, static serving, lifespan |
| `backend/app/api/**` | Public HTTP surface |
| `frontend/src/pages/**`, `frontend/src/App*` | User-visible flows |
| `Dockerfile`, `docker-compose.yml`, `render.yaml` | Deploy / production |
| Ranking weight defaults / budget core loop | User-facing look quality and budget guarantees |
| Telegram auth / `initData` verification | Security |

## How to add a feature (checklist)

1. Read this file and `docs/architecture.md`.
2. For Fashion Engine work, read `backend/app/fashion_engine/README.md` and pick a step from `PIPELINE_STEPS`.
3. If the change affects ranking, budget, verification, or API shape → write `docs/adr/XXXX-title.md`.
4. Implement pure logic first under `fashion_engine/` or `engine/`.
5. Add unit tests; run `make test-backend` (or `make test-engine`).
6. Only then wire API / UI if needed.
7. Update `docs/adding-feature.md` section if you introduce a new extension point.
8. Keep commit messages imperative and scoped (`feat(engine): …`, `docs: …`, `test: …`).

## How to run locally (agents)

```bash
make setup
make test          # full suite
make test-backend  # pytest
make test-engine   # fashion_engine-focused
make typecheck
make run           # http://localhost:8000 — must still work after your change
```

Do **not** require network, bot tokens, or paid keys for unit tests.

## Extension points (stable)

- **Search providers**: `backend/app/fashion_engine/search/providers/` (`SearchProvider`)
- **Outfit pipeline steps**: `from app.fashion_engine import PIPELINE_STEPS` (expand → search → intelligence → validate → … → critic)
- **Ranking factors** (app layer): configurable via `RANKING_WEIGHTS_JSON` (defaults must not silently change)
- **Verification checks**: `backend/app/verification/`
- **Engine mode**: `FASHION_ENGINE_MODE` = `hybrid` | `engine` | `legacy`

## What “done” looks like

- Tests pass in CI
- No unintended API schema changes
- Demo mode still runs offline
- README / ADR updated when behavior or defaults change
- PR description lists risk level: `docs` | `safe-core` | `api` | `ui` | `deploy`
