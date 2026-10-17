---
name: review-plan-doc
description: Critique a planning document for soundness before implementation. Surfaces unstated assumptions, missing stages, scope creep, unresolved risks, and verifiability issues. Trigger when reviewing a plan, stress-testing a planning doc, doing a pre-implementation plan review, or critiquing a plan for gaps.
---

# review-plan-doc

Perform an adversarial review of a planning document to surface risks, missing
stages, and ordering problems before any code is written. This is the critique
pass referenced in the `write-plan-doc` skill.

## Steps

1. Read the target `docs/planning/active/<YYYYMMDD>-<slug>.md`. If the user did
   not name one and several exist, ask which.
2. Verify the plan structure matches the `write-plan-doc` template: Goal,
   Approach, Open questions, Stages (ordered checklist), Notes.
3. Review the plan adversarially across five areas:
   - **Problem understanding**: is the goal clear? Root causes or symptoms?
     Assumptions stated and valid?
   - **Solution approach**: is the design sound? Simpler approaches ruled out?
     Trade-offs explicit?
   - **Stages and sequencing**: right size (one implementation and commit cycle each)?
     Correct order? Independently verifiable? Any missing?
   - **Scope and risks**: open questions resolved or blocking? External
     dependencies called out? Contingencies planned?
   - **Verifiability**: can each stage's completion be observed without
     waiting for downstream stages?
4. Optionally use an available independent review agent for another perspective.
5. Compile findings into a structured critique with strengths, problems (by
   severity), concrete suggested edits, and clarifying questions.
6. Print the critique. Do NOT edit the plan file, the author decides whether
   to fold in fixes.

## Output structure

- **Strengths**
- **Critical issues** (block implementation)
- **Major issues** (affect multiple stages or add risk)
- **Minor issues**
- **Suggested edits** (concrete text to add/change)
- **Clarifying questions**

## Conventions

- Review is advisory and read-only, do not edit the plan file.
- Implementation of stages is the `execute-plan-stage` skill's job.
