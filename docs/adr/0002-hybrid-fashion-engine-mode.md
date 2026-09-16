# ADR 0002: Default hybrid Fashion Engine mode

## Status

Accepted

## Context

The ported Fashion Engine optimises taste, niche level, and outfit architecture.
The application layer optimises budget caps, sizes, seasonality, and product verification.
Users must never receive a look that exceeds budget or includes failed verification items.

## Decision

- Default `FASHION_ENGINE_MODE=hybrid`
- Engine proposes structure and taste; application ranking + budget optimiser enforce constraints
- Fallback to legacy ranker when engine cannot build a look (`FASHION_ENGINE_ALLOW_FALLBACK`)

## Consequences

- Best of both systems
- Agents must not remove budget enforcement from the default path
- Mode can be switched via config for experiments without code forks
