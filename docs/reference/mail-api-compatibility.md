# Mail API compatibility experiment

This records standard Thunderbird mail API behavior observed with a separate
probe extension, as designed in the
[connector plan](../planning/done/20261018-foundation-stage-two-connector.md).
Results apply to the versions below, not supported product capabilities.
Browser compose and production mail commands
remain outside this experiment.

## Versions and isolation

| Component | Tested version |
| --- | --- |
| Thunderbird | 153.5.0 ESR, Linux amd64 |
| Thunderbird build ID | `20261013011825` |
| Thunderbird source stamp | `9d5971ae648b0d17ab57509dcdcb0a06d3fdbe14` |
| Mail probe | 0.1.1 full interactive experiment, 0.1.2 unattended restart follow-up, 2026-11-03 synchronization follow-up, persistent Manifest V2 background page |
| GreenMail | 2.1.14, Linux amd64 |
| GreenMail image digest | `sha256:2bcd0470f569af3c8b98509421b23f1ad11ebb2d58c3648f4233bf450f3b5e2b` |

The [test Compose deployment](../../mailprobe/compose.yaml) creates a fresh
Thunderbird profile, fictional accounts, disposable credentials, and an internal
Docker network. It has no route to real mail providers or published ports. The
optional [administration override](../../mailprobe/compose.admin.yaml) enables
the desktop listener only inside that fixture network.

The separate [probe extension](../../mailprobe/manifest.json) calls
standard Thunderbird APIs. It takes the production extension ID, so the unchanged
Thunderbird image installs it through the same managed policy and configuration.
A [test controller](../../mailprobe/tests/probe/control_server.py)
issues correlated commands without replaying them after disconnects. The
[mail proxy](../../mailprobe/tests/proxy/fault_server.py) forwards SMTP and IMAP
to GreenMail and injects bounded failures. Direct
[IMAP inspection](../../mailprobe/tests/proxy/mail_inspect.py) checks the fictional
mail independently of the extension's result. Only the test profile initializer
accesses the fixture profile. Raicho's server has no profile access.

The production XPI retains its separate manifest and excludes mail probe modules,
permissions, fixture accounts, and message content. Packaging tests enforce that
boundary. This deployment is not a production mail backend or connector protocol.

## Observed behavior of Thunderbird 153.5.0 ESR

| Operation | Evidence and current result |
| --- | --- |
| Background plain-text draft save | Observed a correct draft in GreenMail after `messages.saveMessage()`. |
| HTML draft, attachment, selected identity | Observed HTML, the small attachment, and `alias@raicho.test` in the saved draft. |
| Save result identity | Successful saves can return `{mode: "draft", messages: []}`. The message can be found by query after Thunderbird settles. An empty result is not proof that no draft was saved. |
| Programmatic reopen | `compose.beginNew(existingMessageId)` opens composition type `new`. The original draft remains. This does not establish in-place draft editing. |
| Repeated background save | Two calls created two drafts. No replacement operation was inferred. |
| Repeated save in the same compose tab | One edited draft after two saves, with the second body stored. The first saved numeric ID then returned `Message not found`. |
| Draft rediscovery after Thunderbird restart | Folder plus RFC Message-ID located drafts. Numeric IDs changed. The unattended run needed one native-tab folder selection through the standard API after its initial query returned empty. |
| Folder discovery | `Sent` and `Trash` existed on the server before Thunderbird first started, and the extension never saw them. Thunderbird listed only folders it had created or opened, such as `Drafts` and a folder made through `folders.create`. |
| Background synchronization after restart | Mail appended to INBOX and `Projects` while Thunderbird was stopped. INBOX matched on the first query after restart. With `check_all_folders_for_new`, `Projects` matched after 56 seconds under a one-minute check interval. With the preference explicitly false, `Projects` stayed empty for 150 seconds. No folder was selected. |
| Native reopen, edit, and resave | Native Edit opened type `draft`. Editing Subject/body and pressing Ctrl+S left one replacement and zero original-subject drafts. The alias and attachment digest were preserved. |
| Permission to send | `messages.send` is optional-only in this runtime and requires an explicit native permission grant. Force installation does not grant it. |
| `sendLater` and Thunderbird-owned queue | Message remained in Local Folders/Outbox across restart. No recipient delivery. Startup asked whether to send unsent mail, and the native check chose Later. |
| Immediate send | Exactly one fixture arrival with alias, HTML, and attachment digest verified. API returned `sendNow`, RFC Message-ID, and an empty copy list. |
| Invalid input | Probe rejected a non-string subject. Thunderbird rejected missing recipients and an unknown identity. |
| SMTP rejection | One injected recipient rejection, zero SMTP acceptances and deliveries. Native error dialog appeared. The observer timed out at 30 seconds with `unknown`. |
| Lost connector result | Test controller discarded the successful response and disconnected. Reconnection occurred, with exactly one SMTP acceptance and arrival. Caller retained `unknown`, no replay. |
| Lost SMTP acceptance acknowledgment | Proxy accepted one real submission and dropped its reply. Recipient received one message, while the observer timed out with `unknown`. |
| SMTP acceptance followed by Sent-copy failure | One acceptance and one rejected Sent APPEND, one recipient arrival, zero Sent copies. API nevertheless returned success, `sendNow`, RFC Message-ID, and `messages: []`. |

