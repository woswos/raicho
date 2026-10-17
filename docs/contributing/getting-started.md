# Getting started as a contributor

Anyone can contribute to Raicho. The [README](../../README.md) states what the
repository contains today and what a product change requires. The
[working agreement](working-agreement.md) and [workflow](workflow.md) are the
rules for that work. For AI-assisted work, read [AGENTS.md](../../AGENTS.md).
It loads the always-on documents and names the ones to open for a specific task.

## Agent loading

Use `AGENTS.md` as the repository instruction entry point. Agents that do not
expand its `@` file references must open each named document explicitly. If the
agent does not discover the entry point, start the session with:

> Read AGENTS.md and the documents it loads before working in this repository.
> Open the task-specific documents it names when the work needs them.
> What is your working agreement?

Confirm the answer cites `docs/contributing/working-agreement.md` and the
documents the task requires. This loading instruction does not grant approval
to edit files.

## Shared skills

The six workflow skills live directly in `.agents/skills/<name>/SKILL.md`.
There is no compatibility symlink or vendor-specific settings file. Agents that
do not discover that directory can read the named skill explicitly when needed.
Personal configuration must respect [precedence](working-agreement.md#precedence).

## Current repository checks

Install Docker with Compose and clone the repository with Git. Language tools
run inside the pinned tooling image. Versions and commands are recorded in
[build, test, and generate](../reference/build-test-generate.md).

```bash
docker compose -f compose.tools.yaml build
docker compose -f compose.tools.yaml run --rm check make lint format-check typecheck
```

## Planned application development

The [foundation plan](../planning/active/20261017-thunderbird-first-foundation.md)
introduces the application runtime from stage 1. Repository tooling is available
now, but there is no application deployment to start. See
[architecture](../reference/architecture.md) for current and planned behavior.
