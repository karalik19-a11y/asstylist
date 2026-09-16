# Architecture overview

asStylist is a single-origin app: FastAPI serves both the JSON API and the built Mini App static files.

```
Telegram Mini App (React + TS + Vite)
        │  fetch /api/*  (same origin)
        ▼
FastAPI
   ├── Fashion Engine (search + outfit architecture)
   ├── Ranking + Budget optimiser (application guarantees)
   ├── Verification layer
   ├── Vision (local Pillow; optional cloud)
   └── SQLite (SQLAlchemy)
```

## Layers

### 1. Frontend (`frontend/`)

- Telegram WebApp SDK + demo browser mode
- Pages: home → profile inputs → generate → result; plus engine search screen
- Must not assume backend secrets; only public API

### 2. API (`backend/app/api/`)

Thin HTTP adapters. Prefer putting logic in services / engine modules.
Public contracts are documented at `/docs` (OpenAPI).

### 3. Fashion Engine (`backend/app/fashion_engine/`)

Offline-capable pipeline:

1. Query expansion
2. Search providers (catalog, mock, optional web)
3. Fashion intelligence (materials, silhouette, palette, trends)
4. Taste + anti-generic filtering
5. Validation + identity resolution
6. Outfit architect (roles)
7. Scorer + critic

Modes via `FASHION_ENGINE_MODE`: `hybrid` (default), `engine`, `legacy`.

### 4. Application engine (`backend/app/engine/`)

Guarantees budget, sizes, seasonality, and explainability:

- Body / silhouette from height, weight, photo
- Color palette
- Ranking factors (weights configurable; defaults stable)
- Budget optimiser (never exceeds budget)

### 5. Verification (`backend/app/verification/`)

Products must pass checks before entering looks. Critical failures exclude the item entirely.

### 6. Data

- SQLite by default (`DATABASE_URL` can point to Postgres later)
- Demo catalog seeded and re-verifiable via `make seed`

## Stability boundaries

| Boundary | Stability |
| --- | --- |
| HTTP `/api/*` shapes | High — version or ADR to change |
| Engine pipeline step interfaces | Medium — prefer additive |
| Ranking default weights | High — ADR required |
| Provider implementations | Low — free to improve behind interface |
| UI copy / layout | Medium |

## Deploy notes

Production is typically one process (see `Dockerfile`, `render.yaml`).
Static frontend is built into the image / served by FastAPI.
Changes to deploy files need human review (see AGENTS.md dangerous zones).
