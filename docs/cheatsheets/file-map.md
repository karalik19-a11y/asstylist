# File map cheatsheet

```
backend/app/
├── fashion_engine/          # SAFE — pure discovery + outfit IQ
│   ├── engine.py            # FashionEngine orchestrator, create_outfit
│   ├── pipeline.py          # PIPELINE_STEPS (agent extension map)
│   ├── types.py             # ProductItem, UserStyleProfile, OutfitResult
│   ├── keywords.py / lexicon.py
│   ├── search/
│   │   ├── query_expander.py
│   │   ├── multi_pass_search.py
│   │   ├── provider.py      # SearchProvider interface
│   │   └── providers/       # catalog, mock, avito, web…
│   ├── intelligence/        # taste, trends, attributes
│   ├── outfit/              # architect, scorer, critic
│   └── validation/          # item, image, identity
├── engine/                  # SAFE-ish — app ranking, budget, body, colors
│   ├── ranking.py
│   ├── budget.py
│   ├── look_builder.py
│   └── …
├── verification/            # SAFE-ish — product checks
├── services/                # adapters (catalog → engine cards)
├── api/                     # DANGEROUS — public HTTP
├── main.py                  # DANGEROUS — wiring + static
└── config.py                # flags / env (careful with defaults)

frontend/src/                # DANGEROUS for drive-by changes
docs/adr/                    # decisions when defaults/contracts change
```

**Import direction**

- `fashion_engine` → only itself (+ stdlib)
- `services` / `api` → may import `fashion_engine`
- never the reverse
