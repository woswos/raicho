# Adopt the shared development workflow

- Status: accepted
- Date: 2026-10-05
- Deciders: Barkin Simsek

## Context

Private agent configuration would make repository behavior inconsistent and
invisible in review. Unresolved product work needs a reviewed design before
implementation, and smaller changes still need a recorded rationale. Broken
instruction links, inconsistent filenames, and a hand-maintained ADR index
would make that workflow unreliable.

## Decision

Use one shared, tool-neutral workflow. `AGENTS.md` is the only instruction
entry point. Topic documents under `docs/contributing/`, `docs/reference/`,
and `docs/coding/` own the rules. Store the six workflow skills directly in
`.agents/skills/`. Do not add vendor-specific agent settings, adapter files,
compatibility symlinks, or project hooks.

Record notable decisions as ADRs. The directory listing is the index. Naming,
the two-PR process, and repository integrity checks are defined in
[documentation organisation](../contributing/documentation-organisation.md),
[workflow](../contributing/workflow.md), and
[build, test, and generate](../reference/build-test-generate.md).

## Consequences

Contributors and agents follow the same reviewable instructions. Personal agent
settings can still exist outside the repository. The checks catch missing
references and malformed skill metadata. They do not judge design quality or
replace GitHub review settings.
