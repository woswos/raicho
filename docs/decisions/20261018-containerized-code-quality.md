# Containerize code quality tools

- Status: accepted
- Date: 2026-10-18
- Deciders: Barkin Simsek

## Context

Contributors and CI need the same checks for the repository guards, the
JavaScript showcase, and the accepted Rust and TypeScript foundation, without
installing each language toolchain on the host.

## Decision

Use one pinned Docker tooling image locally and in GitHub Actions. Select
ShellCheck and shfmt for Bash, Ruff and Ruff format for Python, Clippy and
rustfmt for Rust, and ESLint with typescript-eslint and Prettier for JavaScript
and TypeScript. Keep repository guards and their regression tests in that image.
Use TypeScript's compiler for type checking.

Checks mount sources read-only. Formatting is a separate writable command.
CI checks formatting without rewriting files. Do not add commit hooks, format
documentation, generated assets, or vendor files, or add a Python type checker.

## Consequences

Docker and Compose are the shared tooling prerequisite. Tool versions and
configurations stay with the image and lockfiles.
