# Do-not cheatsheet

| Don't | Why | Do instead |
| --- | --- | --- |
| Rewrite `/api/looks/generate` shape | Breaks Mini App | Additive fields or `/api/v2/…` + ADR |
| Change default ranking weights quietly | Looks quality drift | ADR + tests + optional config |
| Bypass budget optimiser in hybrid mode | Users can exceed budget | Keep hybrid guarantees (ADR 0002) |
| Import DB/API inside `fashion_engine` | Couples pure engine to app | Adapter in `services/` |
| Require network in unit tests | CI / offline demo fails | Fixtures, mocks, snapshots |
| Commit `.env` / tokens | Security | `.env.example` only |
| One PR: engine + UI + Docker | Hard to review / roll back | Split by concern |
| Delete critical verification checks | Bad products in looks | ADR + tests |
| “Quick” edit of `main.py` for a feature | Static serving / lifespan risk | Service or router module |

When unsure → `docs` or `safe-core` only, open a question in PR.
