# Coding standards

These rules apply to the application, static showcase, and repository tooling.
The [foundation decision](../decisions/20261017-thunderbird-first-foundation.md)
selects Rust for the server and TypeScript for the browser client and Thunderbird
extension. The diagnostics server uses Axum/Tokio and SQLx, while the browser
uses ordinary TypeScript ES modules. See
[architecture](../reference/architecture.md) for the accepted direction and
implementation status.

## Naming and structure

Use descriptive English words and properly segmented identifiers. Avoid
single-letter names unless an established language convention requires one.
Use `referenceURI` in existing JavaScript lower-camel identifiers, `ReferenceURI`
for exported PascalCase names, and `reference_uri` in Python. Prefer full words
over unexplained abbreviations, while retaining standard protocol acronyms.

Use lower camel case for JavaScript variables/functions, upper snake case for
Bash variables, and snake case for Python identifiers. Use `mock`, not `fake`,
when naming test doubles. New Bash helpers live at `devbin/raicho_<purpose>.bash`
with underscore-separated purpose words. Python helpers use the same prefix
and `.py` suffix. Document filenames follow
[documentation organisation](../contributing/documentation-organisation.md#naming).

Keep files focused on one concern. Split them by functionality at approximately
150 lines or when they hold multiple concerns, unless stronger existing
conventions apply. Keep search, navigation, and review mapped to one concern.
File locations follow the [repository placement rules](../reference/project-structure.md#placement-rules).

## Source filenames

Use lowercase `snake_case` source filenames across languages, such as
`status_poller.ts` and `count_migrations.sql`. Separate words with one underscore.
Numeric prefixes are allowed. Files directly in `server/migrations/` use a
unique four-digit sequence starting at `0000`, followed by a descriptive
snake_case name, such as `0000_connector_credentials.sql`. Increment the
sequence for each new migration, without using a date. The source naming guard
checks the format and rejects duplicate versions. See the
[migration naming decision](../decisions/20261026-naming-conventions.md#migrations).

The naming guard covers Rust (`.rs`), Python (`.py`, `.pyi`), Bash (`.sh`, `.bash`
and extensionless shell scripts), JavaScript (`.js`, `.mjs`, `.cjs`, `.jsx`),
TypeScript (`.ts`, `.tsx`, `.mts`, `.cts`), SQL (`.sql`), HTML (`.html`), and
CSS (`.css`). Extensions must also be lowercase.

Conventional suffixes are allowed after a snake_case stem: `.test` and `.spec`
for JavaScript/TypeScript, `.d` for TypeScript declarations, `.config` for
JavaScript/TypeScript tool configuration, and `.module` for CSS. Preserve
Python's `__init__` and `__main__` module names, `.eslintrc.js`, `.eslintrc.cjs`,
`.prettierrc.js`, `.prettierrc.cjs`, and `.prettierrc.mjs`. Additional tool-required
exceptions belong in the guard and its tests, rather than a general exemption
for dotted filenames.

The guard checks tracked and non-ignored untracked paths. Tracked names with
source extensions are checked even when missing from the worktree. Extensionless
scripts require a readable shell shebang. Stage a rename to remove its old name
from the index before running it. Dependency/build directories and historical
references use the [tooling exclusions](linting-and-formatting.md#scope-and-enforcement).
Documentation, configuration data, and artwork filenames retain their
existing naming conventions. See the
[decision](../decisions/20261018-source-filename-convention.md) for rationale.

## Directory names

Use ASCII lowercase letters and digits only for every owned directory name
inside the repository, matching `[a-z0-9]+`. Join words without separators,
such as `mailprobe` and `lifecycleprobe`. This includes source, documentation,
and asset directories. Skill directories use kebab-case instead, as the
[skill rules](../contributing/documentation-organisation.md#skills) define.
The exact reserved tool paths `.agents`,
`.github`, and `.github/PULL_REQUEST_TEMPLATE` are exceptions. Their other
descendants follow the normal rule.

The directory guard checks parents of tracked and non-ignored untracked paths,
including tracked paths missing from the worktree. Stage directory renames before
running it so removed names leave the index. Dependency/build directories and
historical references use the [tooling exclusions](linting-and-formatting.md#scope-and-enforcement).
The [directory naming decision](../decisions/20261026-naming-conventions.md#directories)
records the rationale and migration.

## Comments and prose

Default to no comments. Explain only a non-obvious reason, not the code itself,
architecture narration, or roadmap state. Guard headers explain why the check
exists. Do not use em dashes or semicolons in prose. Syntax inside code and
commands is exempt from the prose rule.

## Current language idioms

Use semantic HTML, accessible controls, and the existing CSS/JavaScript style
within each showcase file. Keep demo data in its separate module. Avoid new
runtime dependencies for these static pages. New application framework choices
need a design decision first.

Repository guards are direct Python entry points. Use standard-library APIs for
JSON, file paths, and structured Git process arguments. Do not evaluate
user-controlled text as code. Root and event-path handling follows
[build, test, and generate](../reference/build-test-generate.md#checks-and-formatting).

Bash tooling uses `set -euo pipefail`, braces around parameter expansions, and
upper-snake-case variables. Check commands inside explicit conditionals when
aggregating failures.

Each guard prints `FAIL:` diagnostics to stderr and exits nonzero on failure.
Report actionable messages identifying the path or condition.

Rust uses edition 2024, snake_case functions/modules, and PascalCase types.
Propagate failures with context rather than panicking in application paths.
Keep SQLite operations inside persistence modules and HTTP payloads separate
from database implementation details. Use temporary fixture databases in tests.
Production SQL belongs in `server/queries/*.sql` and is embedded at compile
time with `include_str!`. Keep migration SQL in `server/migrations/` and preserve
the [migration invariants](../reference/runtime.md#sqlite-initialization-and-migrations).
Use the [SQL tooling conventions](linting-and-formatting.md) for style.

Browser TypeScript uses strict checking and explicit `.js` imports for emitted
ES modules. Validate JSON at the boundary, render status with DOM text APIs,
and bound asynchronous polling. Test pure behavior with Node's built-in runner.
Select a UI framework only with the stage that requires it.

## Error messages

Use concise sentences describing the failed operation and useful context.
Follow existing error-format conventions within a subsystem. Never include
account secrets or private message content. General error-handling principles
live in [coding principles](../contributing/coding-principles.md#errors).
