# Connector credentials

Use these commands to enroll, rotate, verify, or revoke the local Thunderbird
connector credential. They operate on the selected deployment's SQLite database
while both core services are stopped. See the [runtime reference](../reference/runtime.md)
for storage and [connector contract](../reference/connector-contract.md) for transport.

## Setup and commands

Run from the repository root on a Linux Docker host with Bash and `flock`.
Each `make deploy-connector-<command>` target builds the runtime images, then runs
`bash deploy/credentials/connector.bash <command>`:

```bash
make deploy-connector-init
```

The project is selected by `RAICHO_PROJECT`, then `COMPOSE_PROJECT_NAME`, then
`raicho`. Use the existing Compose project name for another deployment.
`RAICHO_STATE_DIRECTORY` defaults to
`.raicho/<project>` beneath the checkout and must be an absolute path when
overridden. It must belong to the invoking host user with mode 0700 and must not
sit inside another deployment's state directory. Keep that
directory and the named database volume paired. Neither `make clean` nor
`make mrproper` removes either of them, and `make deploy-clean` removes both. Set
`RAICHO_PORT` when the selected deployment needs a different loopback port.

```bash
make deploy-connector-rotate
make deploy-connector-verify
make deploy-connector-status
make deploy-connector-revoke
make deploy-connector-reactivate
```

Every command stops Raicho and Thunderbird. Successful `init`, `rotate`,
`reactivate`, and `verify` recreate both services and the gateway, wait for
their health checks, and require an authenticated heartbeat within 90 seconds.
`status` and
`revoke` leave them stopped. Failures also leave services stopped unless service
recreation itself has already begun. Fix the reported failure before restarting.
The helper holds a deployment operation lock for the entire sequence. SQLite's
instance lock independently rejects provisioning while another process owns it.
Before taking that lock, the helper and `make deploy-clean` check for overlapping
state directories under one per-user lock in `${TMPDIR:-/tmp}/raicho-state-<uid>/`,
so run them with the same `TMPDIR`. A command that finds this lock taken fails and
can be run again.

`compose.credentials.yaml` adds offline provisioning services and mounts
the token read-only into Thunderbird. It configures the fixed internal gateway
endpoint. Verification checks the SQLite keys, file permissions, UID 10001
access, service health, and the live authenticated connection. The diagnostics
page should report `Connected`. This confirms the control connection, not mail
availability. A failed connection check retains recovery files.

The operational wrapper lives in `deploy/credentials/`. Token-file management
and the live connection check are the `raicho-server connector files` and
`raicho-server connector wait` subcommands, so every credential service runs
from the production server image. The disposable acceptance runner is
under `automation/acceptance/credentials/`, as described in
[project structure](../reference/project-structure.md#automation).

## Token ownership

The isolated `connector files` command generates 32 random bytes, encoded as 64
lowercase hexadecimal characters. It never prints the token. The token directory is owned by UID/GID
10001 with mode 0700, and token files use mode 0600. Existing insecure files are
rejected. The one-off file service runs as root with only the filesystem
capabilities needed to prepare those permissions on its narrow bind mount.
The database provisioner and both core services run as UID/GID 10001.

The host files live in the ignored state directory. SQLite stores the two keys derived
from the token and backend/revocation metadata only. Ordinary Raicho mounts no token
file and never imports or re-enrolls credentials at startup. Credentials do not
enter environment variables, command arguments, images, XPIs, or logs. Protect
the host token and database backups as sensitive configuration.

## Rotation and interrupted operations

The files below describe the recoverable transaction. Each file creation,
rename, and removal is synchronized to disk. Only one credential is valid in SQLite.

| Files under `credentials/` | Meaning and action |
| --- | --- |
| No files | Run `init` to prepare the first credential |
| `connector.token` only | Stable configuration, `rotate` prepares a new token |
| `connector.pending`, optionally `connector.token` | Run the same `init` or `rotate` command to resume the database update and publication |
| `connector.pending` and `connector.previous`, no current token | Interrupted publication, rerun `rotate` to restore the old filename and resume |
| `connector.token` and `connector.previous` | New token is published, rerun `rotate` to verify it and recreate services before discarding the previous file |

Rotation prepares `connector.pending`, commits its keys in SQLite, renames
the old token to `connector.previous`, and publishes the pending token. It then
verifies the new file against SQLite and force-recreates services so a file bind
mount cannot retain an old inode. Thunderbird reloads managed policy only at
startup. Only after a verified authenticated heartbeat is the previous
file removed. Retaining that file supports diagnosis and recovery, but does not
keep its credential valid after the database commit.

If a command was interrupted, rerun that same command. Do not delete pending
files or generate another token to bypass a mismatch. A missing file, unexpected
file, wrong owner/mode, revoked record, or mismatch fails closed. Stop both
services before investigating. Preserve the state directory and complete SQLite
directory, including any journal files, before repairs. Restore a known matched
backup only as a deliberate administrative recovery, accounting for any
revocation that occurred after that backup.

An interruption while generating randomness can leave `.connector.preparing`.
The wrapper never submits this staging filename to SQLite. The next command
deletes it when it is a regular file without links, then continues. A link or
other file type under that name fails closed for manual investigation.

Revocation needs no token file and persists across startup. Replaying enrollment
or an interrupted rotation cannot reactivate a revoked record. Automatic
re-enrollment is deliberately unavailable. To deliberately enroll a replacement
after revocation, run `reactivate`. It requires a different credential, and can
recover even when the previous token file is missing. After the database commit,
repeating an interrupted `reactivate` resumes the same replacement. It does not
authorize reusing the revoked token or changing an already active, different
credential.

When the database is revoked, reactivation first renames the entire old token
directory to `revoked.<random>` alongside it in the private deployment state
directory, synchronizes that rename, then generates a fresh token.
This also recovers revocation during an interrupted rotation. If the database
already accepted the replacement, retry uses the existing candidate. The archived
configuration remains for operator inspection and later explicit cleanup. Do not
restore its token as an active credential.

## A connector that stops retrying

The extension retries every failure with capped backoff, including rejected
credentials, closes, and frames it cannot authenticate. It stops only when the
server sends an authenticated `session_replaced` error, which means another
connector with the same token connected after it. The stopped connector stays idle
until Thunderbird restarts, so two connectors never compete for the session, and
the diagnostics page reports the newer connection. Stop the other Thunderbird
instance, then restart this one with the credentials override:

```bash
docker compose -f compose.yaml -f compose.credentials.yaml restart thunderbird
```

Set `RAICHO_CREDENTIAL_DIRECTORY` to the deployment's `credentials/` directory
first, as for administration.

## Validation

```bash
make acceptance-credentials
```

The runner owns a uniquely named disposable Compose project and temporary host
state. It exercises enrollment, rotation interruptions, mismatch and permission
failures, lock contention, restart, revocation, and token isolation. It does not
use an existing deployment, personal profile, or provider credentials.
