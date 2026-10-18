# Containerized foundation runtime

- Status: accepted
- Date: 2026-10-18
- Deciders: project maintainer

## Context

The foundation needs a runnable, persistent deployment before the extension
lifecycle experiment. The reviewed Thunderbird images bundled older application
releases. The maintainer requested an independently maintained image rather than
deriving from either third-party Thunderbird image.

## Decision

Use Axum 0.8.9, Tokio 1.53.3, and tower-http 0.7.1 with the existing Rust toolchain.
Serve a framework-neutral TypeScript diagnostics page compiled with the existing
TypeScript toolchain. Commit Cargo.lock and build with locked dependencies.

Use SQLx 0.9.0 with bundled SQLite, locking libsqlite3-sys 0.37.0 and SQLite
3.51.3. Use one connection, WAL, FULL synchronous mode, foreign keys, and bounded
pool/lock waits. Acquire a separate process lock before initialization because
SQLx's SQLite migration locking is not implemented. Apply transactional migrations
before serving, rejecting incompatible or damaged history. Each migration is
atomic independently. Application tables arrive with their consuming features.

Build our own Thunderbird image from digest-pinned Debian Bookworm slim. Install
the checksum-verified official Thunderbird 153.5.0 ESR archive, an internal X
display, a small window manager, and opt-in noVNC remote administration. Pin the
Debian package snapshot and noVNC release. Disable Thunderbird self-updates.
Both application images run as UID/GID 10001 without a root initialization step.

Initially support Linux amd64. Mozilla's selected release has no Linux ARM64
archive, so the parent distribution's ARM support is not a support claim.
Keep separate named volumes, loopback diagnostics, and an explicit administrative
override. Extension compatibility remains a stage 2 gate.

## Consequences

Contributors need Docker and Compose rather than host language toolchains.
The repository owns Thunderbird packaging, process supervision, dependency
updates, and startup checks. Updates replace images rather than mutable packages
inside running containers. Bind mounts require explicit ownership preparation.

SQLx avoids handwritten async database and migration infrastructure. Its bundle
is not the newest SQLite release, so engine changes need explicit review. Future
backup/restore work must recheck engine fixes and test consistent recovery.
The initial schema stores only migration metadata, not speculative application
tables or mail. No connector, login, remote deployment, or mail workflow is
claimed by stage 1.

See [runtime reference](../reference/runtime.md),
[foundation plan](../planning/active/20261017-thunderbird-first-foundation.md),
[Mozilla ESR artifacts](https://archive.mozilla.org/pub/thunderbird/releases/153.5.0esr/),
[SQLx migrations](https://docs.rs/crate/sqlx-sqlite/0.9.0/source/src/migrate.rs), and
[SQLite releases](https://www.sqlite.org/changes.html).
