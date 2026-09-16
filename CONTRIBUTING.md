# Contributing to asStylist

Thank you for improving asStylist. This project prioritizes **safe, incremental changes** that keep the Telegram Mini App and demo mode working.

## Before you start

1. Read [AGENTS.md](./AGENTS.md) — rules apply to humans and AI agents.
2. Read [docs/architecture.md](./docs/architecture.md).
3. For behavioral or default changes, add an ADR under `docs/adr/`.

## Setup

```bash
make setup
make test
make run
```

Open http://localhost:8000

## Development workflow

1. Branch from `main`: `feature/…` or `fix/…` or `docs/…`
2. Keep PRs focused
3. Prefer engine/core changes with tests over broad refactors
4. Run `make test` and `make typecheck` before opening a PR
5. Describe risk in the PR body (`docs` / `safe-core` / `api` / `ui` / `deploy`)

## Code style

- **Python**: match existing FastAPI / pydantic style; type hints encouraged
- **TypeScript**: strict; no `any` in new code unless justified
- **Tests**: pytest (backend), vitest (frontend)
- **Commits**: conventional-ish prefixes help agents (`feat`, `fix`, `docs`, `test`, `chore`)

## What we reject

- Silent changes to ranking weights, budget guarantees, or verification critical thresholds
- Breaking `/api/*` without versioning or ADR
- Secrets in the repo
- Large drive-by refactors mixed with feature work

## Questions

Open an issue or document decisions in `docs/adr/`.
