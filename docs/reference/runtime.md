# Foundation runtime

Raicho provides diagnostics, persistent application initialization, and an
authenticated control connection to the packaged Thunderbird extension.
The connector carries no mail operations. Mail operations are planned in the
[foundation plan](../planning/active/20261017-thunderbird-first-foundation.md).

See [architecture](architecture.md) for ownership,
[runtime decision](../decisions/20261018-foundation-runtime-stack.md) for choices,
[local operation](../operations/local-runtime.md) for startup and fixture checks,
and [build commands](build-test-generate.md) for source validation.

## Images and storage

`deploy/raicho/Dockerfile` builds browser assets and the Rust executable in
separate stages. Its Debian runtime includes the executable, selected brand
assets, compiled web files, and an explicit HTTP health probe. Its build-context
allowlist excludes profile data, repository metadata, and unrelated artwork.

`deploy/thunderbird/Dockerfile` builds directly from Debian. It installs the
official Mozilla archive, Xvfb, Openbox, DBus, and optional noVNC/websockify support.
Its supervisor starts Thunderbird without a viewer, terminates the other children
if a required child exits, and forwards shutdown. The health check verifies
processes and the internal display. A desktop HTTP response alone is insufficient.
These modules live beside the image recipe in `deploy/thunderbird/` as
`runtime.py`, `supervisor.py`, `policy.py`, and `health_check.py`. The image
installs them as the `/opt/raicho/thunderbird/` package and runs
`python3 -m thunderbird.runtime` and `python3 -m thunderbird.health_check`. The
operational credential wrapper lives in `deploy/credentials/`, with its tests
under `tests/`. Its token-file and live-check services run the
`raicho-server connector files` and `connector wait` subcommands from the server
image. The
[credential runbook](../operations/connector-credentials.md) documents their use.

Base images use digests, support packages use the 20261018 Debian snapshot, and
downloaded application assets use checksums. Installed OS packages are recorded
in `/opt/raicho/packages.tsv` inside the Raicho and Thunderbird images. Runtime
support is Linux amd64.

`deploy/gateway/Dockerfile` pins Nginx 1.30.6 Alpine by digest.
Its routing configuration lives in `deploy/gateway/nginx.conf`.
The gateway runs as UID/GID 10001 with a read-only root, bounded temporary storage,
no data or secret mounts, and no published port.

| Service | Named volume | Container path |
| --- | --- | --- |
| `raicho` | `raicho-data` | `/var/lib/raicho` |
| `thunderbird` | `thunderbird-data` | `/config`, with profile at `/config/profile` |

The runtime Compose project defaults to `raicho`. Override it with `-p` or
`COMPOSE_PROJECT_NAME` for each additional deployment, along with distinct host
ports. Compose prefixes volume names with the project name. Neither service
mounts the other's data. Both run as UID/GID 10001, with read-only roots and
temporary storage in `/tmp`. New named volumes inherit the image directory ownership. SQLite and
Thunderbird profiles require local filesystems and exclusive instance ownership.

For bind mounts, prepare separate empty directories owned by UID/GID 10001 and
mode 0700, then replace the corresponding volume sources in a local override.
Do not point tests at a personal profile or share paths between deployments.
External Thunderbird mail directories require their own explicit mounts.

## HTTP and configuration

| Path | Meaning |
| --- | --- |
| `/health/live` | HTTP process responds |
| `/health/ready` | Initialization succeeded and the application database responds |
| `/api/status` | Readiness, product version, build commit, database status, and connector diagnostics |
| `/` | Static diagnostics page |

Diagnostics use `Cache-Control: no-store`. Unknown API paths and missing assets
return 404, including `/connector/v1` on this listener. Stopping Thunderbird does
not make Raicho unready. Backend status is `unconfigured`, `disconnected`,
`connected`, `revoked`, or `unavailable`. Diagnostics include the current session
generation, accepted heartbeat count, and a fixed error code, never a token or
raw socket error. The browser retains only the status and allowlisted error code
and explains that mail is not yet available.

