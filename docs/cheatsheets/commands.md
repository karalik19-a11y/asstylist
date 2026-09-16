# Commands cheatsheet

```bash
# Install
make setup

# Safe-zone gate (engine / ranking / budget / verification / boundary)
make test-engine
make agent-check          # test-engine + frontend typecheck

# Full gate before merge
make test                 # backend + frontend
make typecheck

# Run app (API + built Mini App)
make run                  # http://localhost:8000
make dev                  # backend reload only; FE often on :5173

# Catalog / optional network jobs
make seed                 # re-seed demo catalog
make refresh-avito        # needs network to avito.ru

# Help
make help
```

## Pytest tips (from `backend/`)

```bash
cd backend
../.venv/bin/python -m pytest -q tests/test_fashion_engine.py
../.venv/bin/python -m pytest -q tests/test_fashion_engine_boundary.py
../.venv/bin/python -m pytest -q -k "taste or architect or expander"
```

Unit tests must pass **offline** (no bot token, no paid keys).
