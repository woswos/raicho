# Project structure

Raicho contains a runnable diagnostics foundation, an independent Thunderbird
image, brand assets, and the shared workflow. Mail integration is still planned.

```text
AGENTS.md          Always-loaded instructions and pointers to task-specific docs
CHANGELOG.md       Product changelog used to cut semantic versions
compose*.yaml      Base deployment and its administration, credential, and login overlays
.agents/skills/    Canonical shared workflow skills
.github/           Pull request templates and GitHub Actions workflows
assets/brand/      Production identity masters, fonts, guides, and prototypes
deploy/            Per-service image recipes, runtime code, configuration, and tests
server/            Rust diagnostics, SQLite queries, migrations, and tests
web/               Preact browser client, public files, and behavioral tests
extension/         Production connector, Thunderbird adapter, packager, and tests
mailprobe/         Mail API compatibility probe, fixtures, Compose files, and runner
protocol/          Connector and status schemas, limits, fixtures, generators, implementations
automation/        Development commands and support packages grouped by responsibility
docs/contributing/ Contribution workflow, working agreements, and project invariants
docs/reference/    Current structure, tooling, CI, and architecture
docs/coding/       Engineering principles and coding and formatting conventions
docs/decisions/    Decision records and their template
docs/planning/     Active and completed staged plans
```

## Placement rules

Use these locations when adding files or moving existing code:

| Material | Location |
| --- | --- |
| Deployed service recipe, filter, runtime code, configuration, and tests | `deploy/<service>/` |
| Base Compose deployment and operator overlays | Repository root |
| Test-only Compose overlays | Beside the acceptance driver that uses them |
| Application sources | Their owning `server/`, `web/`, or `extension/` component |
| Mail API compatibility probe, its fixtures, and its runner | `mailprobe/` |
| Shared connector and status schemas, limits, fixtures, and implementations | `protocol/` |
| Protocol generation scripts and support modules | `protocol/generator/` |
| Component-specific build scripts and packaging | The owning component's root |
| Shared development commands and their support modules | `automation/<responsibility>/` |

Each deployed service owns one directory under `deploy/`: `raicho/`, `gateway/`,
`thunderbird/`, and the operational `credentials/` wrapper. The directory holds
the image recipe, its `Dockerfile.dockerignore`, the service's runtime code and
configuration such as `deploy/gateway/nginx.conf`, and their tests. Build filters
list explicit files or source directories from the owning components. A bare
parent such as `!extension/` would re-include that whole tree. `credentials/` is
the exception: it builds no image and runs no service of its own. Its host
wrapper drives one-off containers from the Raicho server image. The
[repository layout decision](../decisions/20261026-repository-layout.md) records
this organization.

Shared protocol implementations belong together in `protocol/rust/` and
`protocol/typescript/`, with their own sources and tests. Keep them independent
of Thunderbird APIs. Thunderbird adapters and extension integration tests belong
in `extension/`. See the [protocol placement decision](../decisions/20261026-protocol-contracts.md).
Protocol generation belongs to `protocol/generator/`, beside the schema and
implementations it produces.

