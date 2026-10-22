# Extension lifecycle evidence

This records the packaging experiment for the first slice of the
[Stage 2 connector plan](../planning/done/20261018-foundation-stage-two-connector.md).
The [build reference](build-test-generate.md#extension-lifecycle) owns commands,
and the [runtime reference](runtime.md#extension-installation) owns configuration.

## Scope

This historical experiment now lives in `extension/lifecycleprobe/`, packaged
separately from the production connector. Its results below describe the original
fixture versions. The production XPI uses the [control contract](connector-contract.md).

The fixture MV2 extension has a persistent background page and only the
`storage` permission. Its temporary lifecycle messages carry version, session,
and sequence metadata. They are a fixture protocol, not the production connector
contract. No mail commands, provider credentials, mail accounts, or mail data
are involved.

The fixture uses the production Thunderbird image with an isolated internal
network, its own profile, and a generated disposable token. There are no host
ports or desktop viewer. A separate listener reads the first-frame token,
stores sanitized observations, and requires recent heartbeats. Session identity
must survive idle and change after process restart or image upgrade.

## Results on 2026-10-18

The initial unit checks were run before implementation and failed for missing
extension modules, the XPI builder, policy generation, and listener state/check
modules. Focused tests then passed with those implementations present.

The disposable lifecycle runner passed on Linux amd64 with Thunderbird 153.5.0
ESR, UID/GID 10001, a read-only root, and no viewer or published host ports.

| Check | Observed result |
| --- | --- |
| Clean permanent installation | Packaged unsigned extension 0.1.0 connected and sent two heartbeats over 20 seconds. |
| Managed settings and policy symlink | Authentication used the runtime token. Policy path, mode 0600, directory mode 0700, force installation, and disabled automatic updates passed inspection. |
| Persistent background idle | Nine heartbeats over 90 seconds, with one background session and one connection. |
| Container restart | A new background session connected with version 0.1.0 and sent two heartbeats over 20 seconds. The profile marker remained. |
| Image upgrade on the same profile | Version 0.1.1 connected with a new background session and two heartbeats over 20 seconds. The profile marker remained. |
| Origin | `moz-extension://<profile-specific UUID>`, unchanged across restart and upgrade. This is an observation, not a complete authentication rule. |
| Cleanup | The runner removed its disposable containers, volumes, network, and image tags. |

The initial runtime run exposed a test-listener limitation: websockify normally
rejects text frames. The fixture now reuses its pinned frame decoder with a small
text-frame adapter and strict UTF-8 JSON validation. Regression tests cover text,
control, partial frames, and close handling. The corrected real-image run had no
fixture rejections. Production transport does not use this listener.

Focused Docker validation also passed six packaging tests, seven extension
behavior tests, 26 Thunderbird policy/supervision tests, and 20 fixture tests.
Packaging tests compare exact archive bytes and verify that the image artifacts
derive their default version from the manifest. TypeScript, language linting,
formatting, repository guards, and runtime Compose configuration were checked.

## Production acceptance

Subsequent slices have implemented credentials, production protocol, proxy routing, and
network recovery separately. Draft/send findings are in the
[mail compatibility matrix](mail-api-compatibility.md). The
[production acceptance record](connector-acceptance.md) covers the ten-minute
idle run, recovery, privacy checks, and CI integration. This document records the
separate lifecycle fixture.
