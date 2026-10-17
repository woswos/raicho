# Compose layout and SQL quality

## Goal

Group Compose configurations under `compose/` and check SQLite source with the
same Docker tooling locally and in CI. Existing foundation work is preserved
as separate prerequisite commits in the requested pull request.

## Approach

Move all five Compose files together, resolve build contexts and checkout mounts
relative to their new directory, and name the default runtime project `raicho`.
Explicit project overrides isolate separate deployments and disposable CI runs.
The maintainer accepts fresh volumes and requires no compatibility or migration.

Install SQLFluff 4.4.0 and hash-pinned dependencies in the shared tooling image.
Use a single SQLite/raw configuration for linting and formatting. Check owned
`.sql` files through existing Git discovery. Formatting checks parse and format
temporary copies, comparing bytes without changing sources. Extract the four
production queries to `server/queries/` with compile-time Rust embedding so
the checker covers actual application SQL. Test fixture strings remain inline.

## Open questions

None blocking. Both stages, the validation below, commits, and a new GitHub PR
were explicitly authorized on 2026-10-18. Foundation stages after stage 1 remain
outside this work.

## Stages

- [x] Stage 1: Group Compose files.
  Move runtime, admin, test, tooling, and CI configurations into `compose/`.
  Update commands, CI environment paths, formatter scope, and affected docs.
  Validate every configuration combination, including resolved source paths,
  named volumes, profile selection, and published ports. Use a disposable JSON
  event fixture for the CI override. Review the diff before its separate commit.
  Debrief: all five files moved, references updated, and six configuration
  renderings passed, including the explicit project override. No volume
  compatibility or migration was introduced, as requested.
- [ ] Stage 2: Add SQL linting and formatting.
  Add locked SQLFluff dependencies, a stale-image dependency check, SQLite
  configuration, direct Python runner, Make targets, and regression fixtures.
  Extract production queries without changing behavior. Update conventions,
  tooling documentation, and CI coverage. Do not reformat applied migrations.
  Verify parser/lint failures, formatting idempotence and nonmutation, discovery
  exclusions, symlinks, missing tools/configuration, and absent SQL reporting.
  Run the commands below, review the diff, and commit this stage separately.

## Validation

From the repository root, validate each Compose configuration with
`docker compose -f compose/<file>.yaml config --quiet`, using the runtime base
before admin/test overrides and the tooling base before the CI override.

```bash
docker compose -f compose/compose.tools.yaml build
docker compose -f compose/compose.tools.yaml run --rm check \
  make lint format-check typecheck test-tooling test-server
docker compose -f compose/compose.yaml build
git diff --check
```

Apply necessary formatting through the writable Docker service only. Check
documentation links and stale root Compose paths. Exercise the existing
[disposable runtime procedure](../../operations/local-runtime.md) for HTTP
checks, recreation, and SQLite/profile persistence. Clean up only that
test project's resources. The CI lint job uses the same aggregate targets.

## Notes

- [Foundation plan](20261017-thunderbird-first-foundation.md): prerequisite runtime.
- [Compose and SQL decision](../../decisions/20261018-compose-layout-and-sql-quality.md): accepted choices.
- [SQLFluff](https://pypi.org/project/sqlfluff/4.4.0/): selected release.
- [SQLFluff CLI](https://docs.sqlfluff.com/en/stable/reference/cli/): check and format behavior.
