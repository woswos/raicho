# Cache Rust builds and images

- Status: accepted
- Date: 2026-10-26
- Deciders: Barkin Simsek

## Context

A measurement of the build showed that the local Cargo cache worked but held
duplicate copies of many dependencies, and that CI cached nothing. Every job
compiled Rust and built its images from scratch. Different Cargo selections
resolved different dependency features. Clippy used its own target directory. Each
integration test file linked its own binary. The deploy image recompiled every
dependency whenever a source file or the commit changed. SQLx's compile-time
macros built a second copy of SQLite and a large compile-time dependency tree for a
single `migrate!` call.

## Decision

Every debug Cargo command uses `--workspace --all-targets --locked` in the shared
target directory. The protocol generator runs from that directory. Clippy shares it
for the root workspace, while nested workspaces keep their own directory, because
Cargo's artifact hashes ignore a workspace's location. Local builds are incremental.
CI builds are not.

The server's integration tests compile into two binaries. Tests that spawn
processes run apart from the rest, because a child briefly holds the parent's open
files, including SQLite instance locks. Python test modules run in parallel worker
processes.

The server lists its migrations in code and builds the SQLx migrator without the
`macros` feature. This amends the [runtime stack decision](20261018-foundation-runtime-stack.md),
which chose SQLx with that feature. It keeps the bundled SQLite 3.51.3, rather than
Debian's older system library.

The Rust connector decoder no longer runs `jsonschema` on every frame. The generated
types already enforce the schema's types, lengths, patterns, and unknown-field rules,
and the decoder checks the two bounds they miss. `jsonschema` stays a test-only
dependency, in a conformance test over the shared fixtures, which removes its
regular expression and number libraries from the server binary.

The deploy image compiles its Rust dependencies in a layer that depends only on the
manifests and lockfile, against placeholder workspace sources. A later layer
compiles the real sources with `RAICHO_COMMIT`.

CI restores a Cargo cache per job with `actions/cache`. The coverage job also runs
on pushes to `main`, because a pull request can restore caches saved on `main` but
not another pull request's. Runtime images build with Docker's default builder,
whose layer cache stays on the self-hosted runner's Docker host between runs. A
GitHub Actions BuildKit cache was tried and dropped: on that runner it restored
layers at about 284 KiB/s, so a restore took longer than a build. The Make
`build` target is removed. `make images` builds the deliverables, and the test and
lint targets build what they check.

## Consequences

A source edit relinks two test binaries instead of one per file. A new commit
recompiles only the workspace crates in the deploy image. CI jobs reuse compiled
dependencies until `Cargo.lock` or the toolchain changes, or GitHub evicts the cache,
and reuse image layers while the runner's Docker host keeps them.

New server tests are modules of an existing test binary. New migrations need an
entry in the migration list, and a test enforces it. New workspace targets need a
placeholder in the deploy Dockerfile. Nothing sweeps old Cargo artifacts automatically.
`make clean` resets the cache.
