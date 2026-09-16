# Task recipes cheatsheet

## Add a SearchProvider

1. `backend/app/fashion_engine/search/providers/my_provider.py`
2. Subclass `SearchProvider`, implement `search(query, context) -> list[ProductItem]`
3. Register in `providers/__init__.py` if needed
4. Gate costly/network providers with config (default off)
5. Tests with offline fixtures
6. Document env in `.env.example`

## Improve query expansion (RU)

1. `query_expander.py` and/or `keywords.py` / `lexicon.py`
2. Add cases in `tests/test_fashion_engine.py`
3. Keep expand count within existing bounds (see expander tests)

## Tune taste / anti-generic

1. `intelligence/taste_engine.py`
2. Cover niche vs mass-market cases with unit tests
3. Do not change app-layer ranking weights here

## Change outfit roles / architecture

1. `outfit/architect.py`
2. Ensure ≥ 3 items path still works; empty pool still returns structured empty result
3. Boundary + fashion_engine tests

## App budget or ranking defaults

1. **Write ADR first** (`docs/adr/`)
2. `backend/app/engine/budget.py` or `ranking.py`
3. Weights must still normalize to 1.0 if configurable
4. Prefer config override (`RANKING_WEIGHTS_JSON`) over silent default edits

## New API field (additive only)

1. Prefer optional fields; no renames/removals without ADR + version
2. Thin router in `api/`; logic in services/engine
3. TestClient tests
4. Risk label: `api`

## PR checklist

- [ ] Touched only intended zone
- [ ] Tests added/updated
- [ ] `make test-engine` or `make test` green
- [ ] ADR if defaults/contracts changed
- [ ] Risk label in PR body
