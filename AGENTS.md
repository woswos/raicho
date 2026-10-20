# Raicho agent instructions

Raicho is a browser interface for Thunderbird. Its containerized foundation
provides Rust/SQLite diagnostics and a TypeScript page alongside Thunderbird.
Its packaged extension connects through an authenticated control protocol and
reports connection health. Mail commands and browser mail workflows are still planned.

Read the documents below before working in this repository. The `@` lines are
file references. If your agent does not expand them automatically, open each
file explicitly. Rules live in these topic documents, not in this entry point.

## Always loaded

@docs/contributing/working-agreement.md
@docs/contributing/workflow.md
@docs/reference/key-conventions.md
@docs/reference/architecture.md

## Open when the task needs them

- Git branches, commits, and pull requests: `docs/contributing/git-and-pull-requests.md`
- Documentation placement: `docs/contributing/documentation-organisation.md`
- Engineering principles: `docs/contributing/coding-principles.md`
- Repository layout, runtime code, and test fixtures: `docs/reference/project-structure.md`
- Commands: `docs/reference/build-test-generate.md`
- CI and pull request guards: `docs/reference/ci-cd.md`
- Showcase and tooling style: `docs/coding/coding-standards.md`
- Formatters and linters: `docs/coding/linting-and-formatting.md`