[`protocol/schema/status.schema.json`](../../protocol/schema/status.schema.json)
is the response contract, including the 503 body that reports `unavailable` when
the application database does not respond. The server's HTTP tests validate real
responses against it, the page validates every response with a generated
validator, and the connector acceptance check reads its expected members from it.
When the database is unavailable, the page still shows the connector state. See
the [status contract decision](../decisions/20261026-protocol-contracts.md#status-api).

`version` is the declared product version. `commit` is `RAICHO_COMMIT` when the
image was built with that argument, and `unknown` otherwise. The diagnostics
page shows the version alone when the commit is unknown. See
[versioning](versioning.md).

`RAICHO_BIND` defaults to `0.0.0.0:8080` inside the container,
`RAICHO_DATA_DIR` to `/var/lib/raicho`, and `RAICHO_WEB_DIR` to
`/usr/share/raicho/web`. Compose publishes Raicho on host loopback using
`RAICHO_PORT`, default 8080. The browser page is diagnostics only and has no login.

`RAICHO_CONNECTOR_BIND` defaults to `0.0.0.0:8082` and serves only the internal
WebSocket route `/connector/v1`. Compose never publishes it. Authentication and
transport bounds are defined in the [connector contract](connector-contract.md).

`RAICHO_ADMIN_ENABLED=true` starts remote desktop support. Only
`compose.admin.yaml` enables it and publishes loopback port `RAICHO_ADMIN_PORT`,
default 6080. This administrative interface has no application authentication.
Keep it local, close it by recreating Thunderbird without the override, and use
the Raicho page for diagnostics. Remote deployment and browser login are planned
in the [foundation plan](../planning/active/20261017-thunderbird-first-foundation.md).

## Extension installation

The image builds the extension from `extension/` and installs its versioned XPI
through `ExtensionSettings`. The stable ID is `connector@raicho`. Runtime startup
generates `/tmp/raicho-runtime/policies.json` atomically with mode 0600 under a
0700 directory. The normal Thunderbird policy path is a baked symlink to it.
The policy preserves `DisableAppUpdate`, uses `force_installed`, and disables
extension background updates. Image updates own the XPI version.

Without connector configuration the extension is inactive. The credentials override
sets `RAICHO_CONNECTOR_ENDPOINT` and `RAICHO_CONNECTOR_TOKEN_FILE` together.
The runtime reads a 64-character lowercase hexadecimal token from that file and
provides endpoint/token through managed storage. Partial or invalid configuration
fails before Thunderbird starts. Neither value is baked into an image or XPI.
The [credential procedure](../operations/connector-credentials.md) provisions
the production token and SQLite keys. The credentials override mounts the
file into Thunderbird and selects `ws://gateway:8081/connector/v1`.
Managed policy is read at startup. Thunderbird does not support managed-storage
change events, so policy changes require restarting Thunderbird. The credential
wrapper force-recreates it. The connector retries every failure except an
authenticated `session_replaced`, which stops it until Thunderbird restarts, as the
[credential procedure](../operations/connector-credentials.md#a-connector-that-stops-retrying)
describes.

The production MV2 extension shares the [declared product version](versioning.md)
and uses only the `storage`
permission. Its persistent background authenticates and answers heartbeat.
No probe code enters the production XPI. The
[production connector check](build-test-generate.md#production-connector) covers
installation, managed policy, restart, and a same-profile upgrade.

## Network isolation

Raicho and the smoke driver use the project-scoped `application` bridge network.
Thunderbird uses a separate `thunderbird` bridge network. Both use Docker's
default NAT isolation and retain internet egress, but Raicho cannot reach
Thunderbird's container IP or administrative listener. Do not join the two
services to a shared network or enable direct routing around this boundary.
The gateway joins only the internal `connector-application` network, shared with
Raicho, and the internal `connector-thunderbird` network, shared with
Thunderbird. It has no egress, and Docker never forwards its DNS queries to
outside resolvers. See the
[network decision](../decisions/20261026-thunderbird-connector.md#network-isolation).
It accepts an exact WebSocket upgrade
at `/connector/v1` and forwards to `raicho:8082`. Alternate paths, queries, methods,
and arbitrary destinations are rejected. Docker DNS is re-resolved so a changed
Raicho IP requires no gateway recreation. HTTP access logs are disabled.

The administrative override publishes only on host loopback. Use Docker Engine
28 or newer, since older versions have a
[localhost publication limitation](https://docs.docker.com/engine/network/port-publishing/).
The [disposable checks](../operations/local-runtime.md#disposable-automated-checks)
verify loopback access, denial from Raicho to the actual Thunderbird IP, and
listener closure after removing the override.

## SQLite initialization and migrations

The application opens `raicho.sqlite3`, with its WAL and shared-memory files in
the same directory. SQLx uses a single connection, WAL, FULL synchronous mode,
foreign keys, and five-second busy/acquire timeouts. These waits do not establish
a general SQL execution deadline. Never hold a connection while awaiting a mail
backend. The instance lock stays held for the process lifetime.

The connector migration records backend configuration and credential state.
No mail data is stored. Add versioned SQL files under
`server/migrations/` with the feature that uses them, following the
[sequential filename convention](../coding/coding-standards.md#source-filenames).
Name their tables, columns, indexes, views, and triggers in
[snake_case](../coding/coding-standards.md#database-names).
Embedded migration changes trigger recompilation. Do not rename, renumber, or
edit an applied migration, including formatting or whitespace, because SQLx
checks its version and checksums its bytes. Format new migrations before
applying them. Missing versions,
checksum changes, failed migrations, and invalid databases prevent startup.
A failed migration rolls back itself and its bookkeeping, not previously
successful migrations in that batch. The application never resets a failed database.

Production queries live in `server/queries/` and are embedded with `include_str!`
at compile time. They need no runtime SQL file mount. SQL linting and formatting
are described in [tooling conventions](../coding/linting-and-formatting.md).

Upgrade a disposable profile/database before replacing a real installation.
Stop the server before copying the complete state directory, including journal
files, unless using a supported consistent SQLite snapshot. Stop Thunderbird
before copying its complete profile and external mail directories. Image rollback
does not reverse database or profile migrations. Automated restore procedures
are planned in the [foundation plan](../planning/active/20261017-thunderbird-first-foundation.md).
