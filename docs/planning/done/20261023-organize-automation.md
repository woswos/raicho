# Organize repository automation by responsibility

## Goal

Replace the flat `devbin/` tree with discoverable automation packages and keep
operational credential management with runtime code. Preserve command behavior,
credential protections, deterministic packaging, and the existing source basenames.

## Approach

Group developer automation under `automation/repository/`, `quality/`, `build/`,
`release/`, and `acceptance/`. Shared test fixtures belong in
`automation/testing/`. Each area owns a `tests/` subtree. Keep Make as the main
developer interface and call Python packages directly without compatibility
wrappers. Move credential operations into `runtime/credentials/`, with their
tests. Keep protocol generation beside the existing Rust generator under
`protocol/generator/`.

Update imports, repository-root resolution, test discovery, Docker build inputs,
Compose mounts, and CI together. Preserve the credential services' users,
capabilities, networking, and read-only boundaries. Existing lifecycle and mail
fixtures remain with their extension owners. Historical accepted ADRs remain
the record of their original layout.

## Documentation impact

Update `AGENTS.md`, README, the placement guide, coding conventions, command and
CI references, architecture, runtime and acceptance references, operational
runbooks, and relevant current planning documents. Record the accepted placement
decision in an ADR. Check affected local links and documented paths.

## Open questions

None. The maintainer approved the complete reorganization and all source and
disposable acceptance checks. Commits and publication remain separate actions.

## Stages

- [x] Stage 1: Relocate code and update every caller and instruction.
  Move all 83 existing files to their owners, use explicit package imports, and
  update test fixtures and invocation paths. Update Docker, Make, Compose, CI,
  current documentation, and the ADR in the same stage. Check the unchanged
  regression suites, formatting, naming, generated protocol output, and builds.
  Quality gates: rebuild the tooling image, run the Docker format service, then
  `make lint format-check typecheck build-app test-app test-protocol
  test-mail-probe test-tooling` through the Docker check service. Verify local
  documentation links and paths, rename completeness, and `git diff --check`.
  Review checkpoint: report the source validation before acceptance testing.
  Debrief: all 83 files moved, callers and documentation updated, and the Docker
  source gates passed, retaining 168 repository tests and 27 tooling fixture
  checks. Nine Compose combinations and 230 local references passed. Runtime
  credentials use a namespace parent to preserve Thunderbird's `runtime.py`
  imports, verified by the separate 26-test runtime suite.

- [x] Stage 2: Verify the relocated deployment and fixture entrypoints.
  Run the documented Thunderbird runtime unit suite, disposable runtime smoke
  checks, and the relocated connector, credentials, lifecycle, and unattended
  mail acceptance runners. Verify cleanup and update this plan with the results.
  Quality gate: every approved check passes with the production credential and
  packaging boundaries preserved. Move the completed plan to `done/` and report
  results for review before any commit.
  Debrief: runtime startup, persistence, isolation, and independent readiness
  passed. Credential provisioning/recovery, lifecycle install/restart/upgrade,
  and unattended mail draft/restart checks passed. The production connector
  passed ten minutes of stable heartbeats, service restart/recreation, network
  recovery, DNS refresh, isolation, and privacy checks. All five deployments
  removed their temporary containers, volumes, networks, and image tags.

## Notes

- [Placement guide](../../reference/project-structure.md)
- [Commands](../../reference/build-test-generate.md)
- [Documentation workflow](../../contributing/workflow.md#documentation-with-implementation)
