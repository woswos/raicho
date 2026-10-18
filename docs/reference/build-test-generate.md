# Build, test, and generate

The static showcase has no build step or code generation. Its preview and export
procedure is maintained in the [showcase guide](../../assets/brand/showcase/README.md).

## Tooling image

Run from the repository root with Docker and Compose installed. Git is needed
to clone the repository and prepare local PR comparisons. The image supplies
Bash, Python, Make, Node, Rust, and the selected quality tools. Host language
toolchains are not required. Build after changing the image or dependency pins:

```bash
docker compose -f compose/compose.tools.yaml build
```

The entrypoint also compares `package.json`, `package-lock.json`,
`eslint.config.mjs`, and `containers/tooling/requirements.txt` with the image
copies. A mismatch stops the command with a
rebuild instruction, preventing stale installed dependencies or lint rules.

The `check` service mounts the repository read-only. Tool caches and temporary
outputs live outside that mount. It does not mount the Docker socket or start
application services. Make runs checks inside the container without launching
nested containers.

The default mount supports ordinary checkouts. A linked Git worktree also needs
its shared Git metadata mounted read-only at the same absolute host path. Without
that mount, checks fail because Git cannot resolve the worktree metadata:

```bash
RAICHO_GIT_COMMON_DIR="$(git rev-parse --path-format=absolute --git-common-dir)"
docker compose -f compose/compose.tools.yaml run --rm \
  --volume "${RAICHO_GIT_COMMON_DIR}:${RAICHO_GIT_COMMON_DIR}:ro" \
  check make lint format-check typecheck
```

Add the same volume option to formatting and PR checks when using a linked
worktree. The source mount remains read-only for checks.

## Checks and formatting

```bash
docker compose -f compose/compose.tools.yaml run --rm check make lint format-check typecheck
docker compose -f compose/compose.tools.yaml run --rm check make test-tooling
```

| Target | Behavior |
| --- | --- |
| `lint` | Repository integrity, guard tests, language linters, and protocol generation drift |
| `lint-repo` | Agent, documentation, source filename, and skill guards with regression tests |
| `format-check` | Check selected source and configuration formatting without edits |
| `typecheck` | TypeScript compiler with no emitted output |
| `test-tooling` | Disposable passing/failing Rust, TypeScript, and SQL fixtures exercising the runners |
| `lint-pr` | PR metadata and design/decision policy guard |
| `format` | Rewrite files in the documented formatting scope |
| `lint-sql` | Check owned SQLite source for syntax and configured lint rules |
| `format-check-sql` | Compare formatted temporary copies with SQL sources without editing them |
| `format-sql` | Rewrite owned SQL sources using formatting rules only |

The `devbin/raicho_check_*.py` guards are direct Python entry points. Their
optional repository-root argument defaults to the repository containing the
script. Explicit roots are normalized to absolute paths from the caller's
working directory. PR guards resolve a relative `GITHUB_EVENT_PATH` against
that repository root. The Docker/Make commands above remain the normal interface.

Rust compilation is checked by Clippy under `lint`. While Rust or TypeScript
sources are absent, their runners explicitly report not applicable. Once owned
sources appear, missing tools, manifests, or TypeScript configuration fail.
Add the application configuration with its first source files. Fixtures in
`test-tooling` prove runner behavior, not application correctness.

Formatting requires the writable `format` service. Set the caller's UID/GID
explicitly so rewritten files retain the caller's ownership:

```bash
LOCAL_UID="$(id -u)" LOCAL_GID="$(id -g)" \
docker compose -f compose/compose.tools.yaml run --rm format make format
```

