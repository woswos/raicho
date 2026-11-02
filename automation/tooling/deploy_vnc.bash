#!/usr/bin/env bash
# Open vncviewer on the Thunderbird desktop that make deploy-admin publishes.
# The arguments are the deployment's Compose command.
set -euo pipefail

if ! command -v vncviewer >/dev/null; then
    echo 'make deploy-vnc needs vncviewer, such as TigerVNC.' >&2
    exit 1
fi
if ! ADDRESS="$("${@}" port thunderbird 5900 2>&1)"; then
    if [[ ${ADDRESS} != *'no port 5900/tcp'* ]]; then
        printf '%s\n' "${ADDRESS}" >&2
        echo 'Could not look up the Thunderbird VNC port.' >&2
        exit 1
    fi
    ADDRESS=''
fi
if [[ ! ${ADDRESS} =~ ^.+:[1-9][0-9]*$ ]]; then
    echo 'The Thunderbird VNC port is not published. Run make deploy-admin first.' >&2
    exit 1
fi
exec vncviewer "${ADDRESS%:*}::${ADDRESS##*:}"
