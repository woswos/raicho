# Check spelling with typos

- Status: accepted
- Date: 2026-10-26
- Deciders: Barkin Simsek

## Context

Misspellings in prose, identifiers, and file names reach review because no
check covers them. The [containerized code quality](20261018-containerized-code-quality.md)
tooling runs every other linter in one image, locally and in CI.

## Decision

Use [typos](https://github.com/crate-ci/typos) 1.51.1. Its project publishes no
container image, so the tooling image installs the x86-64 Linux release archive
verified by SHA-256. `lint-spelling` checks the quality file scope as part of
`make lint`, and `format-spelling` applies typos' corrections. `make format`
does not run it, because a correction changes words in code and prose and needs
its own review. `.typos.toml` is the only configuration and lists accepted false
positives. The default `en` locale accepts both American and British spellings.

## Consequences

Common misspellings fail CI. typos flags only known misspellings, so unfamiliar
words pass without a project dictionary. Upgrades change the version and the
archive digest together. The tooling image stays x86-64 only, like the Python
dependency lock.
