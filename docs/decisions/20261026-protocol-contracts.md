# Protocol contracts

- Status: accepted
- Date: 2026-10-26
- Deciders: Barkin Simsek

## Context

The Rust server, the Thunderbird extension, and the browser page exchange messages
that each language must parse identically. Parsers written separately per language
drift, and a TypeScript implementation kept inside the extension hides that it
implements the same rules as the Rust one. The browser's `/api/status` response
also crosses a language boundary, carrying connector state to the page.

## Decision

Keep shared contracts and both language implementations in `protocol/`. The
connector schema in `protocol/schema/`, `protocol/limits.json`, and
`protocol/diagnostics.json` are the sources. `protocol/generator/` produces the
Rust bindings in `protocol/rust/`, the TypeScript bindings and a standalone
validator in `protocol/typescript/`, and the decoders' error codes for both
languages. `make check-protocol` fails when committed output drifts. Shared
fixtures in `protocol/fixtures/` pin both implementations, including the
authentication vectors and the connector configuration rules that the Thunderbird
runtime also applies.

The TypeScript package has private ES module metadata, its own TypeScript
configuration, and tests that run independently against the shared fixtures. The
extension imports the shared sources directly, and the production XPI compiles
from the repository root so relative module paths resolve inside the archive.
Extension-specific code and integration tests stay in `extension/`.

### Status API

Describe `/api/status` in `protocol/schema/status.schema.json`, with closed objects
and the 503 `unavailable` body. The generation guard requires its state and error
lists to equal `protocol/diagnostics.json`. The generator emits the browser's types
and a bundled standalone validator. The page validates every response with it,
keeps only the fields it displays, and shows the connector state when the database
is unavailable. Shared documents in `protocol/fixtures/status/` run against the
Rust and browser validators, the server's HTTP tests validate real responses, and
the acceptance check reads its expected members from the schema. The server keeps
hand-written response structs, held to the schema by tests, because its fields
come from the generated diagnostics enums.

## Consequences

Each contract has one source, and both implementations and their tests are
discoverable under one tree. The production XPI includes compiled modules under
`extension/src/` and `protocol/typescript/src/` and needs no published npm package.
Its packaging checks verify that module imports resolve within the archive. The
page rejects undocumented response members, so the server and page change
together, which a single image already guarantees. The future mail API can follow
the status API's pattern.
