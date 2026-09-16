# API surface cheatsheet (handle with care)

OpenAPI live docs: `http://localhost:8000/docs`

## High-traffic endpoints

| Method | Path | Role |
| --- | --- | --- |
| `POST` | `/api/looks/generate` | Main look generation (multipart or JSON) |
| `GET` | `/api/looks`, `/api/looks/{id}` | History / detail |
| `POST` | `/api/looks/{id}/swap` | Replace one slot |
| `POST` | `/api/engine/search` | Free-text engine search |
| `POST` | `/api/engine/outfit` | Engine-native outfit contract |
| `GET` | `/api/engine/health\|schema\|taxonomy` | Engine meta for agents |
| `GET` | `/api/meta` | Styles, moods, budget limits |
| `POST` | `/api/telegram/auth` | Telegram / demo identity |

## Rules

1. **Additive > breaking.** Optional new fields OK; renames need ADR.
2. Keep demo auth path working without a real bot.
3. Engine endpoints should remain usable for external agents (`TOOL_SCHEMA` via `/api/engine/schema`).
4. After API edits: `tests/test_api.py`, `tests/test_engine_api.py`, risk label `api`.

Application guarantees (budget, verification) must still hold for looks returned to the Mini App.
