# Foundation runtime

Raicho currently provides diagnostics and persistent application initialization.
The Thunderbird container runs independently. No extension connects them yet.

See [architecture](architecture.md) for ownership,
[runtime decision](../decisions/20261018-foundation-runtime-stack.md) for choices,
[local operation](../operations/local-runtime.md) for startup and fixture checks,
and [build commands](build-test-generate.md) for source validation.

## Images and storage

`containers/raicho/Dockerfile` builds browser assets and the Rust executable in
separate stages. Its Debian runtime includes the executable, selected brand
assets, compiled web files, and an explicit HTTP health probe. Its build-context
allowlist excludes profile data, repository metadata, and unrelated artwork.

`containers/thunderbird/Dockerfile` builds directly from Debian. It installs the
official Mozilla archive, Xvfb, Openbox, DBus, and optional noVNC/websockify support.
Its supervisor starts Thunderbird without a viewer, terminates the other children
if a required child exits, and forwards shutdown. The health check verifies
processes and the internal display. A desktop HTTP response alone is insufficient.

Base images use digests, support packages use the 20261018 Debian snapshot, and
downloaded application assets use checksums. Installed OS packages are recorded
in `/opt/raicho/packages.tsv` inside each image. Runtime support is Linux amd64.

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
| `/api/status` | Application/database status, versions, and unconfigured backend |
| `/` | Static diagnostics page |

Diagnostics use `Cache-Control: no-store`. Unknown API paths and missing assets
return 404. The status response does not inspect a Thunderbird profile or claim
connector readiness. Stopping Thunderbird does not make Raicho unready.

`RAICHO_BIND` defaults to `0.0.0.0:8080` inside the container,
`RAICHO_DATA_DIR` to `/var/lib/raicho`, and `RAICHO_WEB_DIR` to
`/usr/share/raicho/web`. Compose publishes Raicho on host loopback using
`RAICHO_PORT`, default 8080. The browser page is diagnostics only and has no login.

`RAICHO_ADMIN_ENABLED=true` starts remote desktop support. Only
`compose/compose.admin.yaml` enables it and publishes loopback port `RAICHO_ADMIN_PORT`,
default 6080. This administrative interface has no application authentication.
Keep it local, close it by recreating Thunderbird without the override, and use
the Raicho page for diagnostics. Remote deployment and browser login are stage 3.

## Network isolation

Raicho and the smoke driver use the project-scoped `application` bridge network.
Thunderbird uses a separate `thunderbird` bridge network. Both use Docker's
default NAT isolation and retain internet egress, but Raicho cannot reach
Thunderbird's container IP or administrative listener. Do not join the two
services to a shared network or enable direct routing around this boundary.
Stage 2 must introduce a connector route that preserves this isolation.

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

Only SQLx migration metadata exists initially. Add versioned SQL files under
`server/migrations/` with the feature that uses them. Embedded migration changes
trigger recompilation. Do not change an applied migration, including formatting
or whitespace, because SQLx checksums its bytes. Format new migrations before
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
remain stage 7 work.
