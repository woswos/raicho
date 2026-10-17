# Linting and formatting

## Configured tooling

Run the shared tooling image using the commands in
[build, test, and generate](../reference/build-test-generate.md). The
[code-quality decision](../decisions/20261018-containerized-code-quality.md)
records the selected tools and their boundary.

| Language or check | Configuration |
| --- | --- |
| Repository guards | Five direct Python entry points and standard-library helpers in `devbin/`, with regression tests |
| Bash | `bash -n`, ShellCheck with `.shellcheckrc`, `shfmt -ln bash -i 4 -ci` |
| Python | Ruff lint and format with `pyproject.toml` |
| JavaScript | ESLint recommended rules with `eslint.config.mjs`, Prettier with `.prettierrc.json` |
| TypeScript | typescript-eslint typed rules, Prettier, and `tsc --noEmit` with project configuration |
| Rust | Clippy for Cargo targets, rustfmt with edition 2024 from `rustfmt.toml` |

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

## Scope and enforcement

Check and format commands discover tracked and non-ignored untracked source
through Git. Disposable fixture directories use filesystem discovery. Scope
includes Bash (`.bash`, `.sh`, and shell shebangs), Python (`.py`, `.pyi`),
JavaScript (`.js`, `.mjs`, `.cjs`), TypeScript (`.ts`, `.tsx`, `.mts`, `.cts`),
and Rust (`.rs` and Cargo projects).

Prettier also covers `package.json`, `.prettierrc.json`, `compose.tools.yaml`,
`compose.ci.yaml`, and `.github/workflows/repository-checks.yml`.
Do not broaden it to Markdown, HTML, CSS, SVG, exported previews, historical
references, fonts, or vendor artifacts. Dependency directories, build output,
and generated lockfile formatting are excluded. Preserve the approved artwork
and showcase behavior when applying the source formatting baseline.

Discovery excludes `.git`, `node_modules`, `target`, `dist`, `vendor`,
`__pycache__`, and `assets/brand/references`.

There are no Rust or TypeScript application sources yet. The runners report
that absence explicitly, and `test-tooling` exercises real passing/failing
projects in temporary storage. Once owned sources exist, missing project
configuration or tools must fail. Add manifests and TypeScript configuration
with the first application sources. Fixture success is not evidence of a
working application.

`format-check` never rewrites sources. `format` is an explicit writable command
using the caller's UID/GID. CI runs checks without automatic fixes.

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

GitHub checkout stays at v7.0.1, pinned to
`3d3c42e5aac5ba805825da76410c181273ba90b1`. The `ubuntu-24.04` hosted runner
provides Docker and Compose, not the language-tool versions. Rebuild the tooling
image after changing pins, then run the same check suite locally and in CI.

Validation and commit authorization follow [workflow](../contributing/workflow.md) and
[commit rules](../contributing/git-and-pull-requests.md#commits). Do not install
commit hooks or run formatting automatically in response to a plain commit request.
