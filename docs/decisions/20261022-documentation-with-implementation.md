# Include documentation in implementation plans

- Status: accepted
- Date: 2026-10-22
- Deciders: Barkin Simsek

## Context

Repository reorganizations change paths, commands, and contributor guidance.
Treating documentation as a separate follow-up leaves instructions stale and
requires the maintainer to request updates repeatedly.

## Decision

Adopt the [documentation workflow](../contributing/workflow.md#documentation-with-implementation)
for inline and staged plans. Include documentation scope and verification in
planning, execution, and plan review skills. Keep the canonical rule in the
always-loaded workflow referenced by `AGENTS.md`.

## Consequences

Implementation and its documentation are reviewed together. Plans make omitted
documentation work visible, and completion includes checking affected references.
Changes that need no documentation explain why rather than generating unnecessary
edits. Accepted ADRs retain their existing lifecycle.
