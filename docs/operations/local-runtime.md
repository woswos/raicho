# Run the local foundation

Use this procedure for diagnostics or disposable development profiles. Mail
integration and remote authenticated use are not implemented. See the
[runtime reference](../reference/runtime.md) for configuration and storage.
Docker Compose 2.24 or newer is needed for the test override's reset syntax.

## Start and inspect

From the repository root:

```bash
docker compose -f compose.yaml config --quiet
docker compose -f compose.yaml build
docker compose -f compose.yaml up -d --wait
```

Open <http://127.0.0.1:8080>. Expect a ready application and an unconfigured
Thunderbird connector. No viewer is needed to start Thunderbird.

For explicit administration:

```bash
docker compose -f compose.yaml -f compose.admin.yaml up -d --wait
```

Open <http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=remote>. This is the
native Thunderbird desktop for setup and recovery. Foundation checks use empty
profiles and no provider credentials. To disable the administrative listener:

```bash
docker compose -f compose.yaml up -d --force-recreate thunderbird
```

Inspect failures with `docker compose -f compose.yaml logs` and
`docker compose -f compose.yaml ps`. To stop while retaining both volumes:

```bash
docker compose -f compose.yaml down
```

## Disposable automated checks

These commands create their own project, build the same images as CI, and remove
only that project's resources. Test overrides publish no application host port.
Fixture seeding requires both services stopped. Fixtures add a test-only SQLite
record and Thunderbird preference, not production tables or account data.

```bash
(
  export COMPOSE_PROJECT_NAME="raicho-check-$(date +%s)-$$"
  export COMPOSE_FILE=compose.yaml:compose.test.yaml
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
  docker compose stop thunderbird
  docker compose run --rm smoke http
)
```

Expected evidence: HTTP/asset isolation passes, SQLite contents and actual
Thunderbird preferences survive recreation, and Raicho stays ready with
Thunderbird stopped. Process supervision tests and migration failure cases run
through the [application test commands](../reference/build-test-generate.md).
Visual administration verification is separate from these automated checks.
