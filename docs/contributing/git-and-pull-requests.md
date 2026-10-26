# Git and pull requests

Raicho is hosted on GitHub. Inspect the remote before choosing hosting tools and
use `gh` for this repository. Prefer local `git diff` and `git log` for review
unless remote-only information is needed.

## Branches

Name new branches as `YYYYMMDD-kebab-slug`, for example
`20261017-license-exception`. The date is the day the branch is created. The
default branch is `main`. Branches that already use another name keep it.
Use the actual PR base branch when reviewing a PR that targets another branch.

## Commits

- Use concise Conventional Commits, with an imperative subject of at most
  50 characters. Wrap an optional explanatory body at approximately 72 columns.
- Review the full relevant diff and stage exact paths within the approved scope.
  Do not use blanket `git add -A`.
- When implementation commits are requested, split work into meaningful units.
  Keep related implementation, documentation, and tests together where possible.
- A single plain commit request means one commit containing all changes in the
  user-approved scope. Do not split it, or run tests, builds, linting, formatting,
  deployments, or `make` targets for that request.
- Inspect hooks before committing. Use `--no-verify` if a hook would run an
  unapproved operation. Do not install hooks as part of this workflow.

## Pull requests

Use `gh pr create --draft` after checking authentication and authorization to publish.
Assign an owner, normally `--assignee @me`. Use `--label design` for a planning
PR and the design template with `--template design.md`. GitHub does not apply
labels from slash commands in descriptions.

Create both design and implementation PRs as drafts. Convert a PR with
`gh pr ready` only after the repository maintainer has reviewed it and explicitly
approved making it ready. Passing CI or an automated review does not authorize
that transition.

Lead descriptions with the concrete problem and resulting behavior. Explain the
cause, fix, relevant validation, and limitations. Keep them concise and follow
[prose conventions](../coding/coding-standards.md). Include the design or decision
reference required by [workflow](workflow.md). Review the description before
publication. Body and label edits retrigger the relevant CI guards.

A change an operator can notice also needs a changelog entry. Put it in the
description's Changelog section, or under `## [Unreleased]` in `CHANGELOG.md`.
The kinds, the `skip-changelog` label, and the version bump rules are in
[versioning](../reference/versioning.md).

When a merge and branch deletion are authorized, use `gh pr merge --delete-branch`.
Repository-wide automatic branch deletion and required checks are separate
GitHub settings. Creating workflow files does not enable those settings.
