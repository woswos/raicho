# Connector acceptance

Connector acceptance runs the production connector and the credential procedure
in disposable Docker deployments. See the
[contract](connector-contract.md), [build commands](build-test-generate.md),
[CI jobs](ci-cd.md), and [credential procedure](../operations/connector-credentials.md).
The dated results of the first acceptance are in the
[connector plan](../planning/active/20261018-foundation-stage-two-connector.md#acceptance-evidence).

## Scope

Every runner uses a uniquely named disposable project, fresh Thunderbird
profile, and generated fixture credentials. Production checks use control traffic
and fictional rejection canaries, without mail accounts. No personal
profile or provider credential is used. Each runner removes its owned containers,
volumes, networks, temporary credentials, and fixture image tags.

| Runner | Verifies |
| --- | --- |
| Production connector | Packaged XPI contents, runtime policy, one authenticated generation for ten minutes, rejected proofs and mail-canary payloads, restart and recreation of every service, network interruption, a changed Raicho address without gateway recreation, internal connector networks, browser-route and administrative isolation, a same-profile upgrade, and absence of the token and canaries from logs, diagnostics, and SQLite. |
| Credential procedure | Provisioning, persistence, rotation interruption at both publication points, revocation and restart rejection, explicit reactivation, file access, and token exclusion. |

## CI and reproduction

The workflow invokes the same commands used locally:

```bash
docker compose -f automation/tooling/compose.yaml build
docker compose -f automation/tooling/compose.yaml run --rm check \
  make lint format-check typecheck test-python test-tooling build-app test-app test-protocol
bash automation/acceptance/connector/check_connector.bash
bash automation/acceptance/credentials/check_credentials.bash
```

The `runtime-test` job also checks unconfigured startup, persistence,
administrative isolation, and independent readiness. Source regression tests
check CI runner coverage and label policy. Local command success does not
establish a hosted GitHub Actions result.

## Limits

- Production carries authentication and heartbeat only. Browser login, mail
  reads, mutations, and compose are planned in the
  [foundation plan](../planning/active/20261017-thunderbird-first-foundation.md).
- The ten-minute observation is bounded evidence for this pinned runtime and
  persistent MV2 background. It is not evidence for MV3 or future releases.
