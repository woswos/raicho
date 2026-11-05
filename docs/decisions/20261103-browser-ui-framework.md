# Build the browser client with Preact

- Status: accepted
- Date: 2026-11-03
- Deciders: Barkin Simsek

## Context

The diagnostics page updates a fixed document with hand-written DOM code. Stage 3
adds login, account and mailbox selection, paginated summaries, and explicit
loading, error, disconnected, and stale states. Later stages add message views and
compose. The page runs under `default-src 'self'`, so it cannot load an inline
import map, and the build uses only `tsc` today.

## Decision

The browser client uses Preact 10 components written in TSX. `tsc` type-checks the
sources and compiles them for tests, and the pinned esbuild bundles the page that
ships. Preact is one runtime package without dependencies. It escapes JSX text, so
mail subjects, names, and addresses rendered as JSX text cannot add markup. That
guarantee does not cover Preact's raw HTML path, so those fields never reach
`dangerouslySetInnerHTML` or another raw HTML sink. Sanitized message-body HTML,
when stage 4 adds it, stays inside the message view.

Logic modules are tested with `node:test`. Rendering is checked by inspecting the
running page in light, dark, and mobile layouts. ESLint forbids browser storage
APIs in `web/src`, so mail cannot persist there, and it forbids raw HTML sinks
there, so mail text cannot bypass escaping.

## Consequences

The web build gains a bundling step and one locked runtime dependency, which
`make audit` covers. Plain DOM code, Lit, React, Svelte, and Solid were rejected:
hand-written updates grow brittle as states multiply, and the others add packages,
shadow DOM styling, or compiler plugins. Automated browser rendering tests remain
future work.
