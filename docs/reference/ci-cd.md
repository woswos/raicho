# Continuous integration

[repository-checks.yml](../../.github/workflows/repository-checks.yml) runs on
pushes to `main` and PR activity: opened, synchronized, reopened, edited,
labeled, unlabeled, and ready for review. Body and label edits rerun the guard.
The workflow uses a read-only token and does not retain checkout credentials.

## Jobs

- `lint`: repository integrity, guard regression tests, language linting,
  formatting checks, TypeScript type checking, and runner fixture tests on
  pushes and PRs, including designs. `make lint` also checks protocol generation drift.
- `pr-guards`: PR context checks on PR events only.
- `application-build`: runtime Compose validation and both application images.
- `application-test`: Rust, browser, and extension builds/tests, plus Thunderbird
  process supervision and generated-policy tests.
- `runtime-test`: unattended startup, HTTP isolation, SQLite/profile persistence,
  administrative network isolation and listener closure, and application readiness
  while Thunderbird is stopped, in a disposable project.

There are no coverage, release, publication, or deployment jobs. Runtime tests
use no accounts and remove only their job-specific containers and volumes.

Language jobs build the same pinned tooling image used locally. Runtime jobs
build the application images and use that tooling image for the smoke driver.
Sources remain read-only, with separate cache/temp storage. No formatter writes
or lint fixes run in CI. The hosted runner provides
Docker and Compose, while language tools come from the image. Exact commands
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
Extension packaging regressions also run in `lint` through `lint-repo`.
The Rust workspace and extension application tests exercise the same
[connector contract fixtures](connector-contract.md). No live connector
authentication or heartbeat timing is implied by these source tests.
Credential persistence and CLI tests run in `application-test`, while secret-file
and wrapper regressions run in `lint-repo`. The disposable
[credential runner](build-test-generate.md#credential-persistence) currently runs
locally. Adding the complete connector acceptance suite to CI remains the final
slice of the connector plan.
The separate [extension lifecycle runner](build-test-generate.md#extension-lifecycle)
currently runs locally. Full connector lifecycle coverage in CI is planned for
the connector plan's integration slice.

## Repository integrity

`make lint-repo` checks the AGENTS document references, canonical skills
directory, documentation and source filenames, and skill metadata/example
paths, then runs the guard tests. The
[source naming guard](../coding/linting-and-formatting.md#scope-and-enforcement)
runs in the existing `lint` job and is not bypassed by skip labels.
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
`compose/compose.ci.yaml` override mounts the event JSON read-only at
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

## Labels

| Label | Effect |
| --- | --- |
| `design` | Validates planning-only changes and exempts the reference check. |
| `skip-design-check` | Bypasses the design-link requirement. Does not bypass planning-only enforcement on a `design` PR. |
| `skip-build` | Skips the dedicated application image build job. |
| `skip-test` | Skips application and runtime test jobs. |

The `design` label also skips all three application jobs. Jobs are independent,
so a skipped build does not leave invalid test dependencies. Test jobs still
compile/build their test prerequisites when `skip-build` is present. The labels
do not bypass language linting, guard regression tests, or runner fixtures.

Repository integrity checks never skip because of a label. GitHub labels must
exist before using them. Workflow files do not create labels, enable required
checks, or enforce review approval. These are repository settings to configure
when publication is authorized. PRs can change their own workflow files, so this
is a contributor workflow check rather than a tamper-proof governance boundary.

Future coverage and release checks belong to the
[foundation plan](../planning/active/20261017-thunderbird-first-foundation.md#future-ci-jobs)
and are not part of the current workflow.

See [GitHub events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request)
and [delivery workflow](../contributing/workflow.md) for context.
