---
name: write-evergreen-doc
description: Write or refresh an evergreen reference doc for a subsystem or library. Trigger when documenting a subsystem, writing a deep-dive doc, capturing research findings for reuse, or creating a long-lived reference under docs/.
---

# write-evergreen-doc

Produce a concise, long-lived reference doc for a subsystem so contributors reuse
the understanding instead of re-deriving it. This is the how-to for the
workflow's Investigate section (`docs/contributing/workflow.md`).

## When to use

- An unfamiliar library or subsystem was researched and the findings should
  outlive the session.
- A subsystem has no doc, or its doc no longer matches how it works.

For short-lived planning, use `write-plan-doc`. For reconciling existing docs
at scale, use `execute-doc-housekeeping`.

## Steps

1. Confirm scope and the canonical home (`docs/reference/<topic>.md` or a
   topical subdir, kebab-slug named). Creating or refreshing? When the work is
   not an approved stage, obtain approval under `docs/contributing/workflow.md`.
2. Ground the doc in the code, read the subsystem before writing.
3. Write the doc using the structure below. Link to canonical sources rather
   than restating them.
4. Cross-link: add the doc to any relevant index with a one-line note on why
   it is relevant. Use relative paths.
5. Verify links and naming with `make lint-repo`, as
   `docs/reference/build-test-generate.md` describes it.
6. Commit when authorized, per the repo conventions.

## Structure

- **Introduction**, one or two sentences.
- **See also**, cross-references, each with a one-line relevance note.
- **Principles / key decisions**, link to the ADR when one exists.
- **Detailed sections**, architecture, patterns, gotchas, troubleshooting.
  Only what a reader cannot recover from the code itself.
- **Appendix** (optional).

## Systems in transition

Label the state explicitly: **Current state**, **Target state**, **Migration
status** with a link to the planning doc.

## Conventions

- Single source of truth, link rather than duplicate. Duplication drifts.
- A doc that contradicts the code is a bug.
- Concise over exhaustive, capture the non-obvious.
