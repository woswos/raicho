# Runtime service configuration

## Goal

Keep production service support files together under `runtime/` and ensure
gateway configuration and image changes receive the existing changelog review.

## Approach

Move the sole source in the `config` directory, the gateway's `nginx.conf`,
unchanged into `runtime/gateway/`. Update its Dockerfile and build-context filter,
keeping `/etc/nginx/nginx.conf` as the image destination. Remove the empty old
directories. Compose services and persistent data paths need no changes.

Extend the changelog guard's shipping classification to `runtime/gateway/` and
`containers/gateway/`. Preserve the existing tests and `.dockerignore` exclusions.
Add regression coverage before changing the guard, including rejection without
a changelog entry and acceptance with an entry for each gateway input.

## Documentation impact

Update the placement map in `docs/reference/project-structure.md`, the gateway
path in `docs/reference/runtime.md`, and shipping scope in
`docs/reference/versioning.md`. Add an ADR for the consolidation and policy fix.
Review README, architecture, AGENTS, and skills for affected references. Their
canonical links and runtime descriptions otherwise remain valid. Preserve
accepted ADR bodies and historical planning records.

## Open questions

None. The user approved the move, Docker inputs, documentation, validation, and
the additional changelog guard fix.

## Stages

- [x] Stage 1: Consolidate runtime configuration and close the guard gap
  Add and run focused gateway guard regressions against the old policy, then
  implement the classification fix and rerun them. Move the configuration,
  update image inputs and documentation, and verify its bytes are unchanged.

  ```bash
  docker compose -f compose/compose.tools.yaml run --rm check python3 -B -m unittest automation.repository.tests.raicho_changelog_guard_tests
  docker compose -f compose/compose.tools.yaml run --rm check make lint-repo lint-python format-check
  docker compose -f compose/compose.yaml build gateway
  docker run --rm --read-only --network none --tmpfs /tmp:mode=1777 --cap-drop ALL --security-opt no-new-privileges:true --entrypoint nginx raicho-gateway:local -t
  ```

  Use the writable Docker tooling service for formatting changed Python files
  if needed. Review diffs and local documentation links, imports, and path
  references. Verify the built image contains the unchanged configuration and
  the intended non-root user. No application deployment or long idle check is
  needed because gateway routing bytes and deployed paths are unchanged.
  Record red/green results and final checks, move this plan to `done/`, and
  stop before committing or pushing.

  Completed: configuration moved unchanged, image inputs and all affected
  documentation updated, and both gateway prefixes now receive changelog
  enforcement. Focused tests first failed with six expected subtest failures,
  then all six tests passed after the fix. Full Docker repository checks passed
  170 tests (130 automation, 14 extension, 20 credentials, 6 generators), Python
  lint, and formatting. The gateway image built successfully, Nginx syntax and
  configuration checks passed, and its installed configuration matches both the
  original and relocated source bytes. UID/GID 10001, documentation references,
  whitespace, and independent review passed. Changes remain uncommitted.

## Notes

The accepted [container input decision](../../decisions/20261026-repository-layout.md#components)
already separates runtime code/configuration from recipe-only image directories.
