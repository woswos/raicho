#!/usr/bin/env bash
# Browse fictional mail through the production stack, then check restarts, revocation, and privacy.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIRECTORY}/../../.." && pwd)"
cd "${REPOSITORY_ROOT}"
# shellcheck source=automation/acceptance/credential_deployment.bash
source automation/acceptance/credential_deployment.bash
# The credential wrapper accepts the test overlay only for a raicho-connector- project.
prepare_credential_deployment connector-browsing
export RAICHO_BROWSING_STATE="${RAICHO_STATE_DIRECTORY}/browsing"
mkdir -- "${RAICHO_BROWSING_STATE}"
# The driver runs as UID 10001 inside the private state directory.
chmod 777 -- "${RAICHO_BROWSING_STATE}"
COMPOSE+=(-f automation/acceptance/browsing/compose.browsing.yaml)

browser() {
    "${COMPOSE[@]}" run --rm --no-deps -T browser "${@}"
}

login() {
    "${COMPOSE[@]}" stop raicho
    printf '%s\n' "${PASSWORD}" | "${COMPOSE[@]}" -f compose.login.yaml run --rm --no-deps -T login "${1}"
    "${COMPOSE[@]}" up -d --no-deps --wait --wait-timeout 120 raicho
}

on_cleanup() {
    rm -f -- "${RAICHO_BROWSING_STATE}/password" "${RAICHO_BROWSING_STATE}/state.json"
    rmdir -- "${RAICHO_BROWSING_STATE}" 2>/dev/null || true
}
install_cleanup

docker compose -f automation/tooling/compose.yaml build
"${COMPOSE[@]}" build raicho thunderbird gateway
PASSWORD="$(head -c 18 /dev/urandom | base64 | tr -d '/+=')"
(umask 022 && printf '%s\n' "${PASSWORD}" >"${RAICHO_BROWSING_STATE}/password")
"${COMPOSE[@]}" up -d --no-deps greenmail
browser seed
bash deploy/credentials/connector.bash init
"${COMPOSE[@]}" up -d --no-deps --force-recreate --wait --wait-timeout 120 thunderbird
login init
browser browse
"${COMPOSE[@]}" restart thunderbird
browser stale
"${COMPOSE[@]}" restart raicho
browser persisted
login revoke
browser revoked
"${COMPOSE[@]}" logs --no-color raicho gateway | browser privacy
echo 'Browsing passed: login, sessions, pagination, stale handles, restarts, revocation, and privacy'
