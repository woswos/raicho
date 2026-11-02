# Publish native VNC for Thunderbird administration

- Status: accepted
- Date: 2026-11-02
- Deciders: Barkin Simsek

## Context

The [runtime stack decision](20261018-foundation-runtime-stack.md) selected opt-in
noVNC administration. With `compose.admin.yaml`, x11vnc serves the internal display
on the container's loopback interface, and websockify publishes noVNC on host
loopback port 6080. Native viewers such as TigerVNC `vncviewer` speak plain RFB
and cannot use the WebSocket endpoint, so administration needed a browser.

websockify already listens on every container interface. The isolation check
proves that Raicho cannot reach the Thunderbird container's addresses, and the
fixed gateway is the only other container on a Thunderbird network.

## Decision

In administration mode, x11vnc listens on the container's interfaces at port
5900, and `compose.admin.yaml` publishes it on host loopback as
`RAICHO_VNC_PORT`, default 5900. noVNC on `RAICHO_ADMIN_PORT` stays unchanged.
`make deploy-vnc` opens `vncviewer` on the deployment computer against the
published address and fails when the port is not published. It never starts or
recreates Thunderbird. Without the override, x11vnc does not run.
`make deploy-ps` lists the deployment's running containers with their published
ports, so an administrator can see whether the override is active.

## Consequences

Administrators can use a native viewer as well as a browser. The VNC port has no
password, like noVNC, so it must stay on host loopback. Viewing from another
computer needs an SSH tunnel or a desktop session on the deployment computer.
The runtime acceptance check covers both ports: published only on loopback,
unreachable from Raicho by Thunderbird's container addresses, and closed after
the override is removed. A second deployment on the same host needs its own
`RAICHO_VNC_PORT`.
