# Use SQLite for application state

- Status: accepted
- Date: 2026-10-18
- Deciders: Barkin Simsek

## Context

Raicho needs durable state for login, preferences, and backend connections.
The write workload is small because Thunderbird retains the mail. PostgreSQL
would add a separate database service that this workload does not need.

## Decision

Use embedded SQLite for Raicho-owned application state. Keep database access in
a focused Rust persistence module and evolve the schema through versioned
migrations. The database runs inside the server, so Compose stays at the two
services named by the
[Thunderbird-first foundation](20261017-thunderbird-first-foundation.md).

## Consequences

Application state persists without a separate database service, connection
credentials, or network dependency. Storage, schema upgrades, and backups still
need explicit handling. PostgreSQL and a second application database are not
part of this foundation. Persistence stays separate from the mail-backend
contract.
