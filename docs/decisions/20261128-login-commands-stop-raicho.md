# Stop only Raicho for login commands

- Status: accepted
- Date: 2026-11-28
- Deciders: Barkin Simsek

## Context

The [browser authentication decision](20261103-browser-authentication.md) says
`make deploy-login-init`, `make deploy-login-reset`, and `make deploy-login-revoke`
stop the services before they run `raicho-server login`. The command needs only
the Raicho database, whose SQLite instance lock the running server holds.
Thunderbird and the gateway do not touch it.

## Decision

The login commands stop only the Raicho service, run the subcommand, and restart
Raicho only when it was running before. Thunderbird and the gateway keep running.

## Consequences

Thunderbird keeps its connection to the providers while the password changes. The
connector reconnects once Raicho restarts. The rest of the browser authentication
decision is unchanged.
