# Browser login

One password protects a deployment's browser client. The operator sets it from
the host, and the browser exchanges it for a session cookie. The
[authentication decision](../decisions/20261103-browser-authentication.md) records
the choices, and the [runtime reference](../reference/runtime.md#http-and-configuration)
lists the routes.

## Set the password

Run from the repository root on the deployment's host:

```bash
make deploy-login-init
```

The command builds the runtime images and asks for the password twice without
echoing it. A password has 12 to 1024 bytes. Without a terminal, it reads one line
from standard input instead. The password reaches the one-off `login` service from
`compose.login.yaml` on standard input, never in an argument or the environment.
SQLite keeps only its Argon2id hash.

Each `make deploy-login-<command>` target runs
`bash deploy/credentials/login.bash <command>`:

| Command | Effect |
| --- | --- |
| `init` | Sets the first password. It fails when one exists |
| `reset` | Replaces the password and ends every browser session |
| `revoke` | Ends every browser session and keeps the password |
| `status` | Prints whether a password exists and how many sessions remain |

The wrapper selects the deployment as the
[credential commands](connector-credentials.md#setup-and-commands) do, and holds
the same state directory lock. Raicho holds SQLite's instance lock, so the wrapper
stops it for the command. It restarts Raicho only when Raicho was running before.
The restart recreates Raicho from the current environment and the rebuilt image,
so set `RAICHO_PORT` and `RAICHO_PUBLIC_ORIGIN` as for `make deploy-up`.

## Sign in and sessions

Open the deployment's origin, by default <http://localhost:8080>, and enter the
password. A successful login sets an `HttpOnly`, `SameSite=Strict` cookie that
lasts 30 days. A session also ends after 7 days without use, at logout, or after
`reset` or `revoke`. Each browser keeps its own session, and at most 32 exist at
once, so a new login ends the oldest. Five failed logins within a minute block
further attempts until the oldest failure is a minute old.

There is no email or question-based recovery. A forgotten password is replaced
with `make deploy-login-reset` on the host.

## Origin and HTTPS

`RAICHO_PUBLIC_ORIGIN` is the exact address that browsers use, such as
`https://mail.example.org`. Compose defaults it to
`http://localhost:${RAICHO_PORT}`. A login, logout, or preference change from any
other origin fails with `forbidden_origin`, so open the deployment by that address,
not by `127.0.0.1`. Plain `http` origins are accepted only for `localhost`,
`127.0.0.1`, and `[::1]`, and startup fails for any other.

Raicho itself serves plain HTTP on host loopback. For use from another computer,
put a reverse proxy in front of it that terminates TLS, sets HSTS, and forwards to
the loopback port. A minimal Caddy configuration for `https://mail.example.org`:

```text
mail.example.org {
    header Strict-Transport-Security "max-age=31536000"
    reverse_proxy 127.0.0.1:8080
}
```

Then recreate Raicho with the matching origin:

```bash
RAICHO_PUBLIC_ORIGIN=https://mail.example.org make deploy-up
```

Set the same origin for the login and connector commands, because they recreate
Raicho too.

With an `https` origin the cookie is named `__Host-raicho_session` and carries
`Secure`. Raicho does not read forwarded headers, and the proxy must keep the
browser's `Origin` header unchanged. Stage 7 of the
[foundation plan](../planning/active/20261017-thunderbird-first-foundation.md)
verifies remote HTTPS operation end to end.

## Troubleshooting

| Response | Cause and fix |
| --- | --- |
| `login_unconfigured` | No password exists. Run `make deploy-login-init` |
| `forbidden_origin` | The page's address differs from `RAICHO_PUBLIC_ORIGIN`. Open the configured address, or recreate Raicho with the right origin |
| `rate_limited` | Too many failed logins. Wait for the time in `Retry-After` |
| `unauthenticated` | The session expired, was revoked, or belongs to another origin. Sign in again |
