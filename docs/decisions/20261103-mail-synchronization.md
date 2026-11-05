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
describes the unattended synchronization scenario. In its 2026-11-03 run, mail
delivered to INBOX while Thunderbird was stopped was visible at once after
restart. Mail delivered to `Projects` appeared after 56 seconds under a
one-minute check interval, and only with `check_all_folders_for_new`. With the
preference explicitly false, the folder stayed empty for the 150-second
deadline. Folders that existed only on the server stayed unknown, because IMAP
folder discovery runs when the desktop folder pane expands an account.

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
10 minutes by default, when the account checks for new mail. The policy leaves
`check_new_mail` and the interval to the account, which Thunderbird's wizard
enables, and Thunderbird skips a check while the server is busy or waits for a
password. Every known IMAP folder except Trash is checked on that interval,
which adds IMAP traffic for large accounts. The check compares the server's
unseen count, total message count, and next UID with the local database and
updates a folder only when one of them differs. A read or unread change triggers
the update only when it moves the unseen count. Offsetting read and unread
changes, and star or tag changes, leave those values unchanged and stay stale in
an unopened folder until the desktop opens it. No preference marks Trash for the
check, so it refreshes when
the desktop opens it or its folder properties enable new-mail checks. Folders
created by another client appear after
Thunderbird's desktop expands the account again, and under the default
subscription setting only once the desktop subscribes to them. Operators set up
accounts, subscribe to new folders, and mark folders for checks in the
administrative desktop.

The unattended mail compatibility run requires INBOX and non-INBOX discovery
within its deadline after a restart without folder selection, so a Thunderbird
upgrade that loses either refresh fails that check. It does not assert that INBOX
matches on the first query after login. A future supported refresh API would
replace the wait
for the periodic check.
