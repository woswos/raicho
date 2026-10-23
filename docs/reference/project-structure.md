# Project structure

Raicho contains a runnable diagnostics foundation, an independent Thunderbird
image, brand assets, and the shared workflow. Mail integration is still planned.

```text
AGENTS.md          Always-loaded instructions and pointers to task-specific docs
CHANGELOG.md       Product changelog used to cut semantic versions
.agents/skills/    Canonical shared workflow skills
.github/           Pull request templates and GitHub Actions workflows
assets/brand/      Production identity masters, fonts, guides, and prototypes
containers/        Docker recipes, build-context filters, and dependency locks
runtime/           Production runtime helpers and their component-local tests
config/            Runtime configuration, including the gateway's Nginx config
compose/           Runtime, administration, test, tooling, and CI Compose files
server/            Rust diagnostics, SQLite queries, migrations, and tests
web/               TypeScript diagnostics, public files, and behavioral tests
extension/         Production connector and separate lifecycle/mail API test probes
protocol/          Control schema, limits, fixtures, generators, and implementations
automation/        Development commands and support packages grouped by responsibility
docs/contributing/ Contribution workflow and working agreements
docs/reference/    Current structure, tooling, CI, and architecture
docs/coding/       Concrete coding and formatting conventions
docs/decisions/    Decision records and their template
docs/planning/     Active and completed staged plans
```

## Placement rules

Use these locations when adding files or moving existing code:

| Material | Location |
| --- | --- |
| Docker recipes and image dependency metadata | `containers/<image>/` |
| Compose deployments and overrides | `compose/` |
| Production runtime helpers | `runtime/<component>/` |
| Runtime service configuration | `config/<service>/` |
| Application sources | Their owning `server/`, `web/`, or `extension/` component |
| Shared protocol schema, limits, fixtures, and implementations | `protocol/` |
| Protocol generation scripts and support modules | `protocol/generator/` |
| Component-specific build scripts and packaging | The owning component's root |
| Shared development commands and their support modules | `automation/<responsibility>/` |

Keep `containers/` focused on recipes and build metadata. Each image's
`Dockerfile.dockerignore` lives beside its Dockerfile and selects inputs from
their owning components. The [container input decision](../decisions/20261026-repository-layout.md#components)
records this separation.

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

Keep component-specific builders with their sources: `web/raicho_build_web.mjs`
and `extension/raicho_build_extension.py`. Their packaging and artifact-boundary
tests belong in `extension/tests/`. The
[component ownership decision](../decisions/20261026-repository-layout.md#tests)
records this placement.

Group shared development automation by responsibility, including its import-only
support modules. Use Make as the main developer command interface. It invokes Python
modules directly from the repository root with `python3 -B -m`, and Bash or
JavaScript entry points by path. Keep Bash for substantive host/Docker orchestration.
Do not add thin compatibility wrappers or restore a flat helper directory.

| Responsibility | Package |
| --- | --- |
| Agent, naming, changelog, and pull request guards | `automation/repository/` |
| Language linting, formatting, type checking, and tooling entrypoint | `automation/quality/` |
| Cross-component application build/test dispatch | `automation/build/` |
| Versioning, changelogs, and release preparation | `automation/release/` |
| Cross-service disposable deployment checks | `automation/acceptance/` |
| Fixtures shared by automation tests | `automation/testing/` |

Cross-service acceptance drivers use `connector/` and `runtime/` subpackages.
The shared repository-path helper lives at
`automation/raicho_paths.py`.

Operational credential provisioning, rotation, and live verification belong in
`runtime/credentials/`, including their host Bash wrapper and Python helpers.
These commands manage a deployment and are separate from acceptance tests that
create disposable deployments. Their procedure is in the
[credential runbook](../operations/connector-credentials.md). The
[automation decision](../decisions/20261026-repository-layout.md#automation) records this
organization and the replacement of the former `devbin/` tree.

## Compose deployments

`compose/compose.yaml` runs the application and Thunderbird with separate volumes
and the fixed gateway between their networks.
`compose.admin.yaml` adds local desktop administration, and `compose.runtime_test.yaml`
adds the isolated runtime fixture driver. `compose.tools.yaml` provides checks
and formatting, with `compose.ci.yaml` adding the GitHub event mount.
`compose.credentials.yaml` supplies offline provisioning and the Thunderbird
secret mount, endpoint, and live verification through the
[credential commands](../operations/connector-credentials.md).
`compose.extension_test.yaml` is a standalone disposable extension lifecycle
fixture. `compose.mail_test.yaml` runs the separate fictional mail experiment,
with `compose.mail_admin.yaml` enabling its native UI checks.
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
Automation tests live in the owning package's `tests/` subtree. Changelog guard
regressions belong in `automation/repository/tests/`, beside the other PR policy
tests. Shared guard fixtures live in `automation/testing/`.

`server/tests/`, `web/tests/`, and `extension/tests/` own their respective
application and integration tests. `extension/tests/` also owns Python packaging
regressions, production-XPI inspection used by connector acceptance, and shared
lifecycle/mail fixture-image and runner-cleanup assertions.
Rust test support lives under
`server/tests/support/`.

`protocol/rust/tests/` and `protocol/typescript/tests/` run the shared protocol
fixtures against their respective implementations. TypeScript protocol tests
compile independently of the extension. See the
[contract commands](build-test-generate.md#connector-contract).
Generator regressions live in `protocol/generator/tests/`.

`runtime/credentials/tests/` owns provisioning wrapper, file recovery, and live
verification unit tests. Its `acceptance/` subtree owns the disposable credential
deployment runner and fixture checks. `make lint-repo` includes credential unit
tests, extension packaging and fixture regressions, protocol generator
tests, and the automation package suites.

`runtime/thunderbird/tests/` tests the four production Python modules in
`runtime/thunderbird/`. Set the source import path using the documented
[test command](build-test-generate.md#application-tooling).

`extension/lifecycleprobe/tests/` owns the lifecycle fixture controller, host
acceptance runner, runtime checker, and unit tests.
`extension/mailprobe/tests/` groups the mail probe and scenarios under `probe/`,
fictional profile setup under `profile/`, and SMTP/IMAP fault infrastructure under
`proxy/`, with their unit tests alongside the fixture code and the host acceptance
runner directly in `tests/`.
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
