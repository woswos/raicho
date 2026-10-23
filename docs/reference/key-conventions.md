# Key conventions

Project invariants complement the shared [workflow](../contributing/workflow.md) and
[coding standards](../coding/coding-standards.md).

## Repository organization

Use the [placement rules](project-structure.md#placement-rules) for files and
the [test ownership guide](project-structure.md#test-code) for tests and fixtures.
Naming follows the [source filename](../coding/coding-standards.md#source-filenames)
and [directory name](../coding/coding-standards.md#directory-names) conventions.

## Product and data

- Follow the accepted [foundation decision](../decisions/20261017-thunderbird-first-foundation.md)
  and [target architecture](architecture.md#target-architecture).
- Apply the ownership boundary in the
  [foundation plan](../planning/active/20261017-thunderbird-first-foundation.md#ownership-and-persistence)
  to server, extension, and browser work. Do not introduce an alternate mail store
  or filter engine to work around an API limitation.
- Resolve the relevant [implementation gates](../planning/active/20261017-thunderbird-first-foundation.md#open-questions)
  before each stage, including extension API availability in the selected
  Thunderbird version. Accepted product constraints are not open stack choices.
- Keep fictional showcase data separate from future account/message handling.
  Demo connection labels and interactions are not evidence of live integration.
- Keep Thunderbird data and credentials out of mockups and screenshots.

## Brand integrity

Reuse production SVGs and wordmark outlines in `assets/brand/logos/`. Preserve
the approved bird geometry, including its two thick legs. The authoritative
font settings, typography scale, palette, and usage guidance live in the
[brand guide](../../assets/brand/README.md) and its linked sources.

Use `assets/brand/tokens.css` for core colors and typography. Preserve the font
license and provenance files and the historical material in
`assets/brand/references/`.

## Visual changes

Follow the [showcase guide](../../assets/brand/showcase/README.md) for previews
and exports, including their dependency order. Regenerate affected PNGs when
approved artwork or layouts change. Inspect light/dark themes, responsive
layouts, small-size legibility, clipping, and exact export dimensions.
