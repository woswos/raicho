# Adopt a Thunderbird-first application foundation

- Status: accepted
- Date: 2026-10-17
- Deciders: Barkin Simsek

## Context

Raicho needs everyday mail access from other computers through a browser while
reusing Thunderbird's accounts, local mail, and filters. Operation is
containerized, and the backend boundary must allow alternatives while
Thunderbird remains the initial backend.

## Decision

Use Rust for the application server and TypeScript for the browser client and
Thunderbird extension. Run Raicho and Thunderbird as separate Docker Compose
services with persistent storage, and containerize their runtime and builds.

Serve one person per deployment. Multiple users run independent instances.
Keep Thunderbird as the primary backend behind a Raicho-owned mail contract
and a versioned, language-neutral connector boundary.

Thunderbird owns mail storage, drafts, account connections, search indexes,
and filters. Raicho keeps its operational state without a duplicate mail store
or rule engine.

## Consequences

Mail operations depend on Thunderbird being available. The browser client can
evolve independently of Thunderbird-specific APIs. Independent retention, an
offline Raicho mailbox, shared tenancy, and a replicated filter engine are
outside this foundation. Frontend framework and application image choices
remain open in the
[foundation plan](../planning/active/20261017-thunderbird-first-foundation.md).
