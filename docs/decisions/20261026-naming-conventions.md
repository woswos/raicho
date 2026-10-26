# Naming conventions

- Status: accepted
- Date: 2026-10-26
- Deciders: Barkin Simsek

## Context

The [source filename decision](20261018-source-filename-convention.md) gave files a
checked convention, but other names had none. Directory names mixed underscores,
hyphens, and uppercase tool paths. Helper files repeated the project and directory
names, as in a `raicho_` prefix inside `automation/repository/`. Migrations used
timestamps where short ordered names suffice. SQLFluff requires lowercase unquoted
identifiers, yet accepts names such as `accountpreferences` or `double__underscore`
and skips quoted names entirely. Skill names are typed as commands and already
used kebab-case.

## Decision

The [coding standards](../coding/coding-standards.md) define each rule below
except the skill rule, which
[documentation organisation](../contributing/documentation-organisation.md#skills)
defines. The source filename decision continues to govern filenames.

### Helper files

Name helper scripts, modules, and tests after their role within their directory,
without the project prefix or the directory name, as in
`automation/repository/check_pr.py`, `automation/quality/sql.py`, and
`extension/build.mjs`. Test discovery selects `*_tests.py` and
`*tooling_checks.py`.

### Directories

Owned directory names use only lowercase ASCII letters and digits, joined without
separators, such as `mailprobe`. The exact reserved tool paths `.agents`,
`.github`, and `.github/PULL_REQUEST_TEMPLATE` are exceptions, and skill
directories follow the skill rule below.
`automation.repository.check_directory_naming` runs under `make lint-repo`, with
the source filename guard's Git discovery and exclusions.

### Skills

Skill directories directly under `.agents/skills/` use lowercase kebab-case:
letters and digits in words separated by one hyphen, such as `write-plan-doc`. A
skill's frontmatter `name` equals its directory, and scaffolding skills start with
`add-`. `automation.repository.check_skills` enforces the rule under
`make lint-repo`, and the directory guard applies the same pattern to those
directories.

### Migrations

Files in `server/migrations/` use a unique four-digit sequence starting at `0000`,
followed by a snake_case name, such as `0000_connector_credentials.sql`. The source
naming guard checks the format and rejects duplicate versions.

### Database identifiers

Tables, columns, indexes, views, and triggers use `snake_case`.
`automation.repository.check_schema_naming` runs under `make lint-repo`. It applies
`server/migrations/` in order to an in-memory SQLite database with Python's
`sqlite3`, checks each name a migration introduces, and reports the migration
responsible. A migration that fails to apply also fails the guard.

## Consequences

Paths read without repetition, and module names follow package structure. Generic
names such as `checks.py` appear in several packages, so imports stay
package-qualified. Contributors stage renames before running the guards, because
missing tracked paths remain checked.

Migration order is visible without a date prefix, and concurrent changes must
coordinate their sequence numbers. Applied migrations keep the
[runtime immutability rules](../reference/runtime.md#sqlite-initialization-and-migrations).
The schema rule covers what SQLite actually builds, including quoted names and
columns added later by `ALTER TABLE`, without a SQL parser. Migrations must stay
within features that both the tooling image's SQLite and the bundled SQLx build
support. Query result aliases are outside the rule because queries create no schema.
