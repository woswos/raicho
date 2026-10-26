# Raicho working agreement

Raicho is an open source project. Anyone can contribute. This working agreement
applies to contributors and AI agents working in the repository.
[AGENTS.md](../../AGENTS.md) is the single repository entry point.

## Precedence

Committed project instructions are the project's source of truth for repository
work. Personal agent configuration may supplement them but must not override
them. Explicit user instructions and the agent's governing system policies
remain authoritative. This is a project convention, not a technical override of
an agent's instruction hierarchy.

## Working agreement

- Planning, approval, validation, and delivery: [workflow](workflow.md).
- Engineering principles: [coding principles](../coding/coding-principles.md).
- Branches, commits, and PRs: [Git and pull requests](git-and-pull-requests.md).
- Documentation placement: [documentation organisation](documentation-organisation.md).
- First-time setup: [getting started](getting-started.md).
- Project invariants: [key conventions](key-conventions.md).

## Durable decisions

Record notable project decisions in [ADRs](../decisions/README.md), rather than
leaving their rationale only in conversations or personal agent memory.
Use committed records as the authority for project decisions, regardless of
the agent. The repository does not configure personal agent memory systems.

The shared skill sources live directly in `.agents/skills/`. There are no
agent-specific settings or committed project hooks. See the
[adoption decision](../decisions/20261005-adopt-shared-workflow.md).
