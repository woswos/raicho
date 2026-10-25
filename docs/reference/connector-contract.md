# Connector contract

The first connector contract defines connection control only. The production
Rust listener and TypeScript extension use its generated bindings and boundary
decoders for authentication and heartbeat. The
[acceptance record](connector-acceptance.md) describes production validation and
the [connector plan](../planning/done/20261018-foundation-stage-two-connector.md)
records the approved design.

See [architecture](architecture.md) for component boundaries and
[mail API compatibility](mail-api-compatibility.md) for the separate experiment.
No fixture command, account identity, message handle, or mail content belongs in
this contract. The backend kind is an identifier, not a Thunderbird-specific type.

Offline [credential provisioning](../operations/connector-credentials.md) now
persists one active digest or a revoked record. The Rust `Credential::parse`
boundary hashes the canonical 64-byte lowercase hexadecimal text with SHA-256,
and `CredentialStore::verify` compares digests in constant time while rejecting
revoked records. The transport reuses these boundaries after decoding an
authentication frame. An incoming frame never enrolls a token.

## Sources and generated outputs

- [Schema](../../protocol/schema/connector.schema.json): Draft 7, closed tagged
  objects and local definitions only. The generation guard restricts its vocabulary.
- [Limits](../../protocol/limits.json): shared constants, including frame sizes,
  authentication deadline, heartbeat timing, nesting, and connection budgets.
- [Shared fixtures](../../protocol/fixtures/): the same accepted/rejected frames,
  phases, expected generations, and error codes run in both languages.
- [Rust crate](../../protocol/rust/src/lib.rs): generated types and limits,
  embedded offline `jsonschema` validation, and a boundary decoder.
- [TypeScript project](../../protocol/typescript/src/decode_frame.ts): generated
  types and limits with a bundled Ajv standalone validator. No runtime Ajv,
  network schema retrieval, Node imports, or dynamic code generation is required.
- [Generation scripts](../../protocol/generator/): Python orchestration and
  JavaScript generation, with regression tests in its `tests/` directory.

Both implementations live under `protocol/`, with their own tests. The TypeScript
project is private ES modules and imports no Thunderbird APIs. The extension
imports those sources directly. Its XPI preserves the compiled `extension/src/`
and `protocol/typescript/src/` paths so browser module imports resolve inside the
archive. The background page remains at the archive root. Protocol fixtures and
tests are excluded from production packaging.

Use the boundary decoder on untrusted input. Deserializing a generated type or
calling the schema validator alone does not enforce frame size, phase, generation,
duplicate-member, or parsing rules. A valid authentication frame does not prove
that its token is accepted. Wire structs omit Rust `Debug`, and decoder errors
contain fixed codes without rejected input.

## Envelopes and direction

Every envelope carries `type` and `protocol_version: 1`. Additional members and
unknown message types are rejected. The first version accepts an empty capability
list only. Heartbeat is mandatory connection control, not an advertised mail feature.

| Type | Direction and phase | Fields beyond the common envelope |
| --- | --- | --- |
| `authenticate` | Connector to server, `authentication` | 256-bit lowercase hexadecimal token, backend kind/version, connector version, empty capabilities |
| `welcome` | Server to connector, `handshake` | Server-issued generation, empty capabilities, fixed heartbeat interval/timeout |
| `ping` | Server to connector, `server_control` | Current generation and bounded positive sequence |
| `pong` | Connector to server, `client_control` | Current generation and echoed sequence |
| `error` | Server to connector, handshake or control | Enumerated code, generation only after negotiation |

The decoder rejects a handshake error carrying a generation. A control error
requires the current generation. A connector cannot send an error envelope.
Error codes contain no free-text details or echoed credential. Supported codes
are defined in the schema, rather than accepted as arbitrary strings.

## Integration semantics

The internal listener accepts only the exact connector path, a single canonical
`moz-extension://<UUID>` Origin, and no WebSocket subprotocol. Origin is an
additional boundary check, not a substitute for the credential.

```mermaid
sequenceDiagram
    participant Connector
    participant Server
    Connector->>Server: authenticate
    Note over Server: Verify token and protocol before registration
    Server->>Connector: welcome with new generation
    Server->>Connector: ping with generation and sequence
    Connector->>Server: pong with the same generation and sequence
```

