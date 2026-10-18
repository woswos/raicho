# Mail API compatibility experiment

This records the second slice of the
[Stage 2 connector plan](../planning/done/20261018-foundation-stage-two-connector.md).
Results apply to the versions below, not supported product capabilities.
Browser compose and production mail commands
remain outside this experiment.

## Versions and isolation

| Component | Tested version |
| --- | --- |
| Thunderbird | 153.5.0 ESR, Linux amd64 |
| Thunderbird build ID | `20261013011825` |
| Thunderbird source stamp | `9d5971ae648b0d17ab57509dcdcb0a06d3fdbe14` |
| Mail probe | 0.1.1 full interactive experiment, 0.1.2 unattended restart follow-up, persistent Manifest V2 background page |
| GreenMail | 2.1.14, Linux amd64 |
| GreenMail image digest | `sha256:2bcd0470f569af3c8b98509421b23f1ad11ebb2d58c3648f4233bf450f3b5e2b` |

The [test Compose deployment](../../compose/compose.mail_test.yaml) creates a fresh
Thunderbird profile, fictional accounts, disposable credentials, and an internal
Docker network. It has no route to real mail providers or published ports. The
optional [administration override](../../compose/compose.mail_admin.yaml) enables
the desktop listener only inside that fixture network.

The separate [probe extension](../../extension/mail_probe/manifest.json) calls
standard Thunderbird APIs. A [test controller](../../containers/mail_probe/control_server.py)
issues correlated commands without replaying them after disconnects. The
[mail proxy](../../containers/mail_test/fault_server.py) forwards SMTP and IMAP
to GreenMail and injects bounded failures. Direct
[IMAP inspection](../../containers/mail_test/mail_inspect.py) checks the fictional
mail independently of the extension's result. Only the test profile initializer
accesses the fixture profile. Raicho's server has no profile access.

The production XPI retains its separate manifest and excludes mail probe modules,
permissions, fixture accounts, and message content. Packaging tests enforce that
boundary. This deployment is not a production mail backend or connector protocol.

## Observations on 2026-10-18

| Operation | Evidence and current result |
| --- | --- |
| Background plain-text draft save | Observed a correct draft in GreenMail after `messages.saveMessage()`. |
| HTML draft, attachment, selected identity | Observed HTML, the small attachment, and `alias@raicho.test` in the saved draft. |
| Save result identity | Successful saves can return `{mode: "draft", messages: []}`. The message can be found by query after Thunderbird settles. An empty result is not proof that no draft was saved. |
| Programmatic reopen | `compose.beginNew(existingMessageId)` opens composition type `new`. The original draft remains. This does not establish in-place draft editing. |
| Repeated background save | Two calls created two drafts. No replacement operation was inferred. |
| Repeated save in the same compose tab | One edited draft after two saves, with the second body stored. The first saved numeric ID then returned `Message not found`. |
| Draft rediscovery after Thunderbird restart | Folder plus RFC Message-ID located drafts. Numeric IDs changed. The unattended run needed one native-tab folder selection through the standard API after its initial query returned empty. |
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

The [host runner](../../devbin/raicho_check_mail_compatibility.bash) orchestrates
Docker builds, source tests, uniquely named disposable services, and cleanup:

```bash
bash devbin/raicho_check_mail_compatibility.bash
bash devbin/raicho_check_mail_compatibility.bash --native
```

The default run covers unattended draft checks. The native run adds the desktop
permission checkpoint, sending scenarios, and native draft interoperability.
Grant `messages.send` through Thunderbird's permission UI when prompted. The
native flow is interactive and is not evidence of unattended permission granting.
No real account, personal profile, or provider credential belongs in either run.

The full interactive experiment was executed phase by phase on probe 0.1.1,
including native consent, native editing, restart, delivery faults, and final
settlement. The complete default runner then passed on probe 0.1.2 with the
folder-selection follow-up. Containerized validation also passed 51 fixture
Python tests, 15 probe TypeScript tests, and 65 repository tests including the
production/probe packaging boundary. These local results are not a CI run.
CI now runs probe source tests and the default unattended runner. It explicitly
skips consent-dependent delivery, native editing, and interactive fault checks.
Their observations above remain the separately recorded manual evidence.

The final acceptance rerun also passed unattended drafts and restart with probe
0.1.2. All three restart queries found their draft before the folder-selection
fallback, unlike the earlier run. This does not remove the previously observed
synchronization dependency or establish a general background discovery strategy.

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
