# Build, test, and generate

The static showcase has no build step or code generation. Its preview and export
procedure is maintained in the [showcase guide](../../assets/brand/showcase/README.md).

## Make

Run Make from the repository root, or with `-f` from anywhere. The host needs
Docker, Compose, Git, and GNU Make, but no language toolchains. On the host, each
target first builds the tooling image, which the Docker cache keeps quick when
nothing changed, then runs the same target inside the tooling container as the
caller's UID and GID. Targets that write files use the writable `format` service,
so rewritten files keep the caller's ownership. A linked Git worktree gets its
shared Git metadata mounted read-only at the same absolute path. When
`GITHUB_EVENT_PATH` is set, as in GitHub Actions, the event JSON is mounted too.
Inside the tooling container the same targets run directly. The image sets
`RAICHO_TOOLING_CONTAINER`, which selects that mode.
`automation/tooling/host.mk` and `automation/tooling/container.mk` hold the two
modes.

```bash
make lint test
```

Output stays short when commands succeed. Docker builds, Cargo, and the acceptance
suites' Docker commands print no progress. Each Rust, Node, and Python suite
prints one summary line, and the patch coverage gate only its totals. Formatters print only problems, except that shfmt lists the
files it rewrites. Guards still print one passed line each, and failures print
in full. Add `VERBOSE=1`, as in `make VERBOSE=1 build`, to restore Docker and
Cargo progress and live Rust test output.

Each step prints one line when it starts and one with its duration when it
finishes, such as `building server` and `built server, took 12 seconds`. A failed
step prints `building server failed after 3 seconds` and keeps the command's exit
status. Aggregate targets such as `build` print only their steps' lines.
`automation/tooling/step.bash` writes these lines, colored when `TERM` names an
xterm terminal.

| Target | Behavior |
| --- | --- |
| `build` | Tooling image, server, web page, and extension builds, then the runtime images |
| `test` | Every source suite: Python, tooling fixtures, server, web, extension, mail probe, and protocol |
| `lint` | Repository guards, language linters, spelling, formatting and type checks, and protocol generation drift |
| `format` | Rewrite files in the documented formatting scope |
| `generate` | Regenerate the committed protocol outputs |
| `coverage` | Line coverage of the source suites |
| `check-patch-coverage` | Fail when changed lines are below the coverage threshold |
| `benchmark` | Rust benchmarks, each compared with its previous run |
| `images` | Runtime images only |
| `acceptance` | Every disposable deployment suite, on the host |
| `clean` | Remove ignored build output, interrupted acceptance runs, and this project's images, on the host |
| `lint-pr` | PR metadata, design/decision policy, and changelog guard |

Component targets run one piece of those: `build-server`, `build-web`,
`build-extension`, `test-server`, `test-web`, `test-extension`, `test-mailprobe`,
`test-protocol`, `test-python`, and `test-tooling`; `lint-repo`, `lint-bash`,
`lint-python`, `lint-javascript`, `lint-typescript`, `lint-rust`, `lint-sql`, and
`lint-spelling`; `format` and `format-check`, each with `-bash`, `-python`,
`-javascript`, `-rust`, and `-sql` variants, `format-spelling`, and `typecheck`;
and `generate-protocol` and `check-protocol`.
The `-javascript` formatting variants also cover TypeScript, JSON, and YAML. The acceptance
suites run one at a time as `acceptance-runtime`, `acceptance-connector`,
`acceptance-credentials`, and `acceptance-mail`.

## Tooling image

