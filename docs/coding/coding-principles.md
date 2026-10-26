# Coding principles

Engineering principles for Raicho. Concrete syntax and naming rules live in
[coding standards](coding-standards.md).

## Simplicity

Prefer code that is easy to read, debug, and change. Fix causes rather than
symptoms. Start with the smallest useful implementation and add complexity only
when a requirement calls for it.

## Errors

Surface failures at their source with enough context to act. Do not swallow
errors or hide useful diagnostic information behind broad catch-all handlers.
Keep private mail and credentials out of diagnostics.

## Reuse

Use existing utilities and established local patterns before adding alternatives.
Decompose behavior into focused functions and design boundaries for testing.
Prefer the standard library. Justify a new dependency and prefer maintained
projects with an established community.

## Consistency

Give each rule one source. Generate vocabularies and limits that several
languages share, pin shared algorithms with one test vector that every
implementation runs, and keep a single implementation of each validation rule. Operational commands run from runtime images. The tooling
image is for development and tests only.

## Collaboration

Raise unclear requirements and material design alternatives before proceeding.
Keep changes independently reviewable and ground decisions in the actual code.
