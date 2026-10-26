# Version the product from the changelog

- Status: accepted, amended by `20261026-skip-changelog-label`
- Date: 2026-10-18
- Deciders: Raicho maintainer

## Context

Raicho reports `0.1.0` from the Cargo workspace and has no tag, changelog, or
rule for when that number changes. The running diagnostics page already shows
that version. A future Thunderbird extension manifest must use the same
three-part numeric form the extension build accepts, with each component from
0 to 65535 and no leading zeros.

The product needs one changelog, a semantic version chosen from the kind of
change, and a release from `main` only when an operator can notice something.
Major bumps stay a human decision. The release commit and the tag stay separate
from any build that publishes artifacts.

## Decision

Version Raicho from that changelog.

The declared product version is the Cargo workspace package version. Extension
manifests, when they exist, must match it. `CHANGELOG.md` is the release
record. Pull request descriptions can carry the same entries. Added or Removed
entries select the next minor version. Any other entry selects the next patch.
`--major` is the only way to bump the major version, and the first release is
`0.1.0` while no version tag exists.

`devbin/raicho_cut_release.py` calculates that version and, with `--write`,
dates the changelog and stores the version in the manifests and Cargo lockfile.
It does not commit, tag, or push.
GitHub Actions workflows do those steps when `RELEASE_TOKEN` is configured.
A tag push publishes GitHub release notes from the changelog. These workflows
do not publish container images or binaries.

The server reports the declared version and the build commit. Image builds
record `RAICHO_COMMIT`. An unset commit is `unknown`.

## Consequences

One number identifies the server and, later, the packaged extension. The
extension format rules out pre-release suffixes, so development builds keep
the last declared version and distinguish themselves by commit.

Automatic cuts stay idle until a `RELEASE_TOKEN` can push to `main` and push
tags. The `no changelog` label must exist in GitHub before anyone can use it.
Workflow files do not create that label.

Coverage gates and image publication remain future work. A release with no
changelog section fails before notes are published.