The image supplies Bash, Python, Make, Node, Rust, the selected quality and
coverage tools, and Python test fixtures. Its build-context allowlist is
`automation/tooling/Dockerfile.dockerignore`. Fixture sources come from the
component-local directories listed in [project structure](project-structure.md#test-code).
The tooling entrypoint lives at `automation/tooling/entrypoint.bash`.

The entrypoint also compares `package.json`, `package-lock.json`, `.npmrc`,
`eslint.config.mjs`, and `automation/tooling/requirements.txt` with the image
copies. `.npmrc` disables install scripts, audits, and funding messages for every
`npm ci` in the tooling and runtime images. A mismatch stops the command with a rebuild instruction, preventing stale
installed dependencies or lint rules. Make on the host rebuilds the image first,
so the mismatch only appears when the container runs without it.

The `check` service mounts the repository read-only. Tool caches and temporary
outputs live outside that mount. Cargo's registry and build output persist in the
`raicho-tools_cache` volume at `/cache`, which the `check` and `format` services
share, so repeated runs reuse downloads and compiled dependencies. Cargo locks the
cache, so concurrent runs wait for each other. Other temporary output lives on each
container's own `/tmp` and disappears with it. The service does not mount the Docker socket or start
application services, so Make inside the container never launches nested
containers.

## Checks and formatting

```bash
make lint test-python test-tooling
make format
```

`lint-repo` runs the repository guards, including file, directory, skill, and
database naming. `format-check` checks the selected source and configuration
formatting without edits, and `typecheck` runs the TypeScript compiler with no
emitted output. `test-tooling` runs disposable passing and failing Rust,
TypeScript, and SQL fixtures that exercise the runners. `lint-sql` checks owned
SQLite source for syntax and configured lint rules, `format-check-sql` compares
formatted temporary copies with the SQL sources, and `format-sql` rewrites them
using formatting rules only.

`lint-spelling` runs typos over the same files and reports one line per known
misspelling. `make format-spelling` applies its corrections. `make format`
leaves spelling alone, because a correction changes words in code and prose
and needs its own review. Add accepted false positives to `.typos.toml`.

The guards in `automation/repository/` are Python module entry points. Their
optional repository-root argument defaults to the repository containing the
script. Explicit roots are normalized to absolute paths from the caller's
working directory. PR guards resolve a relative `GITHUB_EVENT_PATH` against
that repository root. The Make targets above remain the normal interface.
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

For SQL alone, use `make lint-sql format-check-sql` or `make format-sql`. SQL
checks need no database connection. Applied migration files must retain
their original bytes, as explained in the [runtime reference](runtime.md#sqlite-initialization-and-migrations).

A new or changed Rust dependency also changes `Cargo.lock`. The `check` service
mounts the checkout read-only and builds use `--locked`, so refresh the lockfile
through the writable service, with the caller's UID and GID, first:

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
make lint-pr
```

Without a local base, the guard conservatively requires a design or decision.
A `design` label needs both commits to prove that only planning docs changed.
GitHub event metadata always takes precedence over local overrides.

When `GITHUB_EVENT_PATH` is set, Make adds `automation/tooling/compose.ci.yaml`,
which bind-mounts the event JSON read-only at `/tmp/github-event.json`. This
override requires `GITHUB_EVENT_PATH` to be an absolute path to an existing host
file. The checkout supplies the base/head Git objects.

## Application tooling

```bash
make build test
```

Inside the container, `build` combines `build-server`, `build-web`, and
`build-extension`, and `test` runs every source suite. Rust uses `--workspace --all-targets --locked` and
temporary Cargo output. The browser build uses `tsc`, copies public files and
the selected identity assets, then runs Node's built-in tests against compiled
modules. The web builder is `web/build.mjs`, and extension packaging
uses `extension/build.mjs`. Both run on Node alone. The shared dispatcher remains in
`automation/build/application.py`. All temporary build output stays
outside the source mount.

Tooling defaults to no Rust debug symbols or incremental output, keeping the
build cache small. These settings affect check containers, not release images. Set
`CARGO_PROFILE_DEV_DEBUG=2`, `CARGO_PROFILE_TEST_DEBUG=2`, or `CARGO_INCREMENTAL=1`
before running Make when that output is needed for local debugging.

`make images`, which `make build` runs last on the host, builds the runtime images
with `docker compose build`. This compiles release artifacts and installs the independently packaged Thunderbird runtime.
The image recipes pin base digests and downloaded artifacts. The Thunderbird
image also builds the XPI with TypeScript and the deterministic Node packager.
See [local runtime](../operations/local-runtime.md) for Compose
startup, administration, persistence checks, and cleanup.

`automation/tooling/compose.yaml` remains a development-only configuration and does
not start the application. Application state belongs to the runtime volumes, not the
checkout. Control-contract generation is described below. Mail commands remain
outside the production contract.

## Acceptance

```bash
make acceptance
```

`acceptance` needs Docker on the host and runs each disposable deployment suite in
turn. `acceptance-runtime` runs `automation/acceptance/runtime/check_runtime.bash`,
which builds a `raicho-runtime-...` project with the test overlay, checks startup,
persistence across recreation, administrative isolation, and readiness while
Thunderbird is stopped, then removes the project. It uses `COMPOSE_PROJECT_NAME`
when set, as CI does, and refuses the `raicho` project. The connector, credential,
and mail runners are described below. Each suite owns uniquely named resources, so
the suites can also run concurrently from separate shells.

## Clean

```bash
make clean
```

`clean` runs `automation/tooling/clean.bash` on the host. It removes:

- Files that the repository's own `.gitignore` files ignore, such as `target/`,
  `dist/`, `node_modules/`, and `__pycache__/`, except `.raicho/`. Files ignored
  only by global or `.git/info/exclude` rules stay.
- Containers, volumes, networks, and images of interrupted acceptance projects,
  which are named `raicho-<suite>-<timestamp>-<number>`, as `raicho-ci-...` is.
- Acceptance state directories named `raicho-<suite>.XXXXXXXX` under `TMPDIR` or
  `/tmp`. Fixture files owned by root are removed through `raicho-tools:local`.
- The `raicho-tools:local`, `raicho-server:local`, `raicho-gateway:local`, and
  `raicho-thunderbird:local` images. An image a container still uses is kept and
  reported.
- The `raicho-tools_cache` volume with Cargo's downloads and build output, unless a
  container is using it.

It never touches the `raicho` deployment, its volumes, or `.raicho/`, and it does
not prune the Docker build cache, which the default builder cannot limit to one
project. The next `make` rebuilds the tooling image.

## Coverage

```bash
make coverage
PR_BASE_SHA="$(git rev-parse origin/main)" make check-patch-coverage
```

`coverage` runs the Rust workspace tests, the protocol, web, and extension
TypeScript suites, and the `test-python` and `test-tooling` suites with coverage
instrumentation. It prints line coverage for each measured source file. Rust builds
with `-C instrument-coverage` into its own target directory in the cache, and the
image's LLVM tools merge and export the profiles. TypeScript test builds emit source
maps, so Node's built-in coverage reports lines of the `.ts` sources. The XPI never
contains source maps. coverage.py measures Python, including subprocesses and the
guard copies that tests run from temporary repositories, with its settings under
`[tool.coverage]` in `pyproject.toml`. The lcov reports stay in
`/tmp/raicho-coverage` inside the container.

Tests, benchmarks, generated files, dependencies, the acceptance drivers in
`automation/acceptance/`, and the `mailprobe/` test artifact are not measured. A
source that no test loads, such as a browser entry point, is absent from the
reports rather than reported as uncovered.

`check-patch-coverage` runs `coverage`, then diff-cover over the reports. It fails
when fewer than 90 percent of the changed, measured lines are covered, and lists
the uncovered lines. The threshold is `fail_under` under `[tool.diff_cover]` in
`pyproject.toml`. The comparison base is the PR base from the GitHub event or
`PR_BASE_SHA`, otherwise the merge base with `origin/main`. Uncommitted changes
count. The [patch coverage decision](../decisions/20261026-repository-layout.md#patch-coverage)
records the tool choices.

## Benchmarks

```bash
make benchmark
```

`benchmark` runs every Rust benchmark target with `cargo bench`, using
[Criterion](https://github.com/criterion-rs/criterion.rs) under the
[benchmark decision](../decisions/20261026-rust-benchmarks.md). Each benchmark
prints its time range, its change from the previous run, and any outliers.
Criterion keeps those baselines in the Cargo cache volume, so `make clean` resets
them. Its progress lines appear only with `VERBOSE=1` or when the run fails.

`protocol/rust/benches/frames.rs` measures the connector's per-frame work:
decoding an authentication and a ping frame, sealing and opening a ping through
`Channel`, and computing and verifying a client proof. `make lint` checks
benchmark code with Clippy, and `make test` runs each benchmark once as a test,
so a broken benchmark fails before anyone times it. CI does not run benchmarks,
because shared runners make timings too noisy to compare.

## Connector contract

```bash
make generate
make check-protocol test-protocol
```

`generate`, which runs `generate-protocol`, builds both generators into temporary output, then updates committed bindings,
limits, diagnostics, and the standalone validator. Python orchestration and JavaScript
generation scripts live in `protocol/generator/`. `check-protocol` compares fresh
output without editing sources and runs under `lint` in CI. `test-protocol` runs the
independently compiled TypeScript protocol tests. The Rust contract and generator
tests run with the workspace under `test-server`.
`make test` includes `test-protocol` with the application and extension suites.
See the [contract reference](connector-contract.md)
for sources, parsing rules, and integration responsibilities.

## Credential persistence

```bash
make test-server lint-repo lint-sql format-check-sql acceptance-credentials
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
make test-server test-extension test-web acceptance-connector
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
make test-mailprobe acceptance-mail
bash mailprobe/tests/check_mail_compatibility.bash --native
```

The separate `test-mailprobe` target compiles and tests the fixture extension.
It is not part of `make build` and does not change the production XPI. The host runner builds
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
