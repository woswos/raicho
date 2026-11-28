# Continuous integration

[repository-checks.yml](../../.github/workflows/repository-checks.yml) runs on
pushes to `main` and when a PR is opened, synchronized, reopened, or marked ready
for review.
[pull-request-guards.yml](../../.github/workflows/pull-request-guards.yml) runs the
PR guard on the same PR events and again when the description or labels change or
the PR returns to draft, so those edits rerun only the guard. Both workflows use a read-only
token and do not retain checkout credentials. A newer run of either workflow for the
same pull request cancels its older one, while runs for pushes to `main` and the
release workflows always finish.

## Jobs

- `changes`: reports whether a PR changes anything other than Markdown files. The
  jobs below `pr-guards` in this list need its answer. Pushes to `main` always count as code.
- `lint`: repository integrity, every Python unit suite, language linting,
  formatting checks, TypeScript type checking, and runner fixture tests on
  pushes and PRs, including designs. `make lint` also checks protocol generation drift.
  It first validates every runtime and fixture Compose configuration.
- `pr-guards`, in `pull-request-guards.yml`: PR context checks, including the
  changelog entry required for user-visible changes.
- `application-test`: the `test-server`, `test-web`, `test-extension`, `test-mailprobe`,
  and `test-protocol` suites. `lint` runs the Python suites, so this job leaves them out.
- `runtime-test`: builds all runtime images, then checks unattended startup, HTTP isolation, SQLite/profile persistence,
  administrative network isolation and listener closure, and application readiness
  while Thunderbird is stopped, in a disposable project.
- `connector-test`: `make acceptance-connector`.
  PRs set `RAICHO_IDLE_SECONDS=120`, so they observe two idle minutes. Pushes to
  `main` observe the full ten.
