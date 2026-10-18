# Connector acceptance

This records local acceptance of the production control connector from the
[approved design](../planning/done/20261018-foundation-stage-two-connector.md).
See the [contract](connector-contract.md), [build commands](build-test-generate.md),
[CI jobs](ci-cd.md), and [credential procedure](../operations/connector-credentials.md).

## Versions and scope

The 2026-10-18 run uses Linux amd64, Thunderbird 153.5.0 ESR, build
`20261013011825`, source stamp `9d5971ae648b0d17ab57509dcdcb0a06d3fdbe14`,
and production extension 0.2.0. The image-packaged XPI SHA-256 is
`a79470ab63de7d277cec9cf9ba655062294f72c7f26a3278ca240678550154b2`.
The proxy uses the digest-pinned Nginx version in its Dockerfile.

Every runner uses a uniquely named disposable project, fresh Thunderbird
profile, and generated fixture credentials. Production checks use control traffic
and fictional rejection canaries, without mail accounts. The separate mail experiment uses fictional GreenMail
accounts on an internal network. No personal profile or provider credential is used.

## Evidence

| Check | Local result on 2026-10-18 |
| --- | --- |
| Source and generated contract | Lint, formatting, type checks, protocol drift, tooling fixtures, application builds, and Rust/browser/production/lifecycle/mail probe tests passed. |
| Repository and acceptance regressions | 107 tests passed, including idle session changes/stalls, token/mail leakage, archive boundaries, CI coverage/labels, and cleanup on termination. |
| Thunderbird supervision and policy | 26 tests passed. |
| Basic runtime | Unconfigured startup, HTTP routing, SQLite/profile persistence across recreation, real-IP administrative isolation, listener closure, and readiness with Thunderbird stopped passed. |
| Production connector | One generation remained connected for 600 seconds, heartbeat count 1 to 41. Invalid-token/mail-payload rejection preserved the active session. Restart/recreation of every service, network interruption, changed Raicho IP without proxy recreation, browser-route isolation, and real-IP administrative isolation passed. Logs, diagnostics, and SQLite retained neither raw token nor mail canaries. |
| Credential operations | Provisioning, persistence, rotation interruption at both publication points, revocation/restart rejection, explicit reactivation, file access, and token exclusion passed. |
| Separate lifecycle fixture | 20 fixture tests and unattended 0.1.0 installation, 90-second same-session idle, restart, and 0.1.1 upgrade preserving the profile passed. |
| Unattended mail experiment | 51 fixture tests, draft/identity/attachment checks, and rediscovery after restart passed. Native and delivery-dependent phases reported `not_run`. |

All runners removed their owned containers, volumes, networks, temporary
credentials, and fixture image tags. Shared local build images remain available.

## CI and reproduction

The workflow invokes the same commands used locally:

```bash
docker compose -f compose/compose.tools.yaml build
docker compose -f compose/compose.tools.yaml run --rm check \
  make lint format-check typecheck test-tooling build-app test-app test-mail-probe
bash devbin/raicho_check_connector.bash
bash devbin/raicho_check_credentials.bash
bash devbin/raicho_check_extension_lifecycle.bash
bash devbin/raicho_check_mail_compatibility.bash
```

The existing `runtime-test` job also checks unconfigured startup, persistence,
administrative isolation, and independent readiness. Source regression tests
check CI runner coverage and label policy. Local command success does not
establish a hosted GitHub Actions result. No push or hosted run is part of this
acceptance record.

## Limits and follow-ups

- Production carries authentication and heartbeat only. Browser login, mail
  reads, mutations, and compose remain later foundation stages.
- The [mail compatibility matrix](mail-api-compatibility.md) records the earlier
  manual send-consent, native draft-editing, and fault evidence. CI repeats only
  the unattended draft/restart experiment and source tests. It does not automate
  native consent or claim native checks passed in CI.
- Standard programmatic draft replacement remains unproven. Native editing works,
  background saves can create duplicates, and restart discovery required native
  folder selection. Resolve these gates before dependent mail workflows.
- A send result does not prove Sent-copy success. Lost results remain `unknown`
  and are never automatically replayed.
- The ten-minute observation is bounded evidence for this pinned runtime and
  persistent MV2 background. It is not evidence for MV3 or future releases.
- Stage 5 had an unclassified rejection and a failed network recovery attempt.
  Native WebSocket Ping/Pong rejection was independently reproduced and fixed,
  but the earlier failures lacked evidence to establish their cause. Preserve
  that uncertainty rather than attributing those failures to the later fix.
  Neither failure recurred in the final Stage 5 or Stage 6 suites.
