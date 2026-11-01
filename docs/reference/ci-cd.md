# Continuous integration

[repository-checks.yml](../../.github/workflows/repository-checks.yml) runs on
pushes to `main` and when a PR is opened, synchronized, or reopened.
[pull-request-guards.yml](../../.github/workflows/pull-request-guards.yml) runs the
PR guard on the same PR events and again when the description, labels, or draft
state change, so those edits rerun only the guard. Both workflows use a read-only
token and do not retain checkout credentials. A newer run of either workflow for the
same pull request cancels its older one, while runs for pushes to `main` and the
release workflows always finish.

## Jobs

- `lint`: repository integrity, every Python unit suite, language linting,
  formatting checks, TypeScript type checking, and runner fixture tests on
  pushes and PRs, including designs. `make lint` also checks protocol generation drift.
- `pr-guards`, in `pull-request-guards.yml`: PR context checks, including the
  changelog entry required for user-visible changes.
- `application-build`: runtime and fixture Compose validation and all runtime images.
- `application-test`: `make test`, which builds and tests the Rust, browser,
  extension, mail probe, and shared protocol sources and reruns the Python suites.
- `runtime-test`: unattended startup, HTTP isolation, SQLite/profile persistence,
  administrative network isolation and listener closure, and application readiness
  while Thunderbird is stopped, in a disposable project.
- `connector-test`: `make acceptance-connector`, then `make acceptance-credentials`.
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
runtime images.
Sources remain read-only, with separate cache/temp storage. No formatter writes
or lint fixes run in CI. Jobs run on the
repository's self-hosted runners, labeled `self-hosted`, `Linux`, and `X64`. Each
runner host provides Docker Engine 28 or newer with Compose 2.24 or newer and
Buildx, Git, GNU Make, Bash, `flock`, `setsid`, and `timeout`. The release workflows install
Python 3.13 with `actions/setup-python` and need the GitHub CLI. Language tools come from the image. Runners
keep Docker images and volumes between jobs, so prune them occasionally. Run only
one runner per Docker host, because jobs use fixed image tags, Compose project
names, and Cargo caches. A runner in a container shares only its work directory
with the Docker host, at the same path, so jobs keep bind-mounted files in the
runner's temporary directory. Exact commands
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
The connector job allows 60 minutes and compatibility allows 45 minutes for cold
builds and runtime checks. They have no dependencies on the optional build job.
The [compatibility matrix](mail-api-compatibility.md#running-the-experiment) lists
the mail checks that stay manual. See [acceptance evidence](connector-acceptance.md)
for scope and limits.

## Acceptance cleanup

When GitHub cancels a run or a job times out, the runner signals only the entry
shell of the running step. That shell exits, but the acceptance runner below it
receives no signal and keeps running until the job ends, so its exit trap never
removes its deployment. Each acceptance step therefore starts its Make target
under `setsid`, which puts the runner and its Docker commands in their own
process group. When `RAICHO_ACCEPTANCE_RECORD` names a file, every runner
sources [project_record.bash](../../automation/acceptance/project_record.bash)
and appends its process group, the start time of that group's leader, its own
process ID and start time, its Compose project, and any state directory to that
file before it creates any Docker resource. The jobs keep the record in the
runner's temporary directory, which the runner empties at the start of each job.
Local runs set no record.

The last step of each acceptance job runs
[remove_recorded_projects.bash](../../automation/acceptance/remove_recorded_projects.bash)
with `if: always()`, which GitHub also runs after a cancellation. For each entry
whose group leader or runner is still running in the recorded group with its
recorded start time, it kills the process group, so the runner cannot recreate
anything. Checking the runner as well covers a leader that was killed on its
own. A group with neither left is not killed, because Linux can reuse its ID.
The step then removes the containers attached to the project's networks or
volumes, the containers, volumes, and networks with the project's exact Compose
label, and any remaining volumes and networks whose names start with the
`<project>_` prefix that Compose gives them. That prefix also finds a volume
that a fixture container created before Compose did, which has no project label.
It then removes images in the repository named after the project, and the state
directory. It fails when any of them remains. It refuses an entry that names its
own process group, a project outside the disposable
`raicho-<suite>-<timestamp>-<number>` pattern, or a state directory that is not
a `raicho-<suite>.XXXXXXXX` directory beside the record. It therefore cannot
stop the CI runner or reach another job's deployment. After a completed run the
step finds nothing left to remove. Locally, `make clean` removes interrupted
acceptance projects. The
[decision record](../decisions/20261101-acceptance-cleanup-after-cancel.md)
explains this design.

## Caching

The [build caching decision](../decisions/20261026-build-caching.md) records why CI caches as it does. Images build with
Docker's default builder and its layer cache on the runner's Docker host. CI uses
no GitHub Actions image cache.

`lint`, `application-test`, and `coverage` restore a Cargo cache with
`actions/cache`, keyed by job, `Cargo.lock`, and `rust-toolchain.toml`, into
`raicho-cache` under the runner's temporary directory. Their Make steps set
`RAICHO_CACHE_DIRECTORY` to that folder, so Make binds it at `/cache` through
`automation/tooling/compose.cache.yaml`. The other jobs use the named volume. CI
turns off incremental compilation. Every job that restores a Cargo cache also runs
on pushes to `main`, where `coverage` builds only when no cache matches its key.

GitHub keeps about 10 GB of caches per repository and evicts the least recently
used, so a run after eviction rebuilds cold and saves again.

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
A full checkout supplies those objects, including fork history. Make adds the
`automation/tooling/compose.ci.yaml` override, which mounts the event JSON
read-only at `/tmp/github-event.json`. Body, labels, and commit IDs are parsed as data and
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
| `skip-test` | Skips application, runtime, connector, compatibility, and coverage jobs. |
| `skip-coverage-check` | Skips only the coverage job. |
| `skip-changelog` | Skips the changelog entry check. Does not skip design, build, or test checks. |

Label changes and a change of the PR's base branch rerun only the guard. A label that
skips or restores other jobs takes effect on the next push. After a retarget, the
other checks run against the new base when a commit is pushed or the PR is closed and
reopened; re-running an earlier run reuses its original merge commit.

The `design` label also skips all five application jobs and the coverage job. Jobs are independent,
so a skipped build does not leave invalid test dependencies. Test jobs still
compile/build their test prerequisites when `skip-build` is present. The labels
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
