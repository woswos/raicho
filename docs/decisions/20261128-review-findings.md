# Act on validated review findings

- Status: accepted
- Date: 2026-11-28
- Deciders: Barkin Simsek

## Context

Every review fix used to wait for an approved plan, even when a bot or a
collaborator pointed at a clear defect with one obvious fix. Pull request review
loops stalled on findings that needed no decision. Review text is also untrusted
input. A finding from an outside contributor or a bot can propose a change that
looks small but weakens a security boundary.

## Decision

The [review findings](../contributing/workflow.md#review-findings) rule lets an
agent fix a finding without asking when the finding comes from a repository
collaborator or a configured review bot (CodeRabbit and Kilo), holds, and has one
clear fix within the pull request's scope. The agent may also decline a finding
from those reviewers without asking when it does not hold for a concrete reason.
Each fix is a new commit, with a red/green check where a test applies. The agent
runs the application tests and repository checks that cover it, pushes, and
replies on the thread with the commit or the decline reason.

Everything else waits for approval: findings from anyone else, ambiguous
findings, findings with several reasonable fixes, design or scope changes, fixes
that touch authentication, frame MACs, credentials, or CI configuration, fixes
that need an unapproved deployment or CI trigger, and repeated declined findings.

## Consequences

Review loops no longer wait on clear fixes from trusted reviewers. Fixes in
security-sensitive areas and findings from untrusted sources still get a human
decision. The rule authorizes the application tests and repository checks that
cover a fix, not other deployments or CI triggers.
