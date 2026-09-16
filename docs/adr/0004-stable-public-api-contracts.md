# ADR 0004: Stable public API contracts

## Status

Accepted

## Context

The Telegram Mini App and any external callers depend on `/api/*` shapes.
Silent breaking changes break the site for users even if tests of pure functions pass.

## Decision

- Treat OpenAPI (`/docs`) as the source of truth for HTTP contracts
- Breaking changes require either a new versioned path or an explicit migration plan + ADR
- Prefer additive fields over renames/removals

## Consequences

- Agents should extend, not reshape, existing endpoints
- Contract tests / careful review on `backend/app/api/**`
