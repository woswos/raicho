# Build, test, and generate

The static showcase has no build step or code generation. Its preview and export
procedure is maintained in the [showcase guide](../../assets/brand/showcase/README.md).

## Tooling image

Run from the repository root with Docker and Compose installed. Git is needed
to clone the repository and prepare local PR comparisons. The image supplies
Bash, Python, Make, Node, Rust, the selected quality and coverage tools, and
Python test fixtures. Host language toolchains are not required. Rebuild after changing
the image, dependency pins, or packaged fixture sources:

```bash
docker compose -f automation/tooling/compose.yaml build
```

The image's build-context allowlist is
`automation/tooling/Dockerfile.dockerignore`. Fixture sources come from the
component-local directories listed in [project structure](project-structure.md#test-code).
The tooling entrypoint lives at `automation/tooling/entrypoint.bash`.

The entrypoint also compares `package.json`, `package-lock.json`,
`eslint.config.mjs`, and `automation/tooling/requirements.txt` with the image
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
docker compose -f automation/tooling/compose.yaml run --rm \
  --volume "${RAICHO_GIT_COMMON_DIR}:${RAICHO_GIT_COMMON_DIR}:ro" \
  check make lint format-check typecheck
```

Add the same volume option to formatting and PR checks when using a linked
worktree. The source mount remains read-only for checks.

## Checks and formatting

```bash
docker compose -f automation/tooling/compose.yaml run --rm check make lint format-check typecheck test-python
docker compose -f automation/tooling/compose.yaml run --rm check make test-tooling
```

| Target | Behavior |
| --- | --- |
| `lint` | Repository integrity, language linters, and protocol generation drift |
| `lint-repo` | Repository guards, including file, directory, and database naming |
| `test-python` | Every Python unit suite, discovered as `*_tests.py` from the repository root |
| `format-check` | Check selected source and configuration formatting without edits |
| `typecheck` | TypeScript compiler with no emitted output |
| `test-tooling` | Disposable passing/failing Rust, TypeScript, and SQL fixtures exercising the runners |
| `lint-pr` | PR metadata, design/decision policy, and changelog guard |
| `format` | Rewrite files in the documented formatting scope |
| `lint-sql` | Check owned SQLite source for syntax and configured lint rules |
| `format-check-sql` | Compare formatted temporary copies with SQL sources without editing them |
| `format-sql` | Rewrite owned SQL sources using formatting rules only |

The guards in `automation/repository/` are Python module entry points. Their
optional repository-root argument defaults to the repository containing the
script. Explicit roots are normalized to absolute paths from the caller's
working directory. PR guards resolve a relative `GITHUB_EVENT_PATH` against
that repository root. The Docker/Make commands above remain the normal interface.
See [automation placement](project-structure.md#automation) for the module layout
and invocation convention.

`test-python` runs one `unittest` discovery of `*_tests.py` from the repository
root. Discovery enters only Python packages, so every directory on a test's
import path needs an `__init__.py`. The suites cover repository policy including
changelog guards, quality discovery, extension and mail probe packaging, mail
probe fixtures, releases, the operational credential wrapper, the Thunderbird
runtime, protocol generation, and acceptance-driver support.

Rust compilation is checked by Clippy under `lint`. While Rust or TypeScript
sources are absent, their runners explicitly report not applicable. Once owned
sources appear, missing tools, manifests, or TypeScript configuration fail.
Add the application configuration with its first source files. Fixtures in
`test-tooling` prove runner behavior, not application correctness.

Formatting requires the writable `format` service. Set the caller's UID/GID
explicitly so rewritten files retain the caller's ownership:

```bash
LOCAL_UID="$(id -u)" LOCAL_GID="$(id -g)" \
docker compose -f automation/tooling/compose.yaml run --rm format make format
```

For SQL alone, use `check make lint-sql format-check-sql` or
`format make format-sql` with the same Compose command and ownership settings.
SQL checks need no database connection. Applied migration files must retain
their original bytes, as explained in the [runtime reference](runtime.md#sqlite-initialization-and-migrations).

A new or changed Rust dependency also changes `Cargo.lock`. The `check` service
mounts the checkout read-only and builds use `--locked`, so refresh the lockfile
through the writable service first:

```bash
LOCAL_UID="$(id -u)" LOCAL_GID="$(id -g)" \
docker compose -f automation/tooling/compose.yaml run --rm format cargo metadata --format-version 1
```

The exact scope and pins are in
[linting and formatting](../coding/linting-and-formatting.md). CI never runs
automatic fixes. Repository integrity checks, `lint-repo` and `test-python`,
retain standing approval during implementation under
[workflow](../contributing/workflow.md). A plain commit
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
docker compose -f automation/tooling/compose.yaml run --rm check make lint-pr
```

Without a local base, the guard conservatively requires a design or decision.
A `design` label needs both commits to prove that only planning docs changed.
GitHub event metadata always takes precedence over local overrides.

CI adds `automation/tooling/compose.ci.yaml` to bind-mount the event JSON read-only at
`/tmp/github-event.json`. This override requires `GITHUB_EVENT_PATH` to be an
absolute path to an existing host file. The checkout supplies the base/head Git
objects:

```bash
docker compose -f automation/tooling/compose.yaml -f automation/tooling/compose.ci.yaml run --rm check make lint-pr
```

## Application tooling

Run source builds and behavioral tests through the same tooling container:

```bash
docker compose -f automation/tooling/compose.yaml run --rm check make build-app test-app test-protocol
```

`build-app` combines `build-server`, `build-web`, and `build-extension`. `test-app`
combines `test-server`, `test-web`, and `test-extension`.
Rust uses `--workspace --all-targets --locked` and
temporary Cargo output. The browser build uses `tsc`, copies public files and
the selected identity assets, then runs Node's built-in tests against compiled
modules. The web builder is `web/build.mjs`, and extension packaging
uses `extension/build.mjs`. Both run on Node alone. The shared dispatcher remains in
`automation/build/application.py`. All temporary build output stays
outside the source mount.

Tooling defaults to no Rust debug symbols or incremental output, keeping the
complete workspace build within the temporary filesystem on CI runners. These
settings affect check containers, not release images. Set
`CARGO_PROFILE_DEV_DEBUG=2`, `CARGO_PROFILE_TEST_DEBUG=2`, or `CARGO_INCREMENTAL=1`
before the Compose command when that output is needed for local debugging.

Build runtime images with `docker compose build`. This
compiles release artifacts and installs the independently packaged Thunderbird runtime.
The image recipes pin base digests and downloaded artifacts. The Thunderbird
image also builds the XPI with TypeScript and the deterministic Node packager.
See [local runtime](../operations/local-runtime.md) for Compose
startup, administration, persistence checks, and cleanup.

`automation/tooling/compose.yaml` remains a development-only configuration and does
not start the application. Application state belongs to the runtime volumes, not the
checkout. Control-contract generation is described below. Mail commands remain
outside the production contract.

## Coverage

```bash
docker compose -f automation/tooling/compose.yaml run --rm check make coverage
```

`coverage` runs the Rust workspace tests, the protocol, web, and extension
TypeScript suites, and the `test-python` and `test-tooling` suites with coverage
instrumentation. It prints line coverage for each measured source file. Rust builds
with `-C instrument-coverage` into its own temporary target directory, and the
image's LLVM tools merge and export the profiles. TypeScript test builds emit source
maps, so Node's built-in coverage reports lines of the `.ts` sources. The XPI never
contains source maps. coverage.py measures Python, including subprocesses and the
guard copies that tests run from temporary repositories. The lcov reports stay in
`/tmp/raicho-coverage` inside the container.

Tests, generated files, dependencies, the acceptance drivers in
`automation/acceptance/`, and the `mailprobe/` test artifact are not measured. A
source that no test loads, such as a browser entry point, is absent from the
reports rather than reported as uncovered. The
[patch coverage decision](../decisions/20261026-repository-layout.md#patch-coverage) records the
tool choices.

## Connector contract

```bash
LOCAL_UID="$(id -u)" LOCAL_GID="$(id -g)" \
  docker compose -f automation/tooling/compose.yaml run --rm format make generate-protocol
docker compose -f automation/tooling/compose.yaml run --rm check make check-protocol test-protocol
```

Use the caller's UID/GID for writable generation as above. `generate-protocol`
builds both generators into temporary output, then updates committed bindings,
limits, diagnostics, and the standalone validator. Python orchestration and JavaScript
generation scripts live in `protocol/generator/`. `check-protocol` compares fresh
output without editing sources and runs under `lint` in CI. `test-protocol` runs the
independently compiled TypeScript protocol tests. The Rust contract and generator
tests run with the workspace under `test-server`.
CI runs `test-protocol` alongside `test-app`, which covers the application and
extension suites. See the [contract reference](connector-contract.md)
for sources, parsing rules, and integration responsibilities.

## Credential persistence

```bash
docker compose -f automation/tooling/compose.yaml run --rm check \
  make test-server lint-repo lint-sql format-check-sql
bash automation/acceptance/credentials/check_credentials.bash
```

The source checks cover credential state transitions, token-file recovery and
safety, and the live connection check in `server/tests/`.
The host runner owns a disposable Docker deployment and checks the actual
provisioning, rotation, revocation, restart, file permissions, and mount boundary.
The [credential runbook](../operations/connector-credentials.md) documents the
operator commands under `deploy/credentials/` and recovery states. Successful
provisioning requires a live authenticated heartbeat before removing the
previous token file.

## Production connector

```bash
docker compose -f automation/tooling/compose.yaml run --rm check make test-server test-extension test-web
bash automation/acceptance/connector/check_connector.bash
```

The host runner owns a fresh `raicho-connector-...` deployment and credentials.
It tests authenticated heartbeat, restart and recreation of all three services,
network interruption, changed server IP without proxy recreation, rejected proofs,
proxy route restrictions, the separate browser listener, and administrative
isolation by actual container IP. It checks logs, database contents, and mount
boundaries before removing its resources. It uses the production XPI and no
provider accounts. Before recovery tests it inspects the actual packaged XPI and
observes one authenticated generation for at least 600 seconds, requiring ongoing
heartbeat progress. A reconnect, counter reset, or heartbeat stall fails the check.
Rejected payloads carry fictional mail canaries. The runner checks that those
canaries and the raw token are absent from logs, diagnostics, and SQLite, and
rejects unexpected application tables. It checks the Thunderbird runtime policy
and a profile sentinel across restarts. Finally it builds the production XPI as
version 65535.0.0 into a disposable volume, mounts it over the image's extension
directory, and requires the same profile to activate that version and reconnect.
It runs unchanged in CI's `connector-test` job alongside the credential runner. See [acceptance evidence](connector-acceptance.md).

The connector runner takes about 20 minutes because of its idle observation. The
credential runner takes about 6 minutes and the mail runner about 3, after cached
image builds. Each owns a uniquely named project and networks, so they can run
concurrently. They run unchanged from a linked worktree, which tests a fixed
commit while editing continues in another checkout.

## Extension packaging

```bash
docker compose -f automation/tooling/compose.yaml run --rm check \
  make build-extension test-extension typecheck test-python
```

The packager stores sorted, uncompressed archive entries with fixed timestamps
and modes. Its reproducibility and version tests run under `test-python`.
`build-extension` uses disposable output. To export an XPI, mount an empty
output directory into the tooling container and run
`node extension/build.mjs --output /output/raicho.xpi`. The `--version` option overrides the manifest
version, as the connector upgrade check does. No test modules or credentials
enter the archive.

## Releases

Product versions are cut from the changelog. The commands and the bump rules
are in [versioning](versioning.md). A dry run writes nothing:

```bash
python3 -B -m automation.release.cut_release
```

Authorization follows [workflow](../contributing/workflow.md). CI behavior is
documented in [CI](ci-cd.md), and runtime details in [runtime](runtime.md).

## Mail API compatibility

```bash
docker compose -f automation/tooling/compose.yaml run --rm check make test-mailprobe
bash mailprobe/tests/check_mail_compatibility.bash
bash mailprobe/tests/check_mail_compatibility.bash --native
```

The separate `test-mailprobe` target compiles and tests the fixture extension.
It does not change `build-app` or the production XPI. The host runner builds
temporary tags for the tooling image and the normal Thunderbird image. The
tooling image runs the controller, SMTP/IMAP fault proxy, and test driver as
`mailprobe.tests` package modules. Their unit suites run under `test-python`. A one-off tooling service builds the mail test XPI into a
disposable artifact volume. Thunderbird mounts it read-only over its production
extension directory, with volume copy-up disabled, and mounts the profile setup
package read-only under `/opt/fixture/`. Only Thunderbird loads its own NSS library to seed credentials.
GreenMail retains its pinned upstream image. There is no separate mail-probe
image recipe. The runner cleans up its own images, containers, networks, and volumes.
The default run covers drafts and restart. After the scenarios, the runner checks
fault proxy submission, rejection, lost acknowledgment, and Sent-copy rejection
against GreenMail from inside the proxy container. `--native` also requires a
browser on the Linux Docker host for the sending permission and native draft
checkpoints. The probe modules compile with the shared production configuration
parser, so the mail probe XPI keeps their `mailprobe/src/` paths.
Sending and native checks are explicitly skipped in unattended mode. CI's
`application-test` job tests the probe TypeScript sources, `lint` runs its Python
suites, and `compatibility-test` runs the unattended experiment. The
[compatibility matrix](mail-api-compatibility.md) records limits and results.
