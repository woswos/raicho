---
name: write-plan-doc
description: Write a staged planning document for a non-trivial feature or epic before implementation. Produces docs/planning/active/YYYYMMDD-slug.md with a goal, approach, open questions, and an ordered checklist of stages. Trigger when the user wants to plan an epic, write a planning/design doc, or scope multi-session work before coding.
---

# write-plan-doc

Turn a feature brief into a durable planning document that survives context
resets and lets any contributor (or a fresh session) pick up the work.

## When to use

- The work spans more than one session or one PR.
- The approach is non-obvious and worth aligning on before code.
- Several files/packages are affected and order matters.

Skip for small, obvious changes, just plan inline and implement after approval.

## Steps

1. Clarify the goal with the user. Ask about scope, constraints, and what
   "done" looks like. Do not start writing until the goal is clear and the
   document edits are approved under `docs/contributing/workflow.md`.
2. Investigate the relevant code so the plan is grounded in what exists. Cite
   the packages/files involved (names, not line numbers).
3. Write `docs/planning/active/<YYYYMMDD>-<slug>.md` using the structure below.
   Prefix the filename with today's date (`YYYYMMDD`). The slug is kebab-case.
   Design stages to be minimal and incrementally complex, with each stage
   including explicit testing tasks and quality gates.
4. Offer a critique pass: re-read the plan adversarially (or invoke the
   `review-plan-doc` skill) and surface risks, missing stages, ordering
   problems, and whether business value is front-loaded. Fold approved fixes in.
5. Present the plan to the user and get explicit approval before any code.

## Document structure

    # <Feature title>

    ## Goal
    One paragraph: what we're building and why. What "done" means.

    ## Approach
    The chosen design and the key trade-offs. Note rejected alternatives briefly.

    ## Open questions
    Anything unresolved that needs a decision. Resolve before implementation.

    ## Stages
    - [ ] Stage 1: <smallest shippable, verifiable step>
      Brief description of what this stage delivers.
    - [ ] Stage 2: ...
      Each stage is independently reviewable and ends in a working tree.

    Each stage should include:
    - The core work (code, config, documentation, etc.)
    - Testing: explicit tests or manual verification steps
    - Quality gate: linting, type checking, or build validation as applicable
    - A stopping point for review before proceeding to the next stage

    ## Notes
    Links to related PRs, design docs, deep-dive docs.

## Conventions

- **Stage design**: Start with a minimal working version that delivers value,
  then layer complexity. Each stage should be small enough to review and commit
  in one cycle. Front-load business value so partial completion remains useful.
- **Stage flow**: End each stage in a working tree. Include testing tasks and
  quality gates as part of the stage, not after.
- Keep stages small and ordered so each approved stage is one implementation
  and commit cycle.
- No source line-number references, name symbols and files.
- Follow `docs/contributing/documentation-organisation.md` for placement and naming.
- Implementation of stages is the `execute-plan-stage` skill's job, not this one.
