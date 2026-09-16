# Fashion Engine package boundary

**Location:** `backend/app/fashion_engine/`  
**Public import:** `from app.fashion_engine import …`  
**Version:** see `ENGINE_VERSION` in `engine.py`

This directory is a **logical package**: pure fashion discovery + outfit intelligence.
It must stay free of FastAPI routes, SQLAlchemy sessions, and Telegram concerns.

## Public surface (prefer these imports)

```python
from app.fashion_engine import (
    FashionEngine,
    create_outfit,
    EngineOptions,
    CatalogSearchProvider,
    SearchProvider,
    ProductItem,
    UserStyleProfile,
    TOOL_SCHEMA,
    ENGINE_VERSION,
)
from app.fashion_engine.pipeline import PIPELINE_STEPS, pipeline_as_dict
```

Everything listed in `__init__.__all__` is the supported API for agents.
Internal modules may change; the public surface should stay additive.

## Pipeline (extension map)

See `pipeline.py` for the ordered steps. Typical agent tasks:

| Goal | Touch |
| --- | --- |
| New product source | `search/providers/*` implementing `SearchProvider` |
| Better RU/EN queries | `search/query_expander.py`, `keywords.py`, `lexicon.py` |
| Taste / anti-generic | `intelligence/taste_engine.py` |
| Outfit roles | `outfit/architect.py` |
| Scoring / critic | `outfit/scorer.py`, `outfit/critic.py` |

## Dependency rule

```
fashion_engine  →  (stdlib + package-local only)
app.services / app.api / app.engine  →  may import fashion_engine
fashion_engine  ↛  app.services, app.api, app.db
```

Adapters that turn DB catalog rows into `ProductItem` live in
`app.services.fashion_engine_service`, not here.

## Tests

```bash
cd backend && python -m pytest tests/test_fashion_engine.py tests/test_fashion_engine_boundary.py -q
# or from repo root:
make test-engine
```

## Why not a separate repo yet?

Moving files would break every `app.fashion_engine` import and the live Mini App
for no user-facing gain. This boundary (README + pipeline registry + tests + ADR)
lets agents improve the engine safely; a physical extract can re-export the same
surface later without rewriting callers.
