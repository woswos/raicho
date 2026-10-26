# Continuous integration

[repository-checks.yml](../../.github/workflows/repository-checks.yml) runs on
pushes to `main` and PR activity: opened, synchronized, reopened, edited,
labeled, unlabeled, and ready for review. Body and label edits rerun the guard.
The workflow uses a read-only token and does not retain checkout credentials.

## Jobs

- `lint`: repository integrity, every Python unit suite, language linting,
  formatting checks, TypeScript type checking, and runner fixture tests on
  pushes and PRs, including designs.
- `pr-guards`: PR context checks on PR events only, including the changelog
  entry required for user-visible changes.
- `application-build`: runtime and fixture Compose validation and all runtime images.
- `application-test`: Rust and browser builds/tests.
- `runtime-test`: unattended startup, HTTP isolation, SQLite/profile persistence,
  administrative network isolation and listener closure, and application readiness
  while Thunderbird is stopped, in a disposable project.

There are no coverage, image publication, or deployment jobs. Changelog
releases are separate workflows described below. Runtime tests
use no accounts and remove only their job-specific containers and volumes.

Language jobs build the same pinned tooling image used locally. Runtime jobs
build the application images and use that tooling image for the smoke driver.
Thunderbird retains its own runtime image.
Sources remain read-only, with separate cache/temp storage. No formatter writes
or lint fixes run in CI. Jobs run on the
repository's self-hosted runners, labeled `self-hosted`, `Linux`, and `X64`. Each
runner host provides Docker Engine 28 or newer with Compose 2.24 or newer and
Buildx, Git, GNU Make, Bash, `flock`, and `timeout`. The release workflows install
Python 3.13 with `actions/setup-python` and need the GitHub CLI. Language tools come from the image. Runners
keep Docker images and volumes between jobs, so prune them occasionally. Run only
one runner per Docker host, because jobs use fixed image tags, Compose project
names, and Cargo caches. Exact commands
and pins are in [build, test, and generate](build-test-generate.md) and
[linting and formatting](../coding/linting-and-formatting.md).

Rust, TypeScript, and SQL checks cover the application sources. SQL linting and
format checks run in the existing `lint` job through the aggregate Make targets,
including SQL failure/formatting fixtures under `test-tooling`. They require no
database service and run even when application jobs are skipped.
Disposable runner
fixtures still verify discovery and failure behavior independently. Missing
project configuration fails rather than silently skipping application checks.
Automated checks do not claim visual verification of the administrative desktop.
Python automation suites and Thunderbird process supervision tests run through
`test-python`, from component-local `tests/` directories.

## Repository integrity

`make lint-repo` checks the AGENTS document references, directory names,
documentation and source filenames, skill metadata/example
paths, and the declared product version through modules in
`automation/repository/`. `make test-python` runs their policy tests, including
changelog guard regressions, with every other Python unit suite described in the
[command reference](build-test-generate.md#checks-and-formatting). The
[naming guards](../coding/linting-and-formatting.md#scope-and-enforcement)
run in the existing `lint` job and are not bypassed by skip labels.
Documentation checks include tracked and untracked non-ignored
documentation, including tracked paths missing from the worktree. `AGENTS.md`
must `@`-load the working agreement, workflow, key conventions, and
architecture documents, and every Markdown path it cites must be a regular
file. Dated plans must be directly in `docs/planning/active/` or
`docs/planning/done/`. Dated decision records must be directly in
`docs/decisions/`. A missing cited instruction file or malformed configuration
fails the job.

## PR context guards

`make lint-pr` reads PR metadata from GitHub's event JSON as data. It uses explicit
base/head commit hashes, not the synthetic merge commit at `GITHUB_SHA`.
A full checkout supplies those objects, including fork history. The
`automation/tooling/compose.ci.yaml` override mounts the event JSON read-only at
`/tmp/github-event.json`. Body, labels, and commit IDs are parsed as data and
never interpolated into shell commands. The changed-path
comparison uses `base...head`, disables rename detection to inspect both sides
of moves, and includes deletions. Missing or invalid context fails closed.

The description must contain exactly one standalone `Design:` or `Decision:`
line when a reference is required. Fenced examples and HTML comments are ignored.

- `Design: docs/planning/active/YYYYMMDD-slug.md` must name a regular Markdown
  file already present at the base commit. A `done/` path is also valid when that
  path already exists at the base. This verifies prior presence, not human approval.
- `Decision: docs/decisions/YYYYMMDD-slug.md` must name a regular Markdown file
  at the PR head commit. It may be introduced in the same PR.

A design PR can change only dated Markdown files directly in
`docs/planning/active/`. All changed paths must meet that rule. A local run with
no comparison base cannot claim this exemption.

For other PRs, a reference is unnecessary when every changed path is a
regular file whose name ends in `.md`. A symlink, script, or non-Markdown
path is not exempt.

User-visible changes also need a changelog entry in the description or in
`CHANGELOG.md`. The paths and the entry format are in
[versioning](versioning.md). Without a comparison base the local guard skips
that check and says so.

## Labels

| Label | Effect |
| --- | --- |
| `design` | Validates planning-only changes and exempts the reference check. |
| `skip-design-check` | Bypasses the design-link requirement. Does not bypass planning-only enforcement on a `design` PR. |
| `skip-build` | Skips the dedicated application image build job. |
| `skip-test` | Skips application and runtime test jobs. |
| `skip changelog` | Skips the changelog entry check. Does not skip design, build, or test checks. |

The `design` label also skips all three application jobs. Jobs are independent,
so a skipped build does not leave invalid test dependencies. Test jobs still
compile/build their test prerequisites when `skip-build` is present. The labels
do not bypass language linting, guard regression tests, or runner fixtures.

Repository integrity checks never skip because of a label. GitHub labels must
exist before using them. Workflow files do not create labels, enable required
checks, or enforce review approval. These are repository settings to configure
when publication is authorized. PRs can change their own workflow files, so this
is a contributor workflow check rather than a tamper-proof governance boundary.

Future coverage and image-publication checks belong to the
[foundation plan](../planning/active/20261017-thunderbird-first-foundation.md#future-ci-jobs)
and are not part of the current workflow.

## Releases

[auto-release.yml](../../.github/workflows/auto-release.yml) runs on pushes to
`main`. When `RELEASE_TOKEN` is set and the changelog has something to
release, it commits the dated changelog, product version, and updated Cargo
lockfile, and pushes an annotated `v*` tag. Without that token it records that nothing was
released. The token must be allowed to push to `main` and to push tags,
because a push made with the default token does not start another workflow.

[major-release.yml](../../.github/workflows/major-release.yml) is manual. The
confirmation text is `MAJOR`, supplied as data through an environment variable.
The job accepts only dispatches targeting `main` and explicitly checks out `main`.

[release.yml](../../.github/workflows/release.yml) runs on `v*` tags and
publishes that version's changelog section as GitHub release notes. It does
not build or publish images. Publication concurrency is scoped to each tag, so
a newer tag cannot cancel another tag's pending publication. Release behavior
is specified in [versioning](versioning.md).

These workflows do not run on pull requests. A `design` pull request therefore
does not cut a release. The repository-checks workflow stays read-only.

See [GitHub events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request)
and [delivery workflow](../contributing/workflow.md) for context.
