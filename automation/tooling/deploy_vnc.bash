#!/usr/bin/env bash
# Open vncviewer on the Thunderbird desktop that make deploy-admin publishes.
# The arguments are the deployment's Compose command.
set -euo pipefail

if ! command -v vncviewer >/dev/null; then
    echo 'make deploy-vnc needs vncviewer, such as TigerVNC.' >&2
    exit 1
fi
ERRORS="$(mktemp)"
trap 'rm -f "${ERRORS}"' EXIT
if ! ADDRESS="$("${@}" port thunderbird 5900 2>"${ERRORS}")"; then
    if ! grep -q 'no port 5900/tcp' "${ERRORS}"; then
        cat "${ERRORS}" >&2
        echo 'Could not look up the Thunderbird VNC port.' >&2
        exit 1
    fi
    ADDRESS=''
fi
if [[ ! ${ADDRESS} =~ ^[^[:space:]]+:[1-9][0-9]*$ ]]; then
    echo 'The Thunderbird VNC port is not published. Run make deploy-admin first.' >&2
    exit 1
fi
rm -f "${ERRORS}"
trap - EXIT
exec vncviewer "${ADDRESS%:*}::${ADDRESS##*:}"
