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