### Interpreting draft results

Inspection of `ext-messages.js` inside the pinned Thunderbird `omni.ja` explains
the empty save result. `MsgOperationWrapper` collects saved Message-IDs and
`msgsClassified` notifications separately. Its return value includes only saved
messages classified before the operation promise resolves, filtering missing
headers without turning a successful save into an error. The fixture therefore
checks settled Thunderbird queries and independent IMAP evidence. It must not
automatically repeat a save merely because the returned header list is empty.

On restart, query-only attempts remained empty for the 30-second observation
window. The successful unattended follow-up first recorded an empty query, then
selected Drafts once through MV2 `mailTabs.update({displayedFolder: folderId})`.
Subsequent queries found all three target drafts without saving again. The
evidence records `initial_matches` and `folder_selection_required` per draft.
This requires a native mail tab, but no viewer or manual click.

Pinned-runtime source inspection shows ordinary `messages.query()` enumerating
cached folder messages, without an IMAP refresh. Its `online` branch applies to
NNTP. Folder synchronization explains the observed selection dependency, but
the experiment does not establish a general background IMAP discovery strategy.
Native-tab selection changes Thunderbird's UI. Record that dependency before
building mailbox discovery, rather than editing its mail database.

### Synchronization and folder discovery

The unattended synchronization scenario stops Thunderbird, appends a message to
INBOX and `Projects` over IMAP, starts it again, and never selects a folder. In
the unattended run its 150-second deadline starts when the host script starts
Thunderbird, so the time to connect and list folders counts against it. The
native run starts the deadline when the driver runs, after the operator confirms
the restarted mail window, so operator time does not count. Thunderbird checks INBOX at login. Another folder is refreshed when the desktop
opens it, or by the periodic new-mail check when `check_all_folders_for_new` is
true or the folder's properties mark it for new-mail checks. The forced check
skips Trash unless it is marked, so mail that another client moves into Trash
appears after the desktop opens that folder. The check compares the server's
unseen count, total message count, and next UID with the local database and
updates the folder only when one of them differs. A read or unread change triggers
the update only when it moves the unseen count. Offsetting read and unread
changes, and star or tag changes, leave those values unchanged and stay stale
until the desktop opens the folder. The
production policy sets `mail.server.default.check_all_folders_for_new` as a
default preference. Thunderbird's account wizard writes `check_new_mail`, the
check interval, and `login_at_startup` for each server, but not this preference,
so the default reaches new accounts. A per-account setting in the desktop still
overrides it. Mail in a folder other than INBOX can therefore appear up to one
check interval after a restart when the account checks for new mail, and later
when Thunderbird skips a check because the server is busy or waits for a
password. Thunderbird's default interval is 10 minutes.

