# Repository layout

- Status: accepted
- Date: 2026-10-26
- Deciders: Barkin Simsek

## Context

The repository holds a Rust server, a TypeScript page and extension, shared
protocol code, deployed service configuration, a mail API probe, and automation
in several languages. Grouping files by type, such as image recipes, runtime code,
and Compose files in separate top-level trees, splits one service change across
unrelated directories. A flat helper directory mixed commands, support modules,
tests, operational helpers, and generation. Helpers written in a language chosen
by history ran in the wrong image. Python fixture servers need tools that
production images must not carry, and nothing measured whether changes were tested.

## Decision

### Components

Give each deployed service one directory under `deploy/`: `raicho/`, `gateway/`,
`thunderbird/`, and `credentials/`. Each holds its Dockerfile, its
`Dockerfile.dockerignore`, runtime code, configuration, and tests. `credentials/`
builds no image and drives one-off containers from the server image. Build filters
select explicit inputs from the owning components.

Keep the base `compose.yaml` at the repository root, with the operator overlays
`compose.admin.yaml` and `compose.credentials.yaml` beside it. Test overlays live
with the drivers that use them, as `automation/acceptance/runtime/compose.test.yaml`
and `automation/acceptance/connector/compose.upgrade.yaml`. Compose resolves
overlay paths from the first file, so those overlays use repository-relative paths.

The mail API probe is the top-level `mailprobe/` component, with its extension
sources, fixtures, runner, Compose files, and tests. It reuses `extension/build.mjs`
and the production configuration parser. The web builder lives in `web/`, the
extension packager in `extension/`, and the server's command-line entry point in
`server/src/cli.rs`.

### Automation

Shared automation lives in `automation/` packages by responsibility: repository
guards, language quality, cross-component builds and coverage, releases,
cross-service acceptance for the connector, credentials, and runtime, the tooling
image, and shared test fixtures. Protocol generation belongs to
`protocol/generator/`. Make is the developer interface, with the verbs `build`,
`test`, `lint`, `format`, `generate`, and `coverage` over finer component targets.
On the host it builds the tooling image and runs each target inside it, using the
writable service with the caller's UID and GID for targets that change files.
Inside the image it invokes Python modules from the repository root with
`python3 -B -m`, and Bash or JavaScript entry points by path, without thin
compatibility wrappers. The
[project structure reference](../reference/project-structure.md) owns the current
map.

### Tests

Tests live in the owning component's or package's `tests/` directory. Python
fixture and runtime modules are packages. The Thunderbird runtime uses relative
imports and runs as `python3 -m thunderbird.runtime` from `/opt/raicho/thunderbird/`,
and mail probe modules import `mailprobe.tests` packages. `make test-python`
discovers every `*_tests.py` from the repository root. The connector acceptance
driver owns the installed-XPI inspector.

npm workspaces for the TypeScript packages were rejected. The tooling image
installs `node_modules` in `/opt/quality` and mounts sources read-only at
`/workspace`, so package specifiers cannot resolve from sources. The XPI also ships
unbundled `tsc` output, which must keep relative imports.

### Tooling image

One development image in `automation/tooling/` runs every check locally and in CI.
It also packages the Python mocks and drivers from component `tests/` directories
with their hash-locked dependencies, for fixture unit tests, mock services, and
the mail test extension build. Separate containers remain where tests need
independent processes or failure injection. Mail compatibility uses the normal
Thunderbird runtime image with read-only mounts for the test extension and profile
setup, and GreenMail's pinned upstream image.

### Helper languages

Token-file management and the live connection check are the `raicho-server
connector files` and `raicho-server connector wait` subcommands. One Rust
validator serves both the token reader and the rotation state machine, and the
credential services run from the server image. The extension packager is Node,
beside the Node web builder, and writes a deterministic uncompressed archive. Host
orchestration stays in Bash. Repository guards, quality and release tooling, and
acceptance drivers stay in Python inside the tooling image.

### Patch coverage

Coverage runs in the tooling image for the suites the source checks run. Rust uses
`-C instrument-coverage` with the toolchain's `llvm-tools` component. TypeScript
uses Node's built-in coverage on source-mapped test builds, so lines map to the
`.ts` sources while the XPI stays free of maps. Python uses coverage.py with its
subprocess patch, mapping guard copies in temporary repositories back to
`automation/`. Each produces lcov, and `make coverage` prints the merged result.

`make check-patch-coverage` runs diff-cover, already installed with SQLFluff, over
those reports against the PR base. It fails below 90% of changed, measured lines.
Tests, generated files, dependencies, acceptance drivers, and the mail probe are
not measured. A PR-only CI job runs the gate, skipped by `design`, `skip-test`, or
`skip-coverage-check`.

## Consequences

`docker compose up` works from the repository root without `-f`, and a change to
one service touches one directory. Component builds and tests sit beside the code
they exercise. Production images and the XPI contain only shipped sources, and
fixture changes require a tooling image rebuild. One command runs every Python
suite, although every directory on a test's import path needs an `__init__.py`.
Python module commands need the repository root on their import path, which Make
provides.

Credential operations need only the runtime images, and token checks cannot drift
between languages. The server gains a direct `rustix` dependency for
directory-relative file operations and a minimal HTTP/1.0 status request. Coverage
gaps in changed code fail before review. The gate cannot see a TypeScript module
that no test imports, such as the entry points, and does not enforce branch
coverage. The coverage job rebuilds the Rust workspace with instrumentation.

This replaces the Compose location in
[Compose layout and SQL quality](20261018-compose-layout-and-sql-quality.md), whose
SQL decisions stand.
