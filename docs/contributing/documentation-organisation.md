# Documentation organisation

Each rule has one canonical topic document. Cross-link instead of copying rules.
[AGENTS.md](../../AGENTS.md) contains only introductory and document-loading text.
It `@`-loads the always-on documents and names the task-specific documents
without loading them.

## Categories

- `docs/contributing/`: contributor and agent working agreements and project invariants.
- `docs/reference/`: evergreen project structure, tools, and architecture.
- `docs/coding/`: engineering principles and concrete coding and formatting conventions.
- `docs/planning/active/`: in-flight staged plans.
- `docs/planning/done/`: completed plans, moved with their final implementation.
- `docs/decisions/`: durable [decision records](../decisions/README.md).
- `docs/operations/`: operational procedures, created when first needed.
- `docs/raicho/`: customer-facing content, created when first needed.
- `assets/brand/`: existing identity sources, provenance, and visual guidance.

Use `write-evergreen-doc` for reference documents. Its structure is introduction,
see-also links, principles or decisions, then necessary details. For systems in
transition, state current behavior, target behavior, and migration status with a
link to the plan. Runbooks explain when to use them, steps, and verification.

Keep reference documents evergreen. Describe current behavior and link to plans
for targets, without dated run results, stage numbers, pull request numbers, or
words such as "now" and "currently". Record dated evidence in an evidence section
of the relevant plan, or in a decision record.

## Naming

Use lowercase `kebab-slug.md` filenames. Plans and ADRs use a `YYYYMMDD-` creation
or acceptance date prefix. `README.md`, `CHANGELOG.md`, `AGENTS.md`, `LICENSE`,
and skill entry points named `SKILL.md` retain their canonical names.
`template.md` is allowed in planning and decision directories.

GitHub requires its own template directory conventions. Existing third-party
font license and provenance filenames remain intact. The naming guard covers
Markdown under `docs/`, including tracked paths that are missing from the
worktree. Dated plans must be directly in `active/` or `done/`. Dated
decision records must be directly in `docs/decisions/`. Historical and vendor
artifacts are outside this guard.

## Skills

Keep one canonical copy directly at `.agents/skills/<name>/SKILL.md`. Skills are flat, with no grouping
subdirectories or auxiliary files. Frontmatter contains an exact `name` and a
non-empty single-line `description`. Use plain or quoted single-line YAML scalars.
Skill names use lowercase kebab-case: letters and digits in words separated by
one hyphen, such as `write-plan-doc` and `execute-plan-stage`. The frontmatter
`name` equals the directory name. The skill guard under `make lint-repo`
enforces both, and the directory guard applies the same pattern.

Only `add-*` scaffolding skills, such as `add-endpoint`, carry an `examples` list
of one to three existing repository file paths. Each example is also cited in
the skill body. Add such skills only once recurring patterns exist. Group related
names with prefixes.

## Maintenance

Documentation scope and completion checks are part of the
[implementation workflow](workflow.md#documentation-with-implementation).
Broken links and instructions that contradict the repository are defects. Use
`execute-doc-housekeeping` to reconcile them. ADR lifecycle rules live in the
[decision guide](../decisions/README.md).
