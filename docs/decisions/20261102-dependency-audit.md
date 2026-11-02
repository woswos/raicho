# Audit dependencies with OSV-Scanner

- Status: accepted
- Date: 2026-11-02
- Deciders: Barkin Simsek

## Context

Raicho locks its dependencies in three files: `Cargo.lock` for the Rust
workspace, `package-lock.json` for TypeScript and JavaScript tooling, and
`automation/tooling/requirements.txt` for Python tooling. No command checked
them against published security advisories, and `.npmrc` turns off npm's
install-time audit.

Per-ecosystem tools need three installations and give three report formats:
cargo-audit for RustSec, `npm audit`, and pip-audit, which would add its own
hash-pinned Python dependencies. OSV-Scanner is one static binary that reads
all three lockfile formats and queries the OSV database, which aggregates
RustSec, the GitHub advisory database, and PyPI advisories.

## Decision

`make audit` runs OSV-Scanner 2.7.0 in the tooling image against every tracked
lockfile. The Dockerfile downloads the release binary and verifies its SHA-256,
like the typos archive. The scan prints only findings unless `VERBOSE=1` is set,
and it fails when any advisory applies. CI does not run it.

## Consequences

Contributors can check advisories with one command and no host tools. The scan
needs network access to the OSV API, and its result can change without a code
change, which is why it stays out of CI. A new lockfile must be added to the
target, and a tooling test fails until it is. Fixing a reported advisory is a
separate dependency update. A scheduled CI job remains possible later.
