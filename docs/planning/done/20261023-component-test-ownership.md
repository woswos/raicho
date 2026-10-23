# Component test ownership

## Goal

Place the remaining extension fixture regressions with their component and
changelog guard regressions beside repository policy, preserving test behavior
and the existing local and CI commands.

## Approach

Move `raicho_runner_cleanup_tests.py` and `raicho_test_images_tests.py` into
`extension/tests/` with their filenames unchanged. Extract `ChangelogGuardTests`
from the release version suite into
`automation/repository/tests/raicho_changelog_guard_tests.py` without changing
its assertions. Remove the empty acceptance test package marker. Existing Make
discovery covers both destination directories. Keep shared support imports and
all runtime images, Compose deployments, and application behavior unchanged.

## Documentation impact

Update the test ownership map in `docs/reference/project-structure.md` and the
coverage descriptions in `docs/reference/build-test-generate.md` and
`docs/reference/ci-cd.md`. Record this refinement in a new ADR, marking the
previous ownership ADR superseded while preserving its historical body and
retaining its other placements. README, architecture, AGENTS, and skills already
refer to the canonical ownership guide and need edits only if a reference changes.
Verify changed local links, file references, and imports with the implementation.

## Open questions

None. The user explicitly approved both moves, the extraction, and documentation
updates. Docker repository checks have standing approval in the shared workflow.
The previously authorized Docker formatting and language checks are reused here.

## Stages

- [x] Stage 1: Align test ownership and documentation
  Move the two extension test files, extract the changelog guard class and its
  imports, remove the empty package marker, and update the documentation above.
  Compare test method inventories before and after to confirm none were lost or
  duplicated. Run formatting for the changed Python files through the writable
  Docker tooling service, then run:

  ```bash
  docker compose -f compose/compose.tools.yaml run --rm check make lint-repo lint-python format-check
  ```

  The quality gate is the same 168 repository tests across the discovered
  packages, passing Python lint and formatting, valid documentation references,
  and a reviewed whitespace-clean diff. No runtime acceptance deployment is
  needed because the change touches only test ownership and documentation.
  Record the results and move this plan to `done/`. Stop before committing.

  Completed: both extension tests moved and all four changelog guard tests were
  extracted. All five affected test class syntax trees remain identical, with
  no duplicated definitions. Docker repository checks passed 128 automation,
  14 extension, 20 credential, and 6 generator tests, preserving the total of
  168. Python lint, formatting, documentation references, whitespace review, and
  independent import/discovery/ownership review passed. No runtime, Compose,
  image, or CI command changes were needed. Changes remain uncommitted.

## Notes

This follows the completed
[component helper reorganization](../done/20261026-repository-layout.md#tests).
