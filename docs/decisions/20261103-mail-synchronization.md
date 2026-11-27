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
describes the unattended synchronization scenario. Its runs before 2026-11-27,
including two CI failures, measured a fixture fault. The fixture network has no
default route, so Gecko reported a link loss shortly after each start and
aborted every IMAP connection. A folder update cut off by the abort stayed
stale.

With the fault removed, a 2026-11-27 experiment ran each combination of
`check_all_folders_for_new` and offline download three times under a
one-minute check interval, without selecting a folder:

- **After a restart:** the check at login found mail in INBOX and `Projects`
  within 7 seconds when `check_all_folders_for_new` was true. With the
  preference false, offline auto-sync found `Projects` within 16 seconds. With
  offline download also off, `Projects` stayed empty for 150 seconds.
- **While Thunderbird ran:** mail appeared within 1 second in a folder where a
  cached connection waited in IMAP IDLE. Other folders waited for the periodic
  check, which found them within 56 seconds when `check_all_folders_for_new` was
  true. With the preference false, `Projects` stayed empty for 330 seconds,
  because auto-sync ran only at startup.

Thunderbird enables offline download and auto-sync by default, but not
`check_all_folders_for_new`. Folders that existed only on the server stayed
unknown, because IMAP folder discovery runs when the desktop folder pane expands
an account.

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

When the account checks for new mail and keeps the default
`check_all_folders_for_new`, Thunderbird refreshes every known folder at login.
Later mail outside INBOX appears at once in a folder that holds an idle
connection, and otherwise within one account check interval, 10 minutes by
default. An account that sets the preference to false gets one refresh from
auto-sync at startup, when offline download is on, and then leaves its unmarked
folders unchecked until the desktop opens them. The policy leaves
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
upgrade that loses either refresh fails that check. The check at login satisfies
it, so the run does not cover the periodic check while Thunderbird runs. It does
not assert that INBOX matches on the first query after login. A future supported
refresh API would replace the wait for the periodic check.
