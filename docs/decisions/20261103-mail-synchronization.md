# Rely on Thunderbird's periodic check for folder synchronization

- Status: accepted
- Date: 2026-11-03
- Deciders: Barkin Simsek

## Context

Stage 3 lists mailboxes and message summaries through standard WebExtension APIs.
The pinned Thunderbird 153.5.0 ESR answers `messages.list` and `messages.query`
from its local folder databases. No API asks an IMAP server for new messages or
new folders. The earlier draft experiment sometimes needed a native mail tab to
select a folder before restarted drafts became queryable.

The [compatibility matrix](../reference/mail-api-compatibility.md#synchronization-and-folder-discovery)
records the follow-up. Mail delivered to INBOX while Thunderbird was stopped was
visible at once after restart. Mail delivered to another folder appeared at the
first periodic check, and only with `check_all_folders_for_new`. Folders that
existed only on the server stayed unknown, because IMAP folder discovery runs when
the desktop folder pane expands an account.

## Decision

The managed Thunderbird policy sets `mail.server.default.check_all_folders_for_new`
to true with the `default` status. Thunderbird keeps its own account settings,
check interval, and IDLE behavior, and the desktop can still override the
preference per account.

Raicho does not select folders in a native mail tab, edit Thunderbird's databases,
or add a privileged Experiment to force synchronization. The browser shows the
folders and messages Thunderbird currently reports, as Thunderbird last
synchronized them, and a refresh lists them again.

## Consequences

Mail outside INBOX can appear up to one account check interval after a restart,
10 minutes by default. Every known IMAP folder is checked on that interval, which
adds IMAP traffic for large accounts. Folders created by another client appear
after Thunderbird's desktop expands the account again. Operators set up accounts
and reveal new folders in the administrative desktop.

The unattended mail compatibility run measures INBOX and non-INBOX discovery after
a restart without folder selection, so a Thunderbird upgrade that changes either
behavior fails that check. A future supported refresh API would replace the wait
for the periodic check.