For SQL alone, use `check make lint-sql format-check-sql` or
`format make format-sql` with the same Compose command and ownership settings.
SQL checks need no database connection. Applied migration files must retain
their original bytes, as explained in the [runtime reference](runtime.md#sqlite-initialization-and-migrations).

The exact scope and pins are in
[linting and formatting](../coding/linting-and-formatting.md). CI never runs
automatic fixes. Repository integrity checks retain standing approval during
implementation under [workflow](../contributing/workflow.md). A plain commit
request does not authorize checks, formatting, or hooks.

## Pull request checks

The `lint-pr` target runs the PR policy guard. GitHub supplies `GITHUB_EVENT_PATH`.
For local use, provide `PR_BASE_SHA` and `PR_HEAD_SHA` as full commit hashes,
`PR_DESCRIPTION` as text, and `PR_LABELS` as a comma-separated list of label names.
The base and head commits must already exist locally. References are checked in
those commits, so a new uncommitted ADR cannot satisfy a check against `HEAD`.
No network fetch occurs. This example uses an existing committed decision:

```bash
PR_BASE_SHA="$(git rev-parse origin/main)" \
PR_HEAD_SHA="$(git rev-parse HEAD)" \
PR_DESCRIPTION="Decision: docs/decisions/20261005-adopt-shared-workflow.md" \
PR_LABELS="" \
docker compose -f compose/compose.tools.yaml run --rm check make lint-pr
```

Without a local base, the guard conservatively requires a design or decision.
A `design` label needs both commits to prove that only planning docs changed.
GitHub event metadata always takes precedence over local overrides.

CI adds `compose/compose.ci.yaml` to bind-mount the event JSON read-only at
`/tmp/github-event.json`. This override requires `GITHUB_EVENT_PATH` to be an
absolute path to an existing host file. The checkout supplies the base/head Git
objects:

```bash
docker compose -f compose/compose.tools.yaml -f compose/compose.ci.yaml run --rm check make lint-pr
```

## Application tooling

Run source builds and behavioral tests through the same tooling container:

```bash
docker compose -f compose/compose.tools.yaml run --rm check make build-app test-app
docker compose -f compose/compose.tools.yaml run --rm check \
  python3 -B -m unittest discover -s containers/thunderbird -p '*_tests.py'
```

`build-app` combines `build-server`, `build-web`, and `build-extension`. `test-app`
combines `test-server`, `test-web`, and `test-extension`.
Rust uses `--workspace --all-targets --locked` and
temporary Cargo output. The browser build uses `tsc`, copies public files and
the selected identity assets, then runs Node's built-in tests against compiled
modules. All temporary build output stays outside the source mount.

Build runtime images with `docker compose -f compose/compose.yaml build`. This
compiles release artifacts and installs the independently packaged Thunderbird runtime.
The image recipes pin base digests and downloaded artifacts. The Thunderbird
image also builds the XPI with TypeScript and the deterministic Python packager.
See [local runtime](../operations/local-runtime.md) for Compose
startup, administration, persistence checks, and cleanup.

`compose/compose.tools.yaml` remains a development-only configuration and does
not start the application. Application state belongs to the runtime volumes, not the
checkout. Control-contract generation is described below. Mail commands remain
outside the production contract.

## Connector contract

```bash
docker compose -f compose/compose.tools.yaml run --rm format make generate-protocol
docker compose -f compose/compose.tools.yaml run --rm check make check-protocol test-protocol
```

Use the caller's UID/GID for writable generation as above. `generate-protocol`
builds both generators into temporary output, then updates committed bindings,
limits, and the standalone validator. `check-protocol` compares fresh output
without editing sources and runs under `lint` in CI. `test-protocol` runs the
Rust contract/generator and compiled production extension tests. The same tests
also run through `test-app`. See the [contract reference](connector-contract.md)
for sources, parsing rules, and integration responsibilities.

## Credential persistence

```bash
docker compose -f compose/compose.tools.yaml run --rm check \
  make test-server lint-repo lint-sql format-check-sql
bash devbin/raicho_check_credentials.bash
```

The source checks cover credential state transitions and host-file recovery.
The host runner owns a disposable Docker deployment and checks the actual
provisioning, rotation, revocation, restart, file permissions, and mount boundary.
The [credential runbook](../operations/connector-credentials.md) documents the
operator commands and recovery states. Production connector authentication is
tested with the later transport integration.

## Extension lifecycle

Run the focused source checks through the tooling image:

```bash
docker compose -f compose/compose.tools.yaml run --rm check \
  make build-extension test-extension typecheck
docker compose -f compose/compose.tools.yaml run --rm check \
  python3 -B -m unittest discover -s containers/thunderbird -p '*_tests.py'
bash devbin/raicho_check_extension_lifecycle.bash
```

The host Bash runner orchestrates Docker only. It creates a unique
`raicho-lifecycle-...` project, builds extension versions 0.1.0 and 0.1.1 into
separate temporary Thunderbird images, and uses an internal network and fresh
profile/credential volumes. It verifies installation without a viewer, managed
configuration, a 90-second idle session, restart, and image upgrade preserving
the profile. `RAICHO_EXTENSION_IDLE_SECONDS` accepts 60 through 3600 seconds.
The runner removes its own containers, volumes, and image tags on exit. It never
uses the default deployment or a personal profile.

The packager stores sorted archive entries with fixed timestamps and modes.
Its reproducibility and version tests run under `lint-repo`. `build-extension`
uses disposable output. To export an XPI, mount an empty output directory into
the tooling container and run `python3 -B devbin/raicho_build_extension.py
--output /output/raicho.xpi`; `--version` selects the version for an upgrade test.
No test modules or credentials enter the archive.

The lifecycle fixture unit tests use the Thunderbird image because its pinned
websockify package provides the WebSocket server. The lifecycle runner runs those
tests before starting the fixture. Full connector acceptance and its CI runtime
job belong to the later integration slice.

Authorization follows [workflow](../contributing/workflow.md). CI behavior is
documented in [CI](ci-cd.md), and runtime details in [runtime](runtime.md).

## Mail API compatibility

```bash
docker compose -f compose/compose.tools.yaml run --rm check make test-mail-probe
bash devbin/raicho_check_mail_compatibility.bash
bash devbin/raicho_check_mail_compatibility.bash --native
```

The separate `test-mail-probe` target compiles and tests the fixture extension.
It does not change `build-app` or the production XPI. The host runner builds
temporary Docker images, runs fixture unit tests, and starts a fresh isolated
mail deployment. It cleans up its own images, containers, networks, and volumes.
The default run covers drafts and restart. `--native` also requires a browser
on the Linux Docker host for the sending permission and native draft checkpoints.
Sending and native checks are explicitly skipped in unattended mode. Full CI
acceptance remains a later slice. The
[compatibility matrix](mail-api-compatibility.md) records limits and results.
