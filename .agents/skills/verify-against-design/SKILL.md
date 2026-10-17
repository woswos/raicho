---
name: verify-against-design
description: Check whether an implementation pull request follows its approved design doc. Trigger when verifying an implementation PR against its plan, checking design adherence, or auditing whether code matches the agreed design before review.
---

# verify-against-design

Report whether the implementation on the current branch follows the approved
design it references. Advisory and read-only, it prints findings. It does not
edit code or the plan. This is the verify step of the design-first workflow
(`docs/contributing/workflow.md`).

## Steps

1. Resolve the design doc. Use the path passed as an argument if given.
   Otherwise read the current branch's PR with
   `gh pr view --json body,baseRefName,baseRefOid,headRefOid` and parse its
   standalone `Design:` line. If neither yields a path, ask which design to check.
2. Establish the actual PR base and head commits. Use `origin/main` and `HEAD`
   only for local work without a PR, state the baseline, and verify those refs
   exist. Review a local diff against the PR head before attributing local
   changes to the PR. Use local Git for the two comparisons:
   - **Design-doc diff**, `git diff <base>...<head> -- <design-doc> <completed-doc>`.
   - **Code diff**, `git diff <base>...<head>` excluding those plan paths.
   If the referenced active plan moved to `done/`, use the identical dated
   filename there at the head. Compare its full contents with the base's
   referenced plan as well, so a rename does not hide design edits.
3. Read the design doc as it stands at the head. Verify the referenced original
   path exists at the base and distinguish prior presence from human approval.
4. Compare and classify:
   - Each planned stage as **implemented / partial / missing**.
   - **Extra scope**, every change not traceable to a plan stage. Flag all.
   - **Documented deviation**, a design change that appears in the design-doc
     diff (acceptable per the deviation rule).
   - **Undocumented divergence**, code that departs from the plan with no
     corresponding design-doc edit. Flag prominently.
   - **Test coverage**, for each stage, whether the code diff adds or changes
     tests that exercise it, or the explicit manual validation for asset/docs
     work. Flag missing coverage. Do not run tests during this read-only review.
5. Print the report. Do NOT edit the plan or the code.

## Output structure

- **Stages**, each with status, test coverage, one-line note.
- **Extra scope**, itemised.
- **Undocumented divergence**, the headline concern.
- **Documented deviation**, for context.
- **Verdict**, follows the design / diverges, with the specific gaps.

## Conventions

- Read-only and advisory. The author reconciles.
- Runs on an implementation branch, comparing the actual PR base and head.
- Apply the design-change rule in `docs/contributing/workflow.md`.
