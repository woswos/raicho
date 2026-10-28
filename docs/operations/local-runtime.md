# Run the local foundation

Use this procedure for diagnostics or disposable development profiles. Mail
integration and remote authenticated use are not implemented. See the
[runtime reference](../reference/runtime.md) for configuration and storage.
Docker Compose 2.24 or newer is needed for the test override's reset syntax.
Use Docker Engine 28 or newer for the
[administrative network boundary](../reference/runtime.md#network-isolation).

The base `compose.yaml` and the operator overlays `compose.admin.yaml` and
`compose.credentials.yaml` live at the repository root.
Run the commands below from the repository root. Configuration may come from
shell variables. If using a repository-root `.env` file, pass `--env-file .env`
explicitly to Compose, for example:

```bash
docker compose --env-file .env config --quiet
```

## Start and inspect

From the repository root, `make deploy` prints an overview of the deployment
targets and the deployment they would act on. To start it:

```bash
make deploy-up
```

`deploy-up` builds the runtime images, then runs `docker compose up -d --wait`.
Open <http://127.0.0.1:8080>. Expect a ready application and an unconfigured
Thunderbird connector. No viewer is needed to start Thunderbird.

Use the [credential procedure](connector-credentials.md) to provision persistent
connector configuration. Its commands manage the matching Compose override and
restart sequence, then verify an authenticated heartbeat.

For explicit administration:

```bash
make deploy-admin
```

Open <http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=remote>. This is the
native Thunderbird desktop for setup and recovery. Foundation checks use empty
profiles and no provider credentials. `make deploy-up` disables the
administrative listener again, because Compose recreates Thunderbird without it.

Once a deployment has a `credentials/` directory in its state directory, the
`deploy-` targets add `compose.credentials.yaml` and set
`RAICHO_CREDENTIAL_DIRECTORY` themselves. When running Compose directly instead,
include both, because recreating Thunderbird without the credentials override
disables its connector configuration.

Inspect failures with `docker compose logs` and
`docker compose ps`. To stop while retaining both volumes:

```bash
make deploy-down
```

`make clean` removes development leftovers without stopping this deployment,
removing its images, or touching its volumes. `make mrproper` also stops and
removes this deployment's containers and every project image, but keeps its
volumes and `.raicho/`. Run `make images` before starting it again. See
[build commands](../reference/build-test-generate.md#clean).

For another deployment, choose its own project name and host ports. Exporting
`COMPOSE_PROJECT_NAME` keeps subsequent startup, inspection, and shutdown commands
on the same project. The equivalent `-p` option must be included on every command.
For example, in a separate shell:

```bash
export COMPOSE_PROJECT_NAME=raicho-second RAICHO_PORT=8081 RAICHO_ADMIN_PORT=6081
make deploy-up
```

## Upgrade

Raicho and Thunderbird images come from the same checkout and are upgraded
together, because the connector protocol version must match exactly. After
updating the checkout, rebuild and recreate both from the repository root:

```bash
make deploy-up
```

Until
both containers run the new images, a connector speaking another protocol version
fails before authentication with `incompatible_version` and keeps retrying. No
session state carries across the upgrade. See the
[version policy](../decisions/20261026-thunderbird-connector.md#versioning).

## Recovering a development database

If Raicho fails to start because a migration's checksum or version does not
match, its database applied an earlier version of a migration that has since
changed. That happens only on unreleased branches, because released migrations
are never edited. For a development deployment, remove the volume and provision
again:

```bash
make deploy-down
docker volume rm "${RAICHO_PROJECT:-${COMPOSE_PROJECT_NAME:-raicho}}_raicho-data"
make deploy-up
make deploy-connector-init
```

This deletes Raicho's application state, including the connector credential.
Thunderbird's profile volume is untouched.

## Remove a deployment

```bash
make deploy-clean
```

`deploy-clean` permanently deletes the selected deployment: its containers,
networks, both volumes, including the Thunderbird profile, and its state directory
with the connector token. It lists what it found and asks you to type the project
name. Any other answer, or no input, cancels without removing anything and exits
with an error. After removing the deployment, or finding nothing to remove, it
runs every `make clean` step. Images stay, so `make deploy-up` starts a fresh,
unconfigured deployment.

It refuses the `raicho-tools` project, a state directory that is a symlink, is
not owned by you with mode 0700, holds another deployment's state, or lacks a
`project` file naming the selected project, and a deployment whose operation
lock a credential command holds. Credential commands write that file, so run
`make deploy-connector-status` once for a state directory created before them. It takes that lock
before listing anything, creating an empty state directory to hold it when none
exists, and keeps the lock file until the volumes are gone, so a credential
command cannot claim the deployment or state inside it meanwhile. Cancelling, or
finding nothing to remove, deletes a state directory it created. It stops the
services first, then removes the state directory's contents, and only then the
volumes. If those contents cannot be removed, the volumes stay paired with them.
Fix the reported ownership and run `make deploy-clean` again.

## Disposable automated checks

The runtime check creates its own project, builds the same images as CI, and removes
only that project's resources. Test overrides publish no application host port.
Fixture seeding requires both services stopped. Fixtures add a test-only SQLite
record and Thunderbird preference, not production tables or account data.
Run it on a Linux Docker host. The administration check temporarily publishes
an ephemeral loopback port and uses containerized probes in the host network.
It restores Thunderbird without administration before returning.

```bash
make acceptance-runtime
```

Expected evidence: HTTP/asset isolation passes, SQLite contents and actual
Thunderbird preferences survive recreation, and Raicho stays ready with
Thunderbird stopped. Administration is reachable on host loopback, inaccessible
from Raicho by container IP, and closed after removing the override.
Process supervision tests and migration failure cases run
through the [application test commands](../reference/build-test-generate.md).
Visual administration verification is separate from these automated checks.
