# Agent quickstart (5 minutes)

1. Skim [CHEATSHEET.md](../CHEATSHEET.md) (1 page)
2. Read [AGENTS.md](../AGENTS.md) if you change code
3. Optional: [architecture.md](./architecture.md), [cheatsheets/](./cheatsheets/)
4. Run:

```bash
make setup
make test-engine   # or make test-backend
```

5. Pick a **safe zone** task (engine provider, docs, tests) — see [cheatsheets/tasks.md](./cheatsheets/tasks.md)
6. If changing defaults or API → write ADR first under `docs/adr/`
7. Open PR with risk label: `docs` | `safe-core` | `api` | `ui` | `deploy`

Do not start with deploy files or Telegram auth. See [cheatsheets/do-not.md](./cheatsheets/do-not.md).
