# How to add common features

Use these recipes so agents and humans extend the system without breaking the site.

## Add a search provider

1. Create `backend/app/fashion_engine/search/providers/my_provider.py`
2. Implement the same interface as existing providers (see `catalog_provider.py`, `web_search_provider.py`)
3. Register in `providers/__init__.py`
4. Gate with a config flag (default off if network/cost involved)
5. Unit-test with offline fixtures
6. Document env vars in `.env.example`

## Add a ranking factor

1. ADR: why, weight proposal, impact on looks
2. Implement score component in `backend/app/engine/ranking.py` (or equivalent)
3. Ensure weights still normalize to 1.0
4. Expose override only via `RANKING_WEIGHTS_JSON` if configurable
5. Add tests for ordering and edge cases
6. Do **not** silently change production defaults without ADR

## Add a verification check

1. ADR if the check is critical (can exclude products)
2. Implement in verification module; assign weight
3. Add intentional failing fixtures if useful for demos
4. Cover with unit tests
5. Update catalog verification report expectations if needed

## Add an API endpoint

1. Prefer thin router in `backend/app/api/`
2. Business logic in services / engine
3. Pydantic request/response models in `schemas.py` (or colocated)
4. Tests via FastAPI TestClient
5. If breaking change → new path (`/api/v2/...`) or feature flag, not silent overwrite

## Add a frontend screen / flow

1. Keep demo mode working without Telegram
2. Use existing API clients; no hardcoded secrets
3. Vitest for logic; avoid brittle full-E2E unless necessary
4. Do not change generate-look happy path without product sign-off

## Port a change from upstream Fashion Engine

Source reference: original TS engine (see README link to `karalik19-a11y/-`).

1. Port pure logic into `backend/app/fashion_engine/`
2. Keep Russian keyword tables in sync when relevant
3. Golden / snapshot tests for representative queries
4. Hybrid mode must still respect budget optimiser

## Checklist before merge

- [ ] `make test` passes
- [ ] `make typecheck` passes
- [ ] ADR added if defaults or contracts change
- [ ] `.env.example` updated if new config
- [ ] Risk label in PR description
