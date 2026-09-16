# ADR 0001: Record architecture decisions

## Status

Accepted

## Context

asStylist is improved by both humans and AI agents. Without a written decision log, defaults (ranking weights, budget behaviour, engine mode, API shapes) drift and the live Mini App risks silent regressions.

## Decision

- Store short Architecture Decision Records in `docs/adr/`
- Number them sequentially: `0001-…`, `0002-…`
- Require an ADR when changing: public API contracts, ranking defaults, budget guarantees, critical verification rules, engine default mode, or deploy topology

## Consequences

- Slight overhead on meaningful changes
- Clear history for agents and reviewers
- Safer parallel work
