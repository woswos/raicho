#!/usr/bin/env bash
set -euo pipefail

for CONFIGURATION in package.json package-lock.json eslint.config.mjs; do
    if ! cmp -s "/workspace/${CONFIGURATION}" "/opt/quality/${CONFIGURATION}"; then
        echo "FAIL: ${CONFIGURATION} changed. Rebuild with docker compose -f compose/compose.tools.yaml build." >&2
        exit 1
    fi
done
if ! cmp -s /workspace/containers/tooling/requirements.txt /opt/quality/requirements.txt; then
    echo 'FAIL: Python tool dependencies changed. Rebuild with docker compose -f compose/compose.tools.yaml build.' >&2
    exit 1
fi
mkdir -p "${HOME}" "${CARGO_HOME}"
exec "${@}"
