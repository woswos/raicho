# Use consistent source filenames

- Status: accepted
- Date: 2026-10-18
- Deciders: Raicho maintainer

## Context

Source files mix hyphenated and underscore-separated names across the browser,
SQL queries, showcase, and tooling. The maintainer requested consistent names
and automated enforcement, scoped to source filenames across languages.

## Decision

Adopt the [source filename convention](../coding/coding-standards.md#source-filenames)
and rename existing violations with their references. A standard-library Python
guard runs through the existing Docker `make lint-repo` path locally and in CI.
Regression tests exercise Git discovery, invalid names, and the documented
exceptions. No new tooling dependency or separate CI job is needed.

## Consequences

Contributors get actionable naming failures before committing and during CI.
Language-specific suffixes and tool-required filenames remain usable. Renaming
source requires updating imports and links. Documentation, artwork, and directory
naming retain their existing conventions. The
[Compose and SQL changes](20261018-compose-layout-and-sql-quality.md) remain
part of the same approved implementation PR.
