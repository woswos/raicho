# Linting and formatting

## Configured tooling

Run the shared tooling image using the commands in
[build, test, and generate](../reference/build-test-generate.md). The
[code-quality decision](../decisions/20261018-containerized-code-quality.md)
records the selected tools and their boundary.
The [Compose and SQL decision](../decisions/20261018-compose-layout-and-sql-quality.md)
extends that tooling to SQLite source, and the
[spell-checking decision](../decisions/20261026-spell-checking.md) adds typos.

| Language or check | Configuration |
| --- | --- |
| Repository guards | Python modules in `automation/repository/`, with package-local regression tests |
| Bash | `bash -n`, ShellCheck with `.shellcheckrc` (braced variables required; SC2236, SC2015, and SC2155 excluded), shfmt with the options in `.shfmt` |
| Python | Ruff lint and format with `pyproject.toml` |
| JavaScript | ESLint recommended rules with `eslint.config.mjs`, Prettier with `.prettierrc.json` |
| TypeScript | typescript-eslint typed rules, Prettier, and `tsc --noEmit` with project configuration |
| Rust | Clippy for Cargo targets, rustfmt with edition 2024 from `rustfmt.toml` |
| SQL | SQLFluff lint and format using the root `.sqlfluff` configuration |
| Spelling | typos with `.typos.toml`, which lists accepted false positives |

Every formatter uses 120-column lines: Ruff's `line-length`, Prettier's
`printWidth`, rustfmt's `max_width`, and SQLFluff's `max_line_length`. The
protocol generator formats its TypeScript output with the same Prettier
configuration. Ruff checks `E4`, `E7`, `E9`, `F`, `I`, `UP`, and `B`, targeting
Python 3.13, and its formatter uses single quotes. Prettier also uses single
quotes. ESLint treats showcase scripts as browser classic scripts and its own
configuration as Node code. TypeScript uses project-aware linting without a
fallback project. Pyright and mypy are not configured.

Clippy runs `--workspace --all-targets --locked` with
`CARGO_BUILD_WARNINGS=deny`. It uses the shared Cargo target directory for the root
workspace and a subdirectory of it for each nested workspace, as the
[build caching decision](../decisions/20261026-build-caching.md) explains. It checks Cargo
targets under their active configuration, not
unreferenced `.rs` files or every conditional feature combination. Formatting
checks cover Cargo projects and each discovered owned `.rs` file independently.

SQLFluff uses the SQLite dialect and raw templater, four-space indentation with
implicit indents allowed, and 120-column lines. Keywords are uppercase, while
functions, literals, types, and unquoted identifiers are lowercase. Quoted
literals use single quotes, and casts use `CAST(... AS ...)`, since SQLite has no
`::` operator. Every SQLFluff rule applies. Formatting applies only SQLFluff's
formatting rules. Both commands force the repository configuration,
ignore personal/nested configurations, and fail on parsing errors. Checks do
not connect to a database. SQLFluff syntax checks complement SQLite behavior
tests rather than proving query execution or migration safety.

## Scope and enforcement

