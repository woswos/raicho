# Project structure

Raicho currently contains brand assets and static browser prototypes, plus the
shared development workflow. There is no production mail client or extension.

```text
AGENTS.md          Always-loaded instructions and pointers to task-specific docs
.agents/skills/    Canonical shared workflow skills
.github/           Pull request templates and GitHub Actions workflows
assets/brand/      Production identity masters, fonts, guides, and prototypes
containers/        Tooling image recipe, with application images still planned
compose.tools.yaml Read-only checks and explicit writable formatting
compose.ci.yaml    Read-only GitHub event mount for PR checks
devbin/            Repository guards, language runners, and tooling tests
docs/contributing/ Contribution workflow and working agreements
docs/reference/    Current structure, tooling, CI, and architecture
docs/coding/       Concrete coding and formatting conventions
docs/decisions/    Decision records and their template
docs/planning/     Active and completed staged plans
```

The [brand guide](../../assets/brand/README.md) describes asset locations and
[showcase guide](../../assets/brand/showcase/README.md) describes editable pages.
See [architecture](architecture.md) for the distinction between the prototype
and the intended product.

## Planned application layout

The [foundation plan](../planning/active/20261017-thunderbird-first-foundation.md#proposed-source-layout)
proposes the following directories. They do not exist yet and are introduced
with their implementation stages.

```text
server/            Rust application server and backend adapters
web/               TypeScript browser client
extension/         TypeScript Thunderbird extension
protocol/          Versioned connector schemas
```

Additional Compose files will define the runtime services and opt-in
administrative access. The existing brand sources remain in
`assets/brand/`. Component responsibilities and persistence are defined in
[architecture](architecture.md).
