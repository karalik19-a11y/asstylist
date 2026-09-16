# asStylist — Agent Cheatsheet (1 page)

Full guide: [AGENTS.md](./AGENTS.md) · details: [docs/cheatsheets/](./docs/cheatsheets/)

## Before any code change

1. Read **safe vs dangerous** zones in `AGENTS.md`
2. Prefer `backend/app/fashion_engine/**` + tests
3. ADR required if: API shape, ranking defaults, budget, critical verification, deploy

## Commands

```bash
make setup && make test-engine   # engine safe-zone gate
make test                        # full suite before merge
make typecheck
make run                         # http://localhost:8000 must still work
```

## Where to edit (by goal)

| Goal | Path |
| --- | --- |
| New product source | `fashion_engine/search/providers/` (`SearchProvider`) |
| Better RU/EN queries | `search/query_expander.py`, `keywords.py`, `lexicon.py` |
| Taste / anti-generic | `intelligence/taste_engine.py` |
| Outfit roles | `outfit/architect.py` |
| Score / critic | `outfit/scorer.py`, `outfit/critic.py` |
| App budget / ranking | `app/engine/` (+ ADR if defaults) |
| Product checks | `app/verification/` |
| HTTP only | `app/api/` (**dangerous**) |
| UI | `frontend/src/` (**dangerous**) |

Pipeline map: `from app.fashion_engine import PIPELINE_STEPS`

## Do not

- Break `/api/*` without version/ADR
- Silently change ranking weights or budget guarantees
- Import `app.api` / `app.db` / `app.services` **from** `fashion_engine`
- Commit secrets; require bot tokens for unit tests
- Mix engine + UI + deploy in one PR

## PR risk label

`docs` | `safe-core` | `api` | `ui` | `deploy`