IMAP folder discovery is a separate limit. The pinned `about3Pane.js` asks the
server to discover mailboxes when a person expands the account in the folder pane.
No WebExtension API starts that discovery, and `folders.query` and
`accounts.list` report only folders that Thunderbird already knows. Under
Thunderbird's default `using_subscription` setting, discovery lists only
subscribed folders. A folder that another client creates therefore appears after
the desktop subscribes to it, or after the account stops showing only subscribed
folders, and the account is expanded again. The fixture account turns
subscriptions off, so the unattended run does not cover the default setting.
Raicho shows the folders Thunderbird reports and does not select folders in a
native tab. See the [synchronization decision](../decisions/20261103-mail-synchronization.md).

The edit-as-new result does not authorize a save-new/delete-old replacement
strategy. Native draft interoperability and a standard programmatic replacement
operation are separate acceptance gates. Dependent compose work needs a design
decision if the latter remains unsupported.

### Submission, copies, and uncertainty

A successful send result establishes submission, not successful Sent storage.
The primary Sent-copy failure above was not reported as an API error. Do not
infer copy success from an empty `messages` list or infer non-submission from a
timeout. Native error dialogs can also delay a background operation's result.
The fixture dismissed an SMTP rejection report without requesting a retry.

The controller and extension never replay a command after losing its result.
Fault counters independently prove the injected conditions were exercised.
The final observation checks all four submitted subjects again after 30 seconds,
requiring exactly one arrival per subject and no queued or rejected deliveries.
This is bounded experimental evidence, not a universal delivery guarantee.

## Running the experiment

The [host runner](../../mailprobe/tests/check_mail_compatibility.bash) orchestrates
Docker builds, uniquely named disposable services, and cleanup. Its commands are in
[build, test, and generate](build-test-generate.md#mail-api-compatibility).

The default run covers unattended draft checks. The native run adds the desktop
permission checkpoint, sending scenarios, and native draft interoperability.
Grant `messages.send` through Thunderbird's permission UI when prompted. The
native flow is interactive and is not evidence of unattended permission granting.
No real account, personal profile, or provider credential belongs in either run.

CI runs probe source tests and the default unattended runner, including the
synchronization scenario. It explicitly skips consent-dependent delivery, native
editing, and interactive fault checks.
Their observations above remain the separately recorded manual evidence. Some
unattended runs find every restarted draft before the folder-selection fallback,
so that synchronization dependency is intermittent rather than resolved. The
[connector plan](../planning/done/20261018-foundation-stage-two-connector.md#acceptance-evidence)
records the individual runs.

The controller stores observations only in the disposable fixture volume. Review
its evidence before cleanup and update this matrix with actual results. A timeout
or disconnected observer remains `unknown` unless separate evidence establishes
what happened. No scenario automatically resends an uncertain operation.

## References

- [Thunderbird messages API](https://webextension-api.thunderbird.net/en/esr-mv2/messages.html)
  documents background save/send operations. The published page identifies
  153.3.1 ESR, so runtime observations above take precedence for this experiment.
- [Thunderbird compose API](https://webextension-api.thunderbird.net/en/esr-mv2/compose.html)
  distinguishes composition windows from background operations.
- [Thunderbird folders API](https://webextension-api.thunderbird.net/en/esr-mv2/folders.html)
  and [mailTabs API](https://webextension-api.thunderbird.net/en/esr-mv2/mailTabs.html)
  describe folder inspection and native tab selection.
- [GreenMail](https://greenmail-mail-test.github.io/greenmail/) supplies the
  disposable SMTP and IMAP endpoints.
