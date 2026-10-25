# Versioning

Raicho has one product version. The changelog decides when it changes, and a
tag named `vMAJOR.MINOR.PATCH` is a release. The
[versioning decision](../decisions/20261018-product-versioning.md) records why.

## See also

- [Git and pull requests](../contributing/git-and-pull-requests.md) covers the
  changelog text expected in a pull request.
- [Continuous integration](ci-cd.md) covers the release workflows and the
  `no changelog` label.
- [Runtime](runtime.md) covers the status fields and `RAICHO_COMMIT`.
- [Build, test, and generate](build-test-generate.md) covers the local commands.

## Principles

The declared version lives in the Cargo workspace package version. Every
tracked `extension/**/manifest.json` outside `tests/` must match it. Each
component is an integer from 0 to 65535 with no leading zeros, because that is
what a Thunderbird extension manifest can store.

`0.1.0` is the current declared version. It is not a release until a `v0.1.0`
tag exists. With no version tags, the first cut is `0.1.0`.

## Changelog entries

`CHANGELOG.md` follows Keep a Changelog. Entries wait under `## [Unreleased]`
until a release dates them.

A pull request can put the same entries in a `## Changelog` section of its
description. Use one of these headings: Added, Changed, Deprecated, Removed,
Fixed, Security. A bullet under that heading becomes the release note, with
the pull request number appended when the release is cut. HTML comments,
a heading that lists several kinds separated by `|`, and a bullet that starts
with `TODO:` are ignored.

Anything an operator can notice needs an entry in one of those two places.
That includes the server, its SQL, the diagnostics page, production extension
manifests and source, production protocol implementations in `protocol/rust/src/`
and `protocol/typescript/src/`, gateway runtime configuration, and the Raicho,
Thunderbird, and gateway image recipes, excluding tests. Documentation, repository
tooling, and tests do not need an entry. The mail probe under
`extension/mailprobe/` is a test artifact and is exempt, including its manifest
and source.
The `no changelog` label skips the check when a change is genuinely invisible.
Any update to `CHANGELOG.md` in the same pull request also satisfies the check.

Write `Unreleased` entries against the last release, not the branch history.
Describe what an operator gains, loses, or must do differently. Do not record
moves, renames, or refactors that happen entirely within the pull request,
because no release ever contained the earlier state. The kinds chosen also set
the version bump, so a feature listed only under Changed ships as a patch.

Added or Removed selects the next minor version. Every other kind selects the
next patch. A major bump is never inferred. Ask for it with
`python3 -B -m automation.release.cut_release --major` or the major-release
workflow, which requires the confirmation text `MAJOR` and must be dispatched on
`main`.

## Cutting a release

The cutter only reads the repository and rewrites files. Committing, tagging,
and pushing stay outside it, so a dry run is safe. Run these module commands from
the repository root:

```bash
python3 -B -m automation.release.cut_release
python3 -B -m automation.release.cut_release --write
```

`--write` dates `CHANGELOG.md` and stores the new version in `Cargo.toml`,
`Cargo.lock`, and any extension manifests. It leaves the changes uncommitted.
On a push to `main`, the auto-release workflow does the same thing and then
commits, tags, and pushes, but only when `RELEASE_TOKEN` is set. The release commit and tag
are pushed atomically: if either ref is rejected, neither advances. Without
that token the workflow reports that nothing was released.

The tag push runs the release workflow, which publishes the matching changelog
section as GitHub release notes. It does not build or publish images. Pushing
a `v*` tag by hand uses that same notes path.

Pull request descriptions are read only when `GITHUB_REPOSITORY` and a token
are present and `gh` is installed. A local dry run otherwise uses only the
Unreleased section, and it says so. When collecting descriptions, an API error
or incomplete metadata stops the cut before release files are changed. An HTTP
404 skips a commit reference that does not identify a pull request. Each response
provides both the description and labels, so a failed label read cannot silently
ignore `no changelog`.

```bash
python3 -B -m automation.release.notes 0.1.0
```

That command prints one dated section and fails when the section is missing.

## Builds

The diagnostics status reports `version` from the declared product version and
`commit` from `RAICHO_COMMIT`. Compose passes that argument into the server
image. Leave it unset and the commit is `unknown`, which the page shows as the
version alone. Set it to the full git commit to record the build:

```bash
RAICHO_COMMIT="$(git rev-parse HEAD)" docker compose -f compose/compose.yaml build
```

The commit text must fit in 80 characters, which a full git object name does.
The page rejects a longer value.