`make lint-repo` runs `automation.repository.check_source_naming` locally and in
CI, and `make test-python` runs its package-local regression tests. It checks the
[source filename convention](coding-standards.md#source-filenames), including
HTML and CSS names without adding them to the formatting scope. Renames are
explicit edits, never formatter fixes.

`automation.repository.check_directory_naming` enforces the separate
[directory convention](coding-standards.md#directory-names). It also runs under
`make lint-repo`. Its regression tests under `make test-python` cover nested
paths, reserved paths, ignored and missing files, and CLI root selection. It shares Git discovery and
the exclusions below with the source filename guard.

Add a new repository guard the same way. Create
`automation/repository/check_<rule>.py` with an optional repository-root
argument, `FAIL:` diagnostics on stderr, and exit code 1 on failure. Write its
tests first in `automation/repository/tests/<rule>_tests.py`, and add the guard
with a failing case to `GUARDS` in `guard_cli_tests.py`. Run it from `lint-repo`
in the Makefile, where `test-python` picks up its tests automatically, state the rule in the [coding standards](coding-standards.md),
describe the guard here, and record a decision.

`automation.repository.check_schema_naming` enforces the
[database naming convention](coding-standards.md#database-names) under
`make lint-repo`. It builds the schema from `server/migrations/` with Python's
`sqlite3` instead of parsing SQL, so it also covers quoted identifiers that
SQLFluff's capitalization rules ignore.

Check and format commands discover tracked and non-ignored untracked source
through Git, so their test fixtures initialize a repository. They reject every
symlink among those files without following it. Scope includes Bash (`.bash`,
`.sh`, and shell shebangs), Python (`.py`, `.pyi`), JavaScript (`.js`, `.mjs`,
`.cjs`), TypeScript (`.ts`, `.tsx`, `.mts`, `.cts`), Rust (`.rs` and Cargo
projects), and SQL (`.sql`).

Prettier also covers every tracked JSON and YAML file, including package, manifest,
and TypeScript configuration, every Compose file, the GitHub workflows, and the
protocol schemas, limits, and fixtures.
Do not broaden it to Markdown, HTML, CSS, SVG, exported previews, historical
references, fonts, or vendor artifacts. Dependency directories, build output,
and generated lockfile formatting are excluded. Preserve the approved artwork
and showcase behavior when applying the source formatting baseline.

Discovery excludes `.git`, `node_modules`, `target`, `dist`, `vendor`,
`__pycache__`, and `assets/brand/references`.

The Rust workspace and browser TypeScript project are checked directly.
`test-tooling` also exercises real passing/failing projects in temporary storage.
Missing project configuration or tools fail. Runner fixture success does not
replace application tests or runtime verification.

Generated contract outputs remain under formatting and generation-drift checks.
ESLint ignores the generated validators, `*validator_generated.js`, entirely.
Hand-written contract files retain normal checks.
Regenerate these files instead of editing them. Rust wire types omit `Debug` to
avoid accidental credential formatting. See the [contract reference](../reference/connector-contract.md).

`format-check` never rewrites sources. `format` is an explicit writable command
using the caller's UID/GID. CI runs checks without automatic fixes. SQL format
checks pass each source to SQLFluff on standard input under its relative path,
parse the formatted result, then compare the result with the source text.
Missing SQL tools or configuration fail even when no SQL files exist. An empty
valid SQL scope reports an explicit skip. SQL strings inside Rust or Python are
outside SQLFluff's file scope. Production queries live in `server/queries/`,
while intentionally invalid test fixtures remain inline. Follow the [migration
immutability rule](../reference/runtime.md#sqlite-initialization-and-migrations)
before formatting migration files.

## Versions and updates

The [tooling Dockerfile](../../automation/tooling/Dockerfile) pins each source
image by digest, and the typos release archive and OSV-Scanner binary by SHA-256. It installs Debian
Bookworm support packages from the `20261018T000000Z` snapshot.

| Tool | Version |
| --- | --- |
| Python | 3.13.16 |
| Node.js | 24.22.0 |
| npm | 11.19.1 |
| Rust, Clippy, rustfmt, LLVM tools | 1.99.1 toolchain |
| Ruff | 0.16.8 |
| ShellCheck | 0.11.0 |
| shfmt | 3.14.1 |
| typos | 1.51.1 |
| OSV-Scanner | 2.7.0 |
| SQLFluff | 4.4.0 |
| coverage.py | 7.16.2 |
| diff-cover | 10.6.0 |
| websockify (test fixtures) | 0.13.0 |

Python tooling dependencies and their wheel hashes are locked in
`automation/tooling/requirements.txt`, currently for Python 3.13 on Linux amd64.
Its first lines set `--only-binary=:all:` and `--require-hashes`, so the image installs it with a plain
`pip install -r`. Keep those lines when refreshing the lock.
Refresh this lock inside Docker when upgrading SQLFluff, coverage, or test dependencies,
review all dependency changes, and rebuild the image. The entrypoint at
`automation/tooling/entrypoint.bash` detects a stale requirements
file.
The [websockify release](https://pypi.org/project/websockify/0.13.0/) supplies
the WebSocket fixture server. Thunderbird's optional desktop support retains its
Debian package independently.

JavaScript tools use exact versions in `package.json` and resolved dependencies
in `package-lock.json`:

| Package | Version |
| --- | --- |
| ESLint | 10.13.0 |
| `@eslint/js` | 10.0.1 |
| typescript-eslint | 8.71.2 |
| Prettier | 3.9.10 |
| eslint-config-prettier | 10.1.8 |
| globals | 17.13.0 |
| TypeScript | 6.0.3 |
| Ajv | 8.20.0 |
| json-schema-to-typescript | 16.0.0 |
| esbuild | 0.28.2 |

An `overrides` entry in `package.json` pins minimatch 11.0.3. ESLint,
`@eslint/config-array`, and typescript-eslint still require minimatch 10, and
GHSA-g3hv-75wg-m249 affects every 10.x release. Remove the entry once their
releases accept minimatch 11.

The contract uses typify 0.8.0 for Rust generation,
jsonschema 0.59.0 in tests that check the decoders and status documents against the
schemas, and prettyplease 0.3.0 with
syn 3.0.9 for generated syntax. Exact direct dependencies live in `Cargo.toml`,
with the graph locked in `Cargo.lock`. Ajv and esbuild run only during generation,
producing a self-contained extension validator with no runtime compiler.

The public listener uses Axum 0.8.9 without its WebSocket support. The connector
listener accepts WebSockets with tokio-tungstenite 0.29.0, which its socket tests
also use, futures-util 0.3.34 for socket writes, and getrandom 0.4.3 for session
generations. The runtime proxy pins Nginx 1.30.6 Alpine by
digest in `deploy/gateway/Dockerfile`.

GitHub checkout stays at v7.0.1, pinned to
`3d3c42e5aac5ba805825da76410c181273ba90b1`, and setup-python at
v7.1.0, pinned to `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`. The self-hosted
runners provide Docker and Compose, not the language-tool versions. Rebuild the tooling
image after changing pins, then run the same check suite locally and in CI.

Validation and commit authorization follow [workflow](../contributing/workflow.md) and
[commit rules](../contributing/git-and-pull-requests.md#commits). Do not install
commit hooks or run formatting automatically in response to a plain commit request.
