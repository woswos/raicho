# Agent workflow

The shared workflow for AI-assisted work in Raicho.

## Plan and approval

Read-only investigation, review, diagnosis, and planning may proceed without
approval. Ask when missing information could materially change implementation.
Re-read a file immediately before editing if it may have changed since inspection.

An approved stage authorizes implementation of that stage, including the
validation it names. Approval means the stage belongs to a merged design, or
the user has explicitly approved that stage. Implement it without presenting
the edit list for a second approval. Pause before committing the stage and
before starting the next stage, unless the user has already authorized those
actions. Explicit authorization may name several stages and their commits.

Work that is not an approved stage needs a concise plan of the proposed edits
and explicit approval before files change. Include the validation commands in
that plan. This includes review fixes that expand the approved scope. Ask
again before materially expanding an approved stage.

Use plan mode for strategic discussion when available. Do not modify repository
files in plan mode. For non-trivial work, use `write-plan-doc` to capture the goal,
approach, open questions, and ordered stages. Resolve blocking questions before
implementation and offer a `review-plan-doc` critique.

## Documentation with implementation

Every edit plan, whether inline or a staged document, must explicitly assess
documentation impact. Name the affected documents, including README files,
references, contributor instructions, and skills where relevant. Assign the
updates and their validation to the stages that introduce the change. If no
documentation updates are needed, state that and explain why.

Required documentation work belongs to the same implementation stage and
approval scope as the change. Update affected behavior descriptions, commands,
paths, examples, and links alongside implementation without waiting for a
reminder. Before reporting completion, verify those documents against the final
implementation and check their local references.

Follow [documentation organisation](documentation-organisation.md) for canonical
locations and cross-links, and the [decision guide](../decisions/README.md) for
accepted records. The [documentation decision](../decisions/20261022-documentation-with-implementation.md)
records this convention.

## Investigate

Research unfamiliar subsystems before implementing them. Capture reusable
findings with `write-evergreen-doc` in the canonical documentation location.
Distinguish existing behavior from proposed behavior.

## Implement and verify

Use `execute-plan-stage` for one approved stage at a time. Follow the stage
authorization and pause rules above. Each stage ends in a working state.

Run the checks listed in the approved stage. The read-only repository integrity
checks in [build, test, and generate](../reference/build-test-generate.md) have
standing approval for implementation work. Application tests and deployments
named by an approved stage are part of that authorization. Any other application
test or deployment needs its own authorization. The separate
[plain-commit rule](git-and-pull-requests.md#commits) takes precedence when the
request is only to commit.

## Design-first delivery

Non-trivial changes use two pull requests:

1. Write a plan in `docs/planning/active/` with `write-plan-doc`. Open a PR
   containing only dated planning documents, labeled `design`. Discuss and merge
   it into its target branch before implementation.
2. Open a separate implementation PR. Its description names the merged plan:
   `Design: docs/planning/active/YYYYMMDD-slug.md`. Use `verify-against-design`
   before review.

An implementation PR without a relevant design can add an ADR and reference it
with `Decision: docs/decisions/YYYYMMDD-slug.md`. Every PR is an implementation
PR by default. The `skip-design-check` label is the escape hatch, with a reason
in the PR description. Prefer a decision record.

The [PR guard](../reference/ci-cd.md) checks these references, exempts docs-only
changes, and verifies that a `design` PR really contains only planning documents.
This bootstrap uses its
[adoption decision](../decisions/20261005-adopt-shared-workflow.md)
as the implementation rationale.

## Design changes and completion

If implementation requires a design change, update the planning document in the
same PR and explain why. Do not silently diverge. When subsystem connections,
packages, dependencies, or data flows change, update
[architecture](../reference/architecture.md) in the same PR.

Where behavioral tests apply, add the planned tests before the implementation.
Record red/green evidence when execution is authorized. For documentation and
assets, use the plan's explicit validation instead of artificial tests.

Every plan starts in `active/`. Never add a plan directly to `done/`. When review
of an unmerged implementation changes the design of a plan that is already in
`done/`, add a dated follow-up note to that plan, and record the change in a new
decision record rather than rewriting the original stages.

After the last stage, move the plan from `active/` to `done/` with `git mv` in the
final implementation commit. Keep the PR's `Design:` line pointing at the path
that exists on the target branch. The verification skill finds the completed
plan at `done/` by the same dated filename.

## Housekeeping

Use `execute-doc-housekeeping` for documentation work within an approved change
or to reconcile existing drift. Do not run it as a periodic prose pass.
Commit conventions live in
[Git and pull requests](git-and-pull-requests.md). The rationale for this workflow
is in the [shared workflow decision](../decisions/20261005-adopt-shared-workflow.md).
