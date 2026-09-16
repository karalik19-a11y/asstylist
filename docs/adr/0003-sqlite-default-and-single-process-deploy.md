# ADR 0003: SQLite default and single-process deploy

## Status

Accepted

## Context

The product is non-commercial (0 ₽ stack). Operational simplicity matters more than multi-node scaling for now.

## Decision

- Default database: SQLite via SQLAlchemy
- `DATABASE_URL` may point to Postgres later without rewriting domain logic
- One process serves API + built static Mini App (Dockerfile / render.yaml)

## Consequences

- Zero-cost local and small production deploys
- Agents must not assume distributed transactions or multiple API replicas
- Changing deploy topology requires human review and a new ADR
