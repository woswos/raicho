# Thunderbird connector

- Status: accepted
- Date: 2026-10-26
- Deciders: Barkin Simsek

## Context

The foundation needs unattended Thunderbird connectivity without exposing its
administrative desktop or copying mail into Raicho. The approved
[connector design](../planning/done/20261018-foundation-stage-two-connector.md)
defines the experiment and implementation boundaries. Thunderbird keeps internet
egress for its mail providers, and Docker's embedded DNS forwards names it cannot
resolve to the host's resolvers. The network path and name resolution therefore
cannot prove that the extension reached the genuine server. Later mail commands
will travel the same channel as authentication and heartbeat.

## Decision

### Packaging and transport

Package a persistent Manifest V2 extension with managed startup configuration in
the pinned Thunderbird image. It connects outbound over WebSocket through a fixed,
unprivileged Nginx gateway to a dedicated Rust listener, separate from the public
listener that serves the browser and connection diagnostics. The generated,
versioned [control contract](../reference/connector-contract.md) carries
authentication and heartbeat, and production mail capabilities stay empty. SQLite
stores the credential keys and revocation state. The
credential procedure (`docs/operations/connector-credentials.md`) owns private host
files, offline changes, interruption recovery, and live verification.

The same Docker source and unattended acceptance commands run locally and in CI.
The mail probe stays a separate test artifact. Native consent, draft
interoperability, and interactive fault observations remain separately identified
evidence in the compatibility matrix (`docs/reference/mail-api-compatibility.md`).

### Network isolation

The gateway joins only two `internal: true` networks. `connector-application`
joins it to Raicho, and `connector-thunderbird` joins it to Thunderbird. Raicho
keeps `application` for its published browser port, and Thunderbird keeps
`thunderbird` for provider access. No network joins Raicho and Thunderbird
directly. Docker Engine 26 and newer never forwards DNS queries for a container
attached only to internal networks, so a stopped `raicho` stays unresolved.
Connector acceptance checks the network membership and internal flags of the
running deployment.

### Listener

The connector listener accepts WebSockets directly with tokio-tungstenite on the
accepted TCP stream, and Axum keeps the public listener without its WebSocket
feature. This narrows the [runtime stack decision](20261018-foundation-runtime-stack.md)
for connector traffic only. A header callback checks the path, origin, query, and
subprotocol, and takes a pending-authentication slot or answers 503. A byte-capped
stream limits the upgrade request to 8 KiB until the handshake returns. One
semaphore bounds open sockets, with room for excess upgrades to receive a 503, and
another bounds pending authentications. One `authentication_deadline_ms` deadline
runs from TCP accept through the upgrade, challenge, authentication frame, and
credential lookup.

### Handshake

Authenticate with a SCRAM-style challenge-response. The server sends a fresh
256-bit nonce. The connector answers with its own nonce and a proof over a
transcript of both nonces and the authentication metadata. The welcome carries the
server's signature over the same transcript. The connector key is an HMAC-SHA256
of a fixed label under the token, and SQLite stores its SHA-256 as the stored key
together with a separately derived server key. The proof is the connector key XOR
an HMAC of the transcript under the stored key, so the server can verify it
without being able to produce it. The token never crosses the connection.

### Frame authentication

Every frame after welcome carries an HMAC-SHA256 `mac`. Both sides derive a
session key under the server key from the transcript and the generation. Each MAC
covers the sender, the sender's implicit frame counter, and the frame's canonical
JSON without `mac`. Including the generation in the key authenticates the
welcome's generation without changing the welcome or its signature. Frames are
not encrypted. The gateway has no outbound route, so a compromised gateway could
tamper but not exfiltrate, and integrity removes the tampering. TLS would add
certificate provisioning and rotation for no further gain on internal networks.

The connector trusts nothing from the server until the welcome signature
verifies, and afterwards trusts no close code and no frame it cannot authenticate.
It retries with capped backoff after every close, decoding failure, unauthenticated
error, and MAC failure, and stops only on an authenticated `session_replaced`.

### Versioning

Upgrade the Raicho and Thunderbird images together. Both come from one checkout
and one Compose project, so every protocol change bumps `protocol_version` and
ships in the same release of both images. The exact-match check stays without a
negotiated range. During an upgrade, a mismatched connector fails before
authentication with `incompatible_version` and retries until both sides match.
The Thunderbird image is independently built, meaning it has its own recipe
instead of an upstream image, not its own release cycle.

## Consequences

Raicho readiness stays independent of Thunderbird. Bounded control messages,
generation fencing, heartbeat, and retries make disconnect behavior explicit. A
captured proof cannot be replayed, and a spoofed endpoint can neither learn a
usable secret nor stop the connector. Injected, altered, replayed, reordered, and
reflected frames fail, and mail commands can use the same channel without another
protocol change. A database copy can impersonate the server and derive session
keys. Alone it cannot impersonate the connector, but with one captured
authentication exchange it recovers the connector key, as in SCRAM, and can then
authenticate as the connector until the credential is rotated. A wrong token or a genuine protocol
rejection retries at the capped interval instead of stopping. Policy changes, and
a connector stopped by an authenticated `session_replaced`, require restarting
Thunderbird.

The gateway has no egress or outside DNS fallback. Thunderbird still resolves
`gateway` through a container that has egress, so a stopped gateway can send that
name to outside DNS, where the handshake keeps the token off the wire. The
listener owns its accept loop, including transient accept errors and shutdown.
Operators recreate both containers after an upgrade. Shipping the Thunderbird image
on its own schedule, or supporting separately released backends, would need a
supported version range and a new decision. Gateway packaging and secret-file
operations add maintenance.

The API experiment leaves programmatic draft replacement unproven. Future compose
work must resolve that limitation, native send consent, and uncertain send outcomes
before exposing mail operations. See the
acceptance evidence (`docs/reference/connector-acceptance.md`) for measured scope.
