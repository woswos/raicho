# Project structure

Raicho contains a runnable diagnostics foundation, an independent Thunderbird
image, brand assets, and the shared workflow. Mail integration is still planned.

```text
AGENTS.md          Always-loaded instructions and pointers to task-specific docs
.agents/skills/    Canonical shared workflow skills
.github/           Pull request templates and GitHub Actions workflows
assets/brand/      Production identity masters, fonts, guides, and prototypes
containers/        Tooling, Rust application, and independent Thunderbird images
compose/           Runtime, administration, test, tooling, and CI Compose files
server/            Rust diagnostics, SQLite queries, migrations, and tests
web/               TypeScript diagnostics, public files, and behavioral tests
devbin/            Repository guards, language runners, and tooling tests
docs/contributing/ Contribution workflow and working agreements
docs/reference/    Current structure, tooling, CI, and architecture
docs/coding/       Concrete coding and formatting conventions
docs/decisions/    Decision records and their template
docs/planning/     Active and completed staged plans
```

`compose/compose.yaml` runs the application and Thunderbird with separate volumes.
`compose.admin.yaml` adds local desktop administration, and `compose.test.yaml`
adds the isolated runtime fixture driver. `compose.tools.yaml` provides checks
and formatting, with `compose.ci.yaml` adding the GitHub event mount. All five
files live in `compose/`. The [runtime guide](../operations/local-runtime.md) and
[tooling commands](build-test-generate.md) show their combinations.

The [brand guide](../../assets/brand/README.md) describes asset locations and
[showcase guide](../../assets/brand/showcase/README.md) describes editable pages.
See [architecture](architecture.md) for the distinction between the prototype
and the intended product.

## Planned application layout

The [foundation plan](../planning/active/20261017-thunderbird-first-foundation.md#proposed-source-layout)
introduces the following directories with the extension stage. They do not exist yet.

```text
extension/         TypeScript Thunderbird extension
protocol/          Versioned connector schemas
```

The existing brand sources remain in
`assets/brand/`. Component responsibilities and persistence are defined in
[architecture](architecture.md).
