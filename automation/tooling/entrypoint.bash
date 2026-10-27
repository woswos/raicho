#!/usr/bin/env bash
set -euo pipefail

for CONFIGURATION in package.json package-lock.json .npmrc eslint.config.mjs; do
    if ! cmp -s "/workspace/${CONFIGURATION}" "/opt/quality/${CONFIGURATION}"; then
        echo "FAIL: ${CONFIGURATION} changed. Run make on the host, which rebuilds the image first." >&2
        exit 1
    fi
done
if ! cmp -s /workspace/automation/tooling/requirements.txt /opt/quality/requirements.txt; then
    echo 'FAIL: Python tool dependencies changed. Run make on the host, which rebuilds the image first.' >&2
    exit 1
fi
mkdir -p "${HOME}" "${CARGO_HOME}"
exec "${@}"
