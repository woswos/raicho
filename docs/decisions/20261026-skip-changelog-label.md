# Rename the changelog skip label

- Status: accepted
- Date: 2026-10-26
- Deciders: Barkin Simsek

## Context

The [product versioning decision](20261018-product-versioning.md) lets a pull
request skip the changelog entry check with a `no changelog` label. That name
reads as a statement about the pull request rather than an instruction to the
guard. The other labels that turn checks off, `skip-design-check`, `skip-build`,
and `skip-test`, already use the `skip-` prefix.

## Decision

The label is named `skip-changelog`. The pull request guard and release-note
collection recognize only that name. The GitHub label is renamed rather than
recreated, so pull requests that carried it keep it.

## Consequences

A pull request labeled with the old name no longer skips the check. The rest of
the product versioning decision is unchanged.