The server accepts one authentication frame within the shared deadline. It verifies
the credential digest before issuing a fresh random 128-bit generation and
registering the connection. The generation belongs to this connection, is never a
durable backend identity, and changes on replacement. Fencing and stale cleanup
compare it. Startup with an active credential begins disconnected. An authenticated
replacement fences the prior session, whose cleanup cannot clear the new state.

The server initiates heartbeat after welcome, with at most one outstanding ping.
Only its matching pong satisfies that ping. It uses the shared 15-second interval
and 45-second timeout and reconnects before sequence overflow. The decoder checks
generation and range, while the transport checks the outstanding sequence and
elapsed time.

An error is terminal for the connection. Authentication or protocol-version
rejection stops reconnect attempts until the extension restarts. Session replacement
also stops retries to avoid competing reconnect loops. Transient disconnects use
exponential backoff with jitter capped at 30 seconds, reset after a valid heartbeat.
Managed policy changes require Thunderbird restart. No command or mail operation
is replayed.

The internal listener caps accepted TCP connections at nine. Everything a client
sends before the server's 101 response must fit 8 KiB and arrive within five
seconds, and non-upgrade responses close their connection. The server allows four
pending authentications and one active session, with five
total upgraded sockets including sessions being closed. The authentication frame
has a five-second deadline and a 4 KiB decoded-frame limit. Credential lookup has
its own five-second bound, and a storage failure closes with retryable
`server_busy` instead of an authentication rejection. A connection lost without
a close frame is recorded as `disconnected`, and a frame over the transport limit
as `message_too_large`. The WebSocket allocation
limit is 64 KiB even before authentication, and control frames have the same
64 KiB limit. Writes are bounded to five seconds. Neither endpoint maintains an
application send queue, which is stricter than the shared eight-envelope ceiling.
The extension retries if its browser socket already has buffered data. Server
shutdown closes sessions before releasing database ownership.

## Parsing and limits

Frame budgets count UTF-8 bytes, including whitespace, before JSON decoding.
The authentication phase uses its smaller budget. Every object key and string
value must be printable ASCII. These are control envelopes, so this restriction
does not define the encoding of future mail content.

Native WebSocket Ping/Pong frames are handled separately. They neither
authenticate a connection nor satisfy or extend the application heartbeat.
Binary application frames are rejected.

Reject duplicate object members, including keys spelled with equivalent JSON
escapes. Reject nesting deeper than the shared limit, measured with the root at
depth zero. Reject non-finite numbers and invalid JSON. These checks happen before
version classification. An unsupported positive integer version within the
32-bit signed range produces `incompatible_version`. Malformed versions produce
`invalid_message`. Schema validation precedes phase and generation checks.

Equivalent integral numeric spellings such as `1`, `1.0`, and `1e0` are accepted.
Rust normalizes validated integral values before generated-type deserialization.
Sequences remain within the shared schema's 32-bit signed range, avoiding loss of
precision in JavaScript. Boundary, decimal-rounding, duplicate, surrogate, and
nesting regressions exercise agreement between the two decoders.

## Generation and verification

```bash
docker compose -f compose/compose.tools.yaml build
LOCAL_UID="$(id -u)" LOCAL_GID="$(id -g)" \
  docker compose -f compose/compose.tools.yaml run --rm format make generate-protocol
docker compose -f compose/compose.tools.yaml run --rm check make check-protocol test-protocol
```

Set `LOCAL_UID` and `LOCAL_GID` for writable generation as described in
[build commands](build-test-generate.md#checks-and-formatting). Generation builds
both language outputs in temporary directories before publishing changed files.
The check regenerates and compares bytes without changing the checkout. Schema
constants must agree with the limits file. Remote, file, and missing references
fail before generation. Review schema, generated changes, and corpus together.

`make lint` includes generation drift checks. Existing application tests cover
the Rust workspace and compiled extension, including shared contract fixtures.
Packaging tests require the production validator and exclude it from the separate
mail probe. The CSP test loads the standalone artifact with dynamic code
generation disabled. The [acceptance record](connector-acceptance.md) describes
the connector lifecycle checks that CI runs.