Apply the [source filename](../coding/coding-standards.md#source-filenames),
[directory name](../coding/coding-standards.md#directory-names), and
[documentation naming](../contributing/documentation-organisation.md#naming)
conventions within these locations.

## Automation

Keep component-specific builders with their sources: `web/build.mjs`
and `extension/build.mjs`. Their packaging and artifact-boundary
tests belong in `extension/tests/`. The
[component ownership decision](../decisions/20261026-repository-layout.md#tests)
records this placement.

Group shared development automation by responsibility, including its import-only
support modules. Use Make as the main developer command interface. On the host it
runs each target through the tooling image, and inside the image it invokes Python
modules from the repository root with `python3 -B -m`, and Bash or JavaScript
entry points by path. `automation/tooling/host.mk` and
`automation/tooling/container.mk` hold the two modes. Keep Bash for substantive host/Docker orchestration.
Do not add thin compatibility wrappers or restore a flat helper directory.

| Responsibility | Package |
| --- | --- |
| Agent, naming, changelog, and pull request guards | `automation/repository/` |
| Language linting, formatting, and type checking | `automation/quality/` |
| Development tooling image, entrypoint, Compose files, Make modes, the target guide, deployment health, step logs, and cleanup | `automation/tooling/` |
| Cross-component application build/test dispatch and coverage | `automation/build/` |
| Versioning, changelogs, and release preparation | `automation/release/` |
| Cross-service disposable deployment checks | `automation/acceptance/` |
| Fixtures shared by automation tests | `automation/testing/` |

Cross-service acceptance drivers use `browsing/`, `connector/`, `credentials/`, and
`runtime/` subpackages, each with its own `run.bash`. The connector and credential runners
source `automation/acceptance/credential_deployment.bash` for their disposable
project, state directory, fixture container, credential commands, and cleanup.
The connector runner also sources `connector/network.bash`, which its tests
exercise directly.
Every acceptance runner, including the mail runner, sources
`automation/acceptance/project_record.bash` to record its project for CI.
`automation/acceptance/remove_recorded_projects.bash` removes those projects in
the final step of each acceptance job.
The shared repository-path and output-mode helpers live at
`automation/paths.py` and `automation/output.py`.

Operational credential provisioning, rotation, and live verification belong in
`deploy/credentials/` as a host Bash wrapper around `raicho-server connector`
subcommands. `login.bash` there wraps the `raicho-server login` subcommands.
`state.bash` holds the deployment selection, state directory checks, operation
lock, and per-user lock that both wrappers, `make deploy-clean`, and `make mrproper` share.
These commands manage a deployment and are separate from acceptance tests that
create disposable deployments. Their procedure is in the
[credential runbook](../operations/connector-credentials.md). The
[automation decision](../decisions/20261026-repository-layout.md#automation) records this
organization and the replacement of the former `devbin/` tree.

## Compose deployments

The root `compose.yaml` runs the application and Thunderbird with separate
volumes and the fixed gateway between their networks, so `docker compose` works
from the repository root without `-f`. `compose.admin.yaml` adds local desktop
administration. `compose.credentials.yaml` supplies offline provisioning and the
Thunderbird token mount, endpoint, and live verification through the
[credential commands](../operations/connector-credentials.md).
`compose.login.yaml` adds the one-off `login` service that the
[login commands](../operations/browser-login.md) run.

Test overlays live with their drivers. `automation/acceptance/runtime/compose.test.yaml`
adds the isolated runtime fixture driver, and
`automation/acceptance/connector/compose.upgrade.yaml` mounts a version-bumped
production XPI for the connector acceptance upgrade check, and
`automation/acceptance/browsing/compose.browsing.yaml` adds GreenMail, the
fictional Thunderbird profile, and the browsing driver. Compose resolves every
overlay's paths from the first file, so these overlays use repository-relative
paths. `automation/tooling/compose.yaml` provides checks and formatting, with
`automation/tooling/compose.ci.yaml` adding the GitHub event mount when Make sees
`GITHUB_EVENT_PATH`.
`mailprobe/compose.yaml` runs the separate fictional mail experiment, with
`mailprobe/compose.admin.yaml` enabling its native UI checks.
The [runtime guide](../operations/local-runtime.md) and
[tooling commands](build-test-generate.md) show their combinations.

The [brand guide](../../assets/brand/README.md) describes asset locations and
[showcase guide](../../assets/brand/showcase/README.md) describes editable pages.
See [architecture](architecture.md) for the distinction between the prototype
and the intended product.

The [connector contract](connector-contract.md) describes the schema, generated
modules, and their current integration boundary. Component responsibilities and
persistence are defined in [architecture](architecture.md).

## Test code

Keep tests, mocks, fixture controllers, and profile setup with their owning
component, using its `tests/` subtree. Do not create a repository-root test tree.
Automation tests live in the owning package's `tests/` subtree, and tests of the
root `automation/` modules live in `automation/tests/`. Changelog guard
regressions belong in `automation/repository/tests/`, beside the other PR policy
tests. Shared guard fixtures, the `docker` command mock, and the POSIX ACL helper live in
`automation/testing/`.

`server/tests/`, `web/tests/`, and `extension/tests/` own their respective
application and integration tests. `extension/tests/` also owns Python packaging
regressions. The production-XPI inspector that connector acceptance runs inside
Thunderbird lives with that driver as `automation/acceptance/connector/inspect_xpi.py`,
and the packaging boundary tests reuse it.
The server's integration tests compile into two test binaries, so a change relinks
two executables instead of one per file. `server/tests/integration/main.rs` declares
each test module and the shared `support/` module. `server/tests/processes/` holds
the tests that spawn processes. They run apart because a child process briefly
inherits the open files of every test in its process, including SQLite instance
locks. Add a test file as a module of one of them, never directly in `server/tests/`,
where Cargo would build it as another binary.

`protocol/rust/tests/` and `protocol/typescript/tests/` run the shared protocol
fixtures against their respective implementations. TypeScript protocol tests
compile independently of the extension. See the
[contract commands](build-test-generate.md#connector-contract).
Generator regressions live in `protocol/generator/tests/`, and the Rust generator's
unit tests sit beside its code in `protocol/generator/src/`. Rust benchmarks live in
the owning crate's `benches/` directory, such as `protocol/rust/benches/`, and
reuse the shared protocol fixtures.
`protocol/fixtures/configuration/connector.json` lists valid and invalid connector
tokens and endpoints. The server's `Credential::parse`, the Thunderbird policy
writer, and the extension's managed configuration parser each test against it,
so their separate boundary checks cannot drift.

`deploy/credentials/tests/` owns the provisioning wrapper tests. Token-file
recovery, file-safety, and live-check tests live with the Rust implementation in
`server/tests/`. `deploy/thunderbird/tests/` tests the production `thunderbird`
package beside it.

Python modules are packages imported from the repository root, including those
that run inside containers. `make test-python` discovers every `*_tests.py` in
them, so a new Python test directory needs only the `__init__.py` files on its
import path.

`mailprobe/` is a test artifact, separate from the production extension. Its
`tests/` groups the controller and scenarios under `probe/`, fictional profile
setup under `profile/`, and SMTP/IMAP fault infrastructure under `proxy/`, with
their unit tests alongside the fixture code. The host acceptance runner and the
probe packaging, fixture-image, and runner-cleanup tests sit directly in `tests/`.
The probe's transport tests reuse the extension's WebSocket fixture,
`extension/tests/probe_fixture.mjs`. `proxy/mail_fixture_integration.py` needs the
live GreenMail deployment, so the runner runs it inside the proxy container and
its name stays outside the `*_tests.py` pattern.
See the [fixture commands](build-test-generate.md#mail-api-compatibility)
for the mail test extension and profile mounts.

## Tooling and image boundaries

Use the shared tooling image for linters, formatters, test runners, Python mocks,
and fixture drivers locally and in CI. Independent fixture processes can use
separate containers from that image. Thunderbird and upstream fixture services
such as GreenMail retain their runtime images. The
[shared tooling decision](../decisions/20261026-repository-layout.md#tooling-image)
records the image boundary.

The tooling image packages fixture sources at their component-relative paths
under `/opt/raicho/`. Its build-context filter includes those fixture directories
and tooling dependencies, excluding host Docker orchestration. Keep fixture code
out of production runtime images and production XPIs. The Thunderbird recipe copies its explicit runtime modules,
and its filter excludes test directories. Rebuild and execution commands live in
[build, test, and generate](build-test-generate.md#tooling-image).

Module boundaries follow the
[coding standards](../coding/coding-standards.md#naming-and-structure).
