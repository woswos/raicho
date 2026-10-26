# Group Compose configurations and check SQL

- Status: accepted, amended by `20261026-repository-layout`
- Date: 2026-10-18
- Deciders: Raicho maintainer

## Context

The approved foundation introduces runtime, admin, and test Compose files next
to the existing tooling and CI configurations. SQL lives in Rust strings and
has no dedicated syntax/style checks. The maintainer requested a dedicated
Compose folder and SQL linting/formatting in the existing Docker workflow.

## Decision

Keep Compose files in `compose/`, alongside the image recipes in `containers/`.
Use directory-relative build contexts and mounts, a default runtime project
name of `raicho`, and explicit project overrides for isolated instances.
Fresh volumes are acceptable. No compatibility files or data migration are
required for the move.

Use SQLFluff 4.4.0, with locked and hash-checked dependencies in the tooling
image, for SQLite linting and formatting. One committed configuration governs
local and CI checks. Extract production queries into compile-time embedded SQL
files. Preserve intentionally invalid test fixtures as host-language strings.
Checks cannot connect to application databases and never rewrite source files.
Applied migrations retain their original bytes because SQLx checksums them.

The maintainer approved both stages and their validation directly and requested
one new implementation PR. It includes the previously approved
[foundation runtime](20261018-foundation-runtime-stack.md) in separate
prerequisite commits. This decision records the rationale without requiring a
separate design PR for the already approved changes.

## Consequences

Compose configuration is easy to find, but commands must name its new paths.
SQL gains real source coverage without runtime file loading. Formatting is
explicit and writable only through the format service. SQLFluff validates
syntax and conventions, while database behavior remains the responsibility of
the server's SQLite tests. Tool upgrades require a dependency-lock refresh and
image rebuild. No mail ownership, database schema, or extension behavior changes.
