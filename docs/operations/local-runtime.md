# Run the local foundation

Use this procedure for diagnostics or disposable development profiles. Mail
integration and remote authenticated use are not implemented. See the
[runtime reference](../reference/runtime.md) for configuration and storage.
Docker Compose 2.24 or newer is needed for the test override's reset syntax.
Use Docker Engine 28 or newer for the
[administrative network boundary](../reference/runtime.md#network-isolation).

Compose files live in `compose/`, separate from image recipes in `containers/`.
Run the commands below from the repository root. Configuration may come from
shell variables. If using a repository-root `.env` file, pass `--env-file .env`
explicitly to Compose, for example:

```bash
docker compose --env-file .env -f compose/compose.yaml config --quiet
```

## Start and inspect

From the repository root:

```bash
docker compose -f compose/compose.yaml config --quiet
docker compose -f compose/compose.yaml build
docker compose -f compose/compose.yaml up -d --wait
```

Open <http://127.0.0.1:8080>. Expect a ready application and an unconfigured
Thunderbird connector. No viewer is needed to start Thunderbird.

Use the [credential procedure](connector-credentials.md) to provision persistent
connector configuration. Its commands manage the matching Compose override and
restart sequence, then verify an authenticated heartbeat.

For explicit administration:

```bash
docker compose -f compose/compose.yaml -f compose/compose.admin.yaml up -d --wait
```

Open <http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=remote>. This is the
native Thunderbird desktop for setup and recovery. Foundation checks use empty
profiles and no provider credentials. To disable the administrative listener:

```bash
docker compose -f compose/compose.yaml up -d --force-recreate thunderbird
```

For an enrolled deployment, include `compose/compose.credentials.yaml` in both
administration commands and set `RAICHO_CREDENTIAL_DIRECTORY` to that deployment's
absolute `credentials/` directory. Omitting the credentials override when
recreating Thunderbird disables its connector configuration.

Inspect failures with `docker compose -f compose/compose.yaml logs` and
`docker compose -f compose/compose.yaml ps`. To stop while retaining both volumes:

```bash
docker compose -f compose/compose.yaml down
```

For another deployment, choose its own project name and host ports. Exporting
`COMPOSE_PROJECT_NAME` keeps subsequent startup, inspection, and shutdown commands
on the same project. The equivalent `-p` option must be included on every command.
For example, in a separate shell:

```bash
export COMPOSE_PROJECT_NAME=raicho-second RAICHO_PORT=8081 RAICHO_ADMIN_PORT=6081
docker compose -f compose/compose.yaml up -d --wait
```

## Disposable automated checks

These commands create their own project, build the same images as CI, and remove
only that project's resources. Test overrides publish no application host port.
Fixture seeding requires both services stopped. Fixtures add a test-only SQLite
record and Thunderbird preference, not production tables or account data.
Run them on a Linux Docker host. The administration check temporarily publishes
an ephemeral loopback port and uses containerized probes in the host network.
It restores Thunderbird without administration before returning.

```bash
(
  export COMPOSE_PROJECT_NAME="raicho-check-$(date +%s)-$$"
  export COMPOSE_FILE=compose/compose.yaml:compose/compose.runtime_test.yaml
  set -eu
  trap 'docker compose down --volumes --remove-orphans' EXIT
  docker compose --profile test build
  docker compose up -d --wait --wait-timeout 120 raicho thunderbird
  docker compose run --rm smoke http
  docker compose stop raicho thunderbird
  docker compose run --rm smoke seed
  docker compose up -d --force-recreate --wait --wait-timeout 120 raicho thunderbird
  docker compose run --rm smoke http
  docker compose run --rm smoke persistence
  bash devbin/raicho_check_admin_isolation.bash
  docker compose stop thunderbird
  docker compose run --rm smoke http
)
```

Expected evidence: HTTP/asset isolation passes, SQLite contents and actual
Thunderbird preferences survive recreation, and Raicho stays ready with
Thunderbird stopped. Administration is reachable on host loopback, inaccessible
from Raicho by container IP, and closed after removing the override.
Process supervision tests and migration failure cases run
through the [application test commands](../reference/build-test-generate.md).
Visual administration verification is separate from these automated checks.