- `credentials-test`: `make acceptance-credentials`. It runs beside `connector-test`,
  because both spend most of their time waiting for production heartbeat intervals.
  The [acceptance scope](connector-acceptance.md#scope) lists what each verifies.
- `compatibility-test`: `make acceptance-mail`.
- `coverage`: on PRs, `make check-patch-coverage` against the PR base. It
  fails when fewer than 90 percent of changed, measured lines are covered. On
  pushes to `main` it runs `make coverage` instead, which saves the coverage
  build's Cargo cache for later PRs.

The acceptance jobs run `make acceptance-runtime`, `make acceptance-connector` and
`make acceptance-credentials`, and `make acceptance-mail`, each under `setsid`.
There are no image publication or deployment jobs. Changelog
releases are separate workflows described below. Runtime tests
use no accounts and remove only their job-specific resources, as
[acceptance cleanup](#acceptance-cleanup) describes.

Language jobs build the same pinned tooling image used locally. Runtime jobs
build the application images and use that tooling image for the smoke driver.
Compatibility runners also use it for Python mock services, fixture unit tests,
and the mail test extension build. Thunderbird and GreenMail retain their own
runtime images. Sources remain read-only, with separate cache/temp storage. No
formatter writes or lint fixes run in CI. Jobs run on GitHub-hosted
`ubuntu-24.04` runners, which provide Docker Engine with Compose and Buildx, Git,
GNU Make, Bash, `flock`, `setsid`, `timeout`, and the GitHub CLI. The release
workflows and the PR guard install Python 3.13 with `actions/setup-python`.
Other language tools come from the image. Every job starts on a fresh machine,
so no image, volume, or Cargo artifact survives on the runner between jobs. Jobs
keep bind-mounted files in the runner's temporary directory. Exact
commands and pins are in [build, test, and generate](build-test-generate.md) and
[linting and formatting](../coding/linting-and-formatting.md).

Rust, TypeScript, and SQL checks cover the application sources. SQL linting and
format checks run in the existing `lint` job through the aggregate Make targets,
including SQL failure/formatting fixtures under `test-tooling`. They require no
database service and run even when application jobs are skipped.
Disposable runner
fixtures still verify discovery and failure behavior independently. Missing
project configuration fails rather than silently skipping application checks.
Automated checks do not claim visual verification of the administrative desktop.
Extension packaging and fixture regressions also run in `lint` through `test-python`.
The Rust workspace and extension application tests exercise the same
[connector contract fixtures](connector-contract.md). Source tests also exercise
authentication, session replacement, heartbeat timeouts, extension retries, and
diagnostics.
Rust credential persistence and CLI tests run in `application-test`. Python
automation suites, extension packaging, XPI inspection, mail probe fixture
regressions, secret-file/wrapper verification, Thunderbird process supervision and
generated-policy tests, and protocol generation regressions run through
`test-python`, from component-local `tests/` directories.
The [credential](build-test-generate.md#credential-persistence),
[production connector](build-test-generate.md#production-connector), and
[mail compatibility](build-test-generate.md#mail-api-compatibility) runners use
the same commands locally and in their dedicated jobs. Each owns its disposable
project and traps exit, including failures, to remove its resources. A cancelled
job never reaches those traps, so its final step removes them instead.
The connector job allows 60 minutes, and credentials and compatibility allow 45 minutes, for cold
builds and runtime checks.
The [compatibility matrix](mail-api-compatibility.md#running-the-experiment) lists
the mail checks that stay manual. See [acceptance evidence](connector-acceptance.md)
for scope and limits.

## Acceptance cleanup

A cancelled or timed-out job signals only the entry shell of the running step,
so an acceptance runner's own exit trap may never run. Each acceptance step runs
its Make target under `setsid`. Before creating any Docker resource, every
runner appends its process group and that group leader's start time, its own
process ID and start time, its Compose project, and any state directory to the
file named by `RAICHO_ACCEPTANCE_RECORD`, which the jobs keep in the runner's
temporary directory. Local runs set no record.

The last step of each acceptance job runs
[remove_recorded_projects.bash](../../automation/acceptance/remove_recorded_projects.bash)
with `if: always()`. For each entry it kills the recorded process group only
while its leader or runner still runs in that group with its recorded start
time, then removes the containers, volumes, and networks with the project's
Compose label, the images named after the project, and the state directory.
Containers, volumes, and networks that runners create outside Compose carry the
same label. The step refuses entries outside the disposable project and state
directory patterns and fails when anything remains. Locally, `make clean`
removes interrupted acceptance projects. The [cancel cleanup
decision](../decisions/20261101-acceptance-cleanup-after-cancel.md) and its
[labelling amendment](../decisions/20261102-label-acceptance-containers.md)
explain the design.

## Caching

The [build caching decision](../decisions/20261026-build-caching.md) and its
[hosted runner amendment](../decisions/20261126-github-hosted-runners.md) record why CI caches as it does.

Every image-building job creates a BuildKit container builder with
`docker/setup-buildx-action` and makes it the default. `docker/bake-action` then
builds the tooling image, and in the acceptance jobs the application images, with
the GitHub Actions cache as layer source and destination. Each image has its own
cache scope, `tooling`, `raicho`, `gateway`, or `thunderbird`, because an export
replaces whatever its scope held. All jobs share those scopes. The later Compose and `docker build`
commands run unchanged against the same builder, so they reuse its warm layers. The
builder loads every image into Docker's image store.

`lint`, `application-test`, and `coverage` restore a Cargo cache with
`actions/cache`, keyed by job, `Cargo.lock`, and `rust-toolchain.toml`, into
`raicho-cache` under the runner's temporary directory. Their Make steps set
`RAICHO_CACHE_DIRECTORY` to that folder, so Make binds it at `/cache` through
`automation/tooling/compose.cache.yaml`. The other jobs use the named volume. CI
turns off incremental compilation. Every job that restores a Cargo cache also runs
on pushes to `main`, where `coverage` builds only when no cache matches its key.

GitHub keeps about 10 GB of caches per repository, shared by the Cargo caches and
the image layers, and evicts the least recently used, so a run after eviction
rebuilds cold and saves again.

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

The guard reads PR metadata from GitHub's event JSON as data. It uses explicit
base/head commit hashes, not the synthetic merge commit at `GITHUB_SHA`.
A full checkout supplies those objects, including fork history. The job runs
`python3 -B -m automation.repository.check_pr` with the runner's Python 3.13, because
the guard needs only Python and Git and a tooling image build would dominate its
runtime. `make lint-pr` runs the same module in the tooling image. Body, labels, and commit IDs are parsed as data and
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

## Automated review

CodeRabbit and Kilo review pull requests outside CI. `.coderabbit.yaml` turns on
CodeRabbit approvals (`reviews.auto_approvals.enabled`,
which replaces the deprecated `request_changes_workflow`). CodeRabbit then
requests changes for blocking findings and approves once it has reviewed the
latest commit, its threads are resolved, and its checks pass. A top-level `@coderabbitai approve` comment also
approves, including from the pull request author. Either approval satisfies the
one approving review that `main` requires. `main` dismisses approvals when new
commits are pushed, so that approval always covers the latest commit. CodeRabbit's Ruff is off because
CodeRabbit runs a newer Ruff than the `required-version` pin in `pyproject.toml`
allows, so it fails without results. The `lint` job runs Ruff at the pinned
version. Its other checks keep their defaults.

## Labels

| Label | Effect |
| --- | --- |
| `design` | Validates planning-only changes and exempts the reference check. |
| `skip-design-check` | Bypasses the design-link requirement. Does not bypass planning-only enforcement on a `design` PR. |
| `skip-test` | Skips application, runtime, connector, credentials, compatibility, and coverage jobs. |
| `skip-coverage-check` | Skips only the coverage job. |
| `skip-changelog` | Skips the changelog entry check. Does not skip design, build, or test checks. |

## Skipped jobs

- A draft PR runs `changes`, `lint`, `pr-guards`, and `application-test`. It skips the
  four acceptance jobs and `coverage`. Marking the PR ready for review starts a full run.
- A PR that changes only files whose names end in `.md` runs `changes`, `lint`, and
  `pr-guards`. This matches the guard's documentation exemption.
- Pushes to `main` run every job, so a merged change is always fully checked.

Label changes and a change of the PR's base branch rerun only the guard. A label that
skips or restores other jobs takes effect on the next push. After a retarget, the
other checks run against the new base when a commit is pushed or the PR is closed and
reopened; re-running an earlier run reuses its original merge commit.

The `design` label also skips all five application jobs and the coverage job. Each
test job builds its own prerequisites. The labels
do not bypass language linting, guard regression tests, or runner fixtures.

Repository integrity checks never skip because of a label. GitHub labels must
exist before using them. Workflow files do not create labels, enable required
checks, or enforce review approval. These are repository settings to configure
when publication is authorized. PRs can change their own workflow files, so this
is a contributor workflow check rather than a tamper-proof governance boundary.

Future image-publication checks belong to the
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
