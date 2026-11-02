# Carry read-only mail requests over the authenticated session

- Status: accepted
- Date: 2026-11-03
- Deciders: Barkin Simsek

## Context

Stage 3 lists accounts, mailboxes, and message summaries from Thunderbird. The
connector session already authenticates both peers, signs every frame, and fences
replaced sessions by generation. Its channel has one owner, the server's session
task, and control frames are limited to 64 KiB. Version 1 frames allow printable
ASCII only, which cannot carry mail subjects and names. The mail probe's command
protocol is unauthenticated test code.

## Decision

Protocol version 2 adds three frames to the signed session. The server sends
`request` with a positive request identifier and one operation, and `cancel` to
abandon a request. The connector answers with `reply`, which carries the same
identifier and one result. The operations are `list_accounts`, `list_mailboxes`,
`list_messages`, `continue_list`, and `close_list`. Results are accounts,
mailboxes, or messages, each list with an optional cursor, `closed`, or an
enumerated error. Handles and cursors are random 22-character tokens that the
connector issues.

String values may hold any Unicode text without C0 control characters or unpaired
surrogates. Member names stay printable ASCII. Canonical JSON then escapes only
quotation marks and backslashes in both languages, so frame MACs still agree.

Every frame keeps the 64 KiB limit. The connector fills each page up to a byte
budget instead of a fixed count. Message bodies and attachments in stage 4 will be
sent as a sequence of frames within this limit, not as larger frames.

The session task stays the only writer. HTTP handlers place requests in a queue of
16, and the session keeps at most 16 awaiting a reply. A full queue fails at once
as busy. Each request has a 15-second deadline, after which the server sends
`cancel`, reports a timeout, and ignores a late reply. A reply to an identifier the
server never sent ends the session. A disconnect fails every queued and pending
request, and nothing is queued while disconnected. The connector holds at most 16
open lists and closes one that is idle for 5 minutes. No request is retried.

Both images still require the exact protocol version, as the
[version policy](20261026-thunderbird-connector.md#versioning) records.

## Consequences

Mail reads share the session's authentication, MACs, and generation fencing. A
long Thunderbird operation cannot block heartbeat, because the session multiplexes
both. Large folders need several pages, and the deadline bounds a slow
Thunderbird. A version 1 connector fails with `incompatible_version` until its
image is upgraded. Mutations in later stages reuse these frames, but they will
need per-item results and an explicit unknown outcome.
