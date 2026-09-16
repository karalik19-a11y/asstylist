# ADR 0005: Fashion Engine package boundary (in-tree)

## Status

Accepted

## Context

Agents need a clear place to extend search, taste, and outfit architecture without
touching HTTP, ranking weights of the application layer, or deploy config.

A full move to `packages/fashion_engine` would force a large import rewrite and
risk breaking the live site. The engine already lives under
`backend/app/fashion_engine/` and is mostly pure.

## Decision

1. Keep the physical path `backend/app/fashion_engine/` and import prefix
   `app.fashion_engine`.
2. Treat `__init__.__all__` as the **public surface**.
3. Document ordered steps in `pipeline.py` (`PIPELINE_STEPS`).
4. Enforce dependency direction: engine must not import `app.api`, `app.db`,
   or `app.services`.
5. Adapters (catalog → `ProductItem`) stay in `app.services.fashion_engine_service`.
6. Add boundary tests that only exercise the public surface and pipeline registry.

## Consequences

- Agents can target a single pipeline step with lower risk.
- Site imports and OpenAPI behaviour stay unchanged.
- A future standalone package can re-export the same symbols without API churn.
