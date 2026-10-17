---
name: execute-doc-housekeeping
description: Reconcile documentation with code and conventions when a plan stage lands or a document contradicts the repository. Trigger when a stage changes behavior the docs still describe, or when instructions, references, or structure have drifted.
---

# execute-doc-housekeeping

Keep documentation accurate and synchronized with the codebase.

## When to use

- A plan stage has landed and the instructions or reference docs must match it.
- A document contradicts the code or the current structure.

Do not run this as a periodic prose pass.

## Steps

1. **Scope the review.** Full set (`AGENTS.md`, `docs/contributing/`,
   `docs/reference/`, `docs/coding/`, `docs/decisions/README.md`) or a subset.
   Ask what changed that prompted this pass if the context is missing.
2. **Read key docs and code.** Check for stale examples, rules that contradict
   the codebase, unresolved cross-references and `@` file references.
3. **Identify drift.** Feature mismatches, moved files, renamed commands,
   missing docs, broken links, duplication, a superseded ADR whose status was
   never updated.
4. **Plan the updates.** When this pass is part of an approved stage, that stage
   authorizes the edits. Otherwise present the concrete edits and get approval
   under `docs/contributing/workflow.md` before editing.
5. **Execute the edits** in logical groups.
6. **Run integrity checks.** `make lint-repo` through the Docker check service,
   using the command in `docs/reference/build-test-generate.md`. The repository
   guards and their failure-path tests must pass.
7. **Verify cross-links and status.** Deprecated features marked, upcoming work
   labelled "planned".
8. **Commit when authorized.** Doc changes only, one `chore:` Conventional Commit.

## Conventions

- Single source of truth, cross-reference rather than duplicate.
- Mark features as current, deprecated, or planned.
- Every notable decision is in `docs/decisions/<YYYYMMDD>-<slug>.md`. The
  directory listing is the index.
- No over-updating. Do not rewrite a doc just to tighten prose.
