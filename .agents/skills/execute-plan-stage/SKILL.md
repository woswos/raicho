---
name: execute-plan-stage
description: Execute the next unchecked stage of a planning document, then pause for review. Implements one approved stage from docs/planning/active/YYYYMMDD-slug.md, checks it off, and stops before committing or starting the next stage unless those actions are already explicitly authorized. Trigger when the user wants to continue/advance a planning doc, do the next stage, or work through a plan stage by stage.
---

# execute-plan-stage

Drive a planning doc forward one stage at a time, with a human checkpoint
between stages. Pairs with the `write-plan-doc` skill.

## Steps

1. Read the target `docs/planning/active/<YYYYMMDD>-<slug>.md`. If the user did
   not name one and several exist, ask which.
2. Find the first unchecked `- [ ]` stage. That is the only stage you do this
   run unless the user explicitly authorized a named sequence of stages.
3. Implement that stage. An approved stage authorizes edits inside its scope.
   Defer anything that belongs to a later stage. Follow
   `docs/contributing/workflow.md` for what counts as approval.
4. Verify with the checks named by the stage. `make lint-repo` has standing
   approval when run through the Docker check service, using the command in
   `docs/reference/build-test-generate.md`. Follow the same workflow for any
   other test or deployment command.
5. Mark the stage `- [x]` and add a one-line debrief under it: what changed,
   decisions made, anything surprising, follow-ups discovered, and any
   deviation from the plan with why. If this was the last unchecked stage,
   move the plan from `docs/planning/active/` to `docs/planning/done/` with
   `git mv`, in the same commit as the final stage.
6. Report what you did and pause before committing or starting the next stage
   unless those actions are already explicitly authorized. Commit an approved
   stage as one Conventional Commit.

## Conventions

- One stage per run by default. Pause before the commit and before the next stage.
- If a stage turns out wrong or too big, stop and propose updating the plan via
  `write-plan-doc` rather than improvising.
- Delivery rules live in `docs/contributing/workflow.md`. Pull request checks
  live in `docs/reference/ci-cd.md`.
