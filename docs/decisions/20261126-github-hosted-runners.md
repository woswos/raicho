# Run CI on GitHub-hosted runners

- Status: accepted
- Date: 2026-11-26
- Deciders: Barkin Simsek

## Context

The self-hosted runner was removed, so every workflow job waited for a runner that
no longer existed. The [build caching decision](20261026-build-caching.md) relied
on that runner: images built with Docker's default builder, whose layer cache
stayed on the runner's Docker host. A GitHub Actions BuildKit cache had been
dropped only because that host restored layers at about 284 KiB/s.

GitHub-hosted runners start empty. Without a layer cache, seven jobs would rebuild
the tooling image and four would rebuild the application images on every run.

The last self-hosted runs also showed where time went. One push took about 34
job minutes. The connector job took 20 of them, mostly its ten-minute idle
observation. The PR guard built the tooling image to run a Python check that
needs only the standard library. `make test` reran the Python suites that `lint`
had already run. The build job built images that the runtime job builds anyway.
Every push to a draft PR ran the whole suite, and six drafts were open in one stack.

## Decision

Every job runs on `ubuntu-24.04`. The cancel cleanup steps stay, because a
re-run attempt and local runs still benefit and the tests assert them.

Image-building jobs create a BuildKit container builder as the default builder,
with `default-load=true` so existing Compose and `docker build` commands keep
loading images. `docker/bake-action` warms that builder from the GitHub Actions
cache and writes new layers back. The acceptance scripts are unchanged. This
replaces the image part of the earlier decision. Its Cargo cache rules stay.

The PR guard runs its module with the runner's Python instead of the tooling image.

`application-test` runs only the suites `lint` does not run. The
`application-build` job and its `skip-build` label are removed. Compose
configuration validation moves to `lint`, and `runtime-test` builds every
runtime image.

Three rules trade coverage on PRs for time:

- Draft PRs skip the acceptance jobs and `coverage`. Marking a PR ready runs them.
- PRs that change only Markdown files skip every application job.
- PRs observe two idle minutes in the connector runner. Pushes to `main` and
  local runs keep ten.

## Consequences

Jobs run in parallel instead of queueing on one runner. Nothing needs pruning,
and the one-runner-per-host rule is gone.

Image layers now share GitHub's 10 GB cache limit with the Cargo caches. A run
after eviction rebuilds cold.

A draft can hide an acceptance or coverage failure until it is marked ready. A
heartbeat fault that appears only after two idle minutes surfaces on `main`
after the merge instead of on the PR. Pushes to `main` run every job in full,
but they do not hold a release back: `auto-release.yml` starts on the same push
and can tag a release while those jobs still run.

Standard hosted runners are free for public repositories, so these cuts shorten
feedback rather than a bill while the repository stays public.
