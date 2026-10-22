# Linting and formatting

## Configured tooling

Run the shared tooling image using the commands in
[build, test, and generate](../reference/build-test-generate.md). The
[code-quality decision](../decisions/20261018-containerized-code-quality.md)
records the selected tools and their boundary.
The [Compose and SQL decision](../decisions/20261018-compose-layout-and-sql-quality.md)
extends that tooling to SQLite source.

| Language or check | Configuration |
| --- | --- |
| Repository guards | Direct Python entry points and standard-library helpers in `devbin/`, with regression tests |
| Bash | `bash -n`, ShellCheck with `.shellcheckrc`, `shfmt -ln bash -i 4 -ci` |
| Python | Ruff lint and format with `pyproject.toml` |
| JavaScript | ESLint recommended rules with `eslint.config.mjs`, Prettier with `.prettierrc.json` |
| TypeScript | typescript-eslint typed rules, Prettier, and `tsc --noEmit` with project configuration |
| Rust | Clippy for Cargo targets, rustfmt with edition 2024 from `rustfmt.toml` |
| SQL | SQLFluff lint and format using the root `.sqlfluff` configuration |

Ruff checks `E4`, `E7`, `E9`, `F`, `I`, `UP`, and `B`, targeting Python 3.13.
Its formatter uses 88 columns and single quotes. Prettier also uses single
quotes. ESLint treats showcase scripts as browser classic scripts and its own
configuration as Node code. TypeScript uses project-aware linting without a
fallback project. Pyright and mypy are not configured.

Clippy runs `--workspace --all-targets --locked` with
`CARGO_BUILD_WARNINGS=deny` and a separate temporary target directory per
workspace to prevent cache collisions from hiding failures. It checks Cargo
targets under their active configuration, not
unreferenced `.rs` files or every conditional feature combination. Formatting
checks cover Cargo projects and each discovered owned `.rs` file independently.

SQLFluff uses the SQLite dialect and raw templater, four-space indentation,
88-column lines, uppercase keywords/functions/literals/types, and lowercase
unquoted identifiers. The lint rules cover layout, capitalization, ambiguous
result columns (`AM04`), and NULL comparison (`CV05`). Formatting applies only
SQLFluff's formatting rules. Both commands force the repository configuration,
ignore personal/nested configurations, and fail on parsing errors. Checks do
not connect to a database. SQLFluff syntax checks complement SQLite behavior
tests rather than proving query execution or migration safety.

## Scope and enforcement

`make lint-repo` runs `devbin/raicho_check_source_naming.py` and its regression
tests locally and in CI. It checks the
[source filename convention](coding-standards.md#source-filenames), including
HTML and CSS names without adding them to the formatting scope. Renames are
explicit edits, never formatter fixes.

`devbin/raicho_check_directory_naming.py` enforces the separate
[directory convention](coding-standards.md#directory-names). It also runs under
`make lint-repo`, including regression tests for nested paths, reserved paths,
ignored and missing files, and CLI root selection. It shares Git discovery and
the exclusions below with the source filename guard.

Check and format commands discover tracked and non-ignored untracked source
through Git. Disposable fixture directories use filesystem discovery. Scope
includes Bash (`.bash`, `.sh`, and shell shebangs), Python (`.py`, `.pyi`),
JavaScript (`.js`, `.mjs`, `.cjs`), TypeScript (`.ts`, `.tsx`, `.mts`, `.cts`),
Rust (`.rs` and Cargo projects), and SQL (`.sql`).

Prettier also covers `package.json`, `.prettierrc.json`, `compose/compose.tools.yaml`,
`compose/compose.ci.yaml`, the runtime/admin/test/credential Compose files, browser package and
TypeScript configuration, extension manifest/package/TypeScript configuration,
the extension lifecycle and mail fixture Compose files, separate mail probe
manifest/package/TypeScript configuration, and
`.github/workflows/repository-checks.yml`. The control schema, limits, and shared
protocol fixture JSON files are also included.
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
Only `protocol/typescript/src/validator_generated.js` disables ESLint's generated
variable redeclaration, unused variable/assignment, and unreachable-code rules.
Other JavaScript rules and hand-written contract files retain normal checks.
Regenerate these files instead of editing them. Rust wire types omit `Debug` to
avoid accidental credential formatting. See the [contract reference](../reference/connector-contract.md).

`format-check` never rewrites sources. `format` is an explicit writable command
using the caller's UID/GID. CI runs checks without automatic fixes.
SQL format checks parse and format temporary copies with the original relative
paths, then compare bytes. Missing SQL tools or configuration fail even when no
SQL files exist. An empty valid SQL scope reports an explicit skip. SQL strings
inside Rust or Python are outside SQLFluff's file scope. Production queries live
in `server/queries/`, while intentionally invalid test fixtures remain inline.
Follow the [migration immutability rule](../reference/runtime.md#sqlite-initialization-and-migrations)
before formatting migration files.

## Versions and updates

The [tooling Dockerfile](../../containers/tooling/Dockerfile) pins each source
image by digest. It installs Debian Bookworm support packages from the
`20261018T000000Z` snapshot.

| Tool | Version |
| --- | --- |
| Python | 3.13.16 |
| Node.js | 24.22.0 |
| npm | 11.19.1 |
| Rust, Clippy, rustfmt | 1.99.1 toolchain |
| Ruff | 0.16.8 |
| ShellCheck | 0.11.0 |
| shfmt | 3.14.1 |
| SQLFluff | 4.4.0 |
| websockify (test fixtures) | 0.13.0 |

Python tooling dependencies and their wheel hashes are locked in
`containers/tooling/requirements.txt`, currently for Python 3.13 on Linux amd64.
The image installs them with `pip --require-hashes --only-binary=:all:`.
Refresh this lock inside Docker when upgrading SQLFluff or test dependencies,
review all dependency changes, and rebuild the image. The entrypoint detects a
stale requirements file.
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

The contract uses typify 0.8.0 and schemars 0.8.22 for Rust generation,
jsonschema 0.59.0 for offline runtime validation, and prettyplease 0.3.0 with
syn 3.0.9 for generated syntax. Exact direct dependencies live in `Cargo.toml`,
with the graph locked in `Cargo.lock`. Ajv and esbuild run only during generation,
producing a self-contained extension validator with no runtime compiler.

The production listener enables Axum 0.8.9's WebSocket support, uses futures-util
0.3.34 for socket writes, and getrandom 0.4.3 for session generations.
Socket tests pin tokio-tungstenite 0.29.0, matching
Axum's resolved implementation. The runtime proxy pins Nginx 1.30.6 Alpine by
digest in `containers/gateway/Dockerfile`.

GitHub checkout stays at v7.0.1, pinned to
`3d3c42e5aac5ba805825da76410c181273ba90b1`. The `ubuntu-24.04` hosted runner
provides Docker and Compose, not the language-tool versions. Rebuild the tooling
image after changing pins, then run the same check suite locally and in CI.

Validation and commit authorization follow [workflow](../contributing/workflow.md) and
[commit rules](../contributing/git-and-pull-requests.md#commits). Do not install
commit hooks or run formatting automatically in response to a plain commit request.
