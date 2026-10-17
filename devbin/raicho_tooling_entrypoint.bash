#!/usr/bin/env bash
set -euo pipefail

for CONFIGURATION in package.json package-lock.json eslint.config.mjs; do
    if ! cmp -s "/workspace/${CONFIGURATION}" "/opt/quality/${CONFIGURATION}"; then
        echo "FAIL: ${CONFIGURATION} changed. Rebuild with docker compose -f compose.tools.yaml build." >&2
        exit 1
    fi
done
mkdir -p "${HOME}" "${CARGO_HOME}"
exec "${@}"
