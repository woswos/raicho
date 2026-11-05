# Authenticate one browser user with an offline password

- Status: accepted
- Date: 2026-11-03
- Deciders: Barkin Simsek

## Context

Stage 3 exposes account names, mailbox names, and message summaries to the
browser. One person owns each deployment and may use several browsers. The
foundation plan requires login, protected session cookies, and mutation
CSRF/origin checks before mail access, and HTTPS through a reverse proxy for
remote use. A first-run setup page would let whoever reaches the port first claim
the deployment. Host access already controls the connector credential.

## Decision

An operator sets the single login password offline. `make deploy-login-init`,
`make deploy-login-reset`, and `make deploy-login-revoke` stop the services and run
`raicho-server login` subcommands against the database, as the connector
credential commands do. The host prompts without echo and passes the password on
standard input. Passwords have 12 to 1024 bytes and no composition rules. SQLite
stores an Argon2id PHC string at OWASP's baseline or above (19 MiB, two passes,
one lane). Reset replaces the password and revokes every session. There is no
email or question-based recovery, and the browser cannot change the password yet.

A successful login creates a 256-bit random token. The cookie carries the token,
and SQLite stores only its SHA-256 digest with its creation, last use, and
expiry times. A session expires after 7 days without use or 30 days after login.
Last use is written at most every 5 minutes. At most 32 sessions exist, so a new
login removes the oldest. Logout deletes its session, and `revoke` deletes all of
them. Failed logins pass through one in-memory throttle, and one password hash runs
at a time.

`RAICHO_PUBLIC_ORIGIN` names the browser origin, and Compose defaults it to
`http://localhost:${RAICHO_PORT}`. Startup rejects an `http` origin unless its host
is loopback. With an `https` origin the cookie is `__Host-raicho_session` and
`Secure`. On loopback HTTP it is `raicho_session` without `Secure`, because
browsers differ on `Secure` and `__Host-` cookies there. Both use `HttpOnly`,
`SameSite=Strict`, and `Path=/` without a `Domain` attribute, so the cookie is
host-only. Browsers do not isolate cookies by port, so loopback deployments that
share a host name share this cookie, and any service the browser contacts on
that host receives it. Run one Raicho per host name. Every request other than GET
or HEAD must send
that exact `Origin` and `Sec-Fetch-Site: same-origin` when the browser sends the
header. Each one except a body-less logout `DELETE` must also send a JSON content
type. GET requests change no stored state except a session's last use and the
removal of expired sessions.

Raicho serves HTTP on loopback. Remote use goes through a reverse proxy that
terminates TLS and sets HSTS. `/health` and `/api/status` stay public, so the
login page can show the Thunderbird connection. Mail and preference routes require
a session.

The deployment's theme preference (`system`, `light`, or `dark`) lives in SQLite
and applies to every session.

## Consequences

Setting or resetting the password needs host access and a brief service stop.
A database copy cannot replay a session, because it holds only token digests. The
origin check and `SameSite=Strict` replace a CSRF token, and they rely on browsers
that send `Origin` with every non-GET request. A deployment reached by several
host names needs one canonical origin. Built-in TLS, password changes in the
browser, and a sign-out-everywhere button remain possible later.

Failed logins share one counter, so five failures within a minute block every
login, including one with the correct password, until the oldest failure is a
minute old. Anyone who can reach the origin can hold the owner out for a minute
at a time. That is accepted while the origin is loopback-only, and a remote
deployment needs per-source throttling at its reverse proxy.
