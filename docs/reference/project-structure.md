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
runtime/           Production runtime helpers, including Thunderbird startup
config/            Runtime configuration, including the gateway's Nginx config
compose/           Runtime, administration, test, tooling, and CI Compose files
server/            Rust diagnostics, SQLite queries, migrations, and tests
web/               TypeScript diagnostics, public files, and behavioral tests
extension/         Production connector and separate lifecycle/mail API test probes
protocol/          Control schema, limits, shared fixtures, Rust bindings/generator
devbin/            Repository guards, language runners, and tooling tests
tests/             Thunderbird runtime tests and disposable integration fixtures
docs/contributing/ Contribution workflow and working agreements
docs/reference/    Current structure, tooling, CI, and architecture
docs/coding/       Concrete coding and formatting conventions
docs/decisions/    Decision records and their template
docs/planning/     Active and completed staged plans
```

`compose/compose.yaml` runs the application and Thunderbird with separate volumes
and the fixed gateway between their networks.
`compose.admin.yaml` adds local desktop administration, and `compose.test.yaml`
adds the isolated runtime fixture driver. `compose.tools.yaml` provides checks
and formatting, with `compose.ci.yaml` adding the GitHub event mount.
`compose.credentials.yaml` supplies offline provisioning and the Thunderbird
secret mount, endpoint, and live verification through the
[credential commands](../operations/connector-credentials.md).
`compose.extension_test.yaml` is a standalone disposable extension lifecycle
fixture. `compose.mail_test.yaml` runs the separate fictional mail experiment,
with `compose.mail_admin.yaml` enabling its native UI checks. All Compose files
live in `compose/`. The [runtime guide](../operations/local-runtime.md) and
[tooling commands](build-test-generate.md) show their combinations.

The [brand guide](../../assets/brand/README.md) describes asset locations and
[showcase guide](../../assets/brand/showcase/README.md) describes editable pages.
See [architecture](architecture.md) for the distinction between the prototype
and the intended product.

The [connector contract](connector-contract.md) describes the schema, generated
modules, and their current integration boundary. Component responsibilities and
persistence are defined in [architecture](architecture.md).

## Test code

`tests/thunderbird_runtime/` tests the four production Python modules in
`runtime/thunderbird/`. Set the source import path using the documented
[test command](build-test-generate.md#application-tooling).

`tests/extension_lifecycle/` owns the lifecycle fixture controller and its tests.
`tests/mail_compatibility/` groups the mail probe and scenarios under `probe/`,
fictional profile setup under `profile/`, and SMTP/IMAP fault infrastructure under
`proxy/`, with their unit tests alongside the fixture code. The tooling image
packages these fixtures under `/opt/raicho/tests/`. Docker recipes stay under
`containers/`, and the production Thunderbird image copies only its explicit
runtime modules. See the [fixture commands](build-test-generate.md#mail-api-compatibility)
for the mail test extension and profile mounts.

Module boundaries follow the
[coding standards](../coding/coding-standards.md#naming-and-structure).
