# Component-owned build and test helpers

## Goal

Finish the approved automation audit by moving twelve component-specific build
and acceptance files beside the sources they build or exercise. Preserve the
developer commands, runtime behavior, test coverage, and image boundaries.

## Approach

Move the web builder into `web/`, the extension packager into `extension/`, and
its packaging tests and XPI inspector into `extension/tests/`. Put lifecycle and
mail acceptance drivers in their probe's `tests/` directory. Put the credential
acceptance driver and fixture helper in `runtime/credentials/tests/acceptance/`.
Keep filenames unchanged. Update callers directly rather than adding wrappers.

Keep cross-component build dispatch, connector/runtime acceptance, repository
policy, quality tools, releases, and shared test support under `automation/`.
Infer component builder defaults from their own location so image builds do not
need the automation package. Keep host orchestration outside packaged fixtures.

## Documentation impact

Update the canonical placement and test ownership guidance in
`docs/reference/project-structure.md`, commands in
`docs/reference/build-test-generate.md`, architecture and acceptance references,
the credential runbook, and any affected current README or planning examples.
Record the layout refinement in a new ADR. Verify local links, imports, command
modules, and documented paths. Existing accepted ADRs retain their historical
decision text. Contributor instructions and skills already require component
ownership and documentation updates, so change them only if a reference moves.

## Open questions

None. The user approved the twelve proposed moves and associated integration
and documentation changes. The previously approved Docker validation applies.

## Stages

- [x] Stage 1: Relocate component helpers and integrate their callers
  Move the twelve files, preserve Python package discovery and isolated packager
  fixtures, and update Make, Docker inputs, Compose mounts, CI, regression tests,
  and the documentation listed above. Verify with a tooling rebuild, Docker
  formatting, and the shared source checks:

  ```bash
  docker compose -f compose/compose.tools.yaml build
  LOCAL_UID="$(id -u)" LOCAL_GID="$(id -g)" docker compose -f compose/compose.tools.yaml run --rm format make format
  docker compose -f compose/compose.tools.yaml run --rm check make lint format-check typecheck build-app test-app test-protocol test-mailprobe test-tooling
  docker compose -f compose/compose.tools.yaml run --rm -e PYTHONPATH=/workspace/runtime/thunderbird check python3 -B -m unittest discover -s runtime/thunderbird/tests -p '*_tests.py'
  ```

  Check all Compose configurations, changed documentation references, and
  whitespace. Review packaging exclusions and confirm the original repository
  test count is preserved. Review the diff before acceptance validation.

  Completed: all twelve moves and caller/documentation updates are integrated.
  Docker formatting, lint, type checks, builds, application/protocol/probe tests,
  and 27 tooling fixture tests passed. The 168 repository tests are preserved
  across automation (131), extension packaging/XPI (11), credentials (20), and
  protocol generation (6). Thunderbird's 26 runtime tests, all nine Compose
  configurations, documentation references, whitespace, and independent reviews
  passed. No implementation deviation was required.

- [x] Stage 2: Verify disposable deployments and finish the record
  Run the existing isolated runtime startup/persistence/admin-isolation harness
  and these host acceptance commands:

  ```bash
  bash automation/acceptance/connector/raicho_check_connector.bash
  bash runtime/credentials/tests/acceptance/raicho_check_credentials.bash
  bash extension/lifecycleprobe/tests/raicho_check_extension_lifecycle.bash
  bash extension/mailprobe/tests/raicho_check_mail_compatibility.bash
  ```

  Use fresh disposable deployments, preserve the full idle intervals, and
  verify cleanup of their containers, volumes, networks, and temporary tags.
  Record the results and recheck documentation against the final paths. Move
  this plan into `done/` after completion. Stop before committing or pushing.

  Completed: runtime startup, persistence, administrative isolation, and
  independent readiness passed. Connector acceptance passed the full 600-second
  idle interval, authentication, restart/recreation, network recovery, changed
  server address, isolation, and privacy checks. Credential provisioning,
  persistence, rotation recovery, and revocation passed. Lifecycle installation,
  90-second idle, restart, and upgrade passed. Unattended mail draft/restart
  compatibility passed. Native consent, sending, and editing checks were not
  requested or run. All five disposable deployments cleaned up their containers,
  volumes, networks, and temporary image tags. Final documentation and whitespace
  checks passed. Changes remain uncommitted.

## Notes

This is the approved follow-up to the
[automation reorganization](../done/20261026-repository-layout.md#automation) and its
[decision](../../decisions/20261026-repository-layout.md#automation).
