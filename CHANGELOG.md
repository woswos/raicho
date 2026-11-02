# Changelog

Notable changes to Raicho. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Connect Thunderbird to Raicho through a packaged extension that authenticates
  with a challenge-response handshake, then signs and verifies every later frame,
  and answers heartbeats.
- Run a fixed internal gateway that is the only network path between Raicho and
  Thunderbird.
- Provision, rotate, revoke, and reactivate the connector credential offline
  with `deploy/credentials/connector.bash`.
- Show Thunderbird connection status and failure reasons on the diagnostics page
  and in `/api/status`.
- Publish the Thunderbird administration desktop to native VNC viewers on
  loopback port 5900, opened with `make deploy-vnc`.
- List a deployment's running containers with `make deploy-ps`.
- Check a running deployment without stopping it with `make deploy-health`, and
  read logs, restart containers, or open a shell with `make deploy-logs`,
  `make deploy-restart`, and `make deploy-shell`.
- Print every Make target with `make help`, which a bare `make` now runs.
- Open the tooling container with `make shell`, and run selected tests with
  `TEST=` for `test-python` and `test-server`.
- Check lockfiles against known security advisories with `make audit`.
