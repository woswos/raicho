#!/usr/bin/env bash
# Set the browser password or end browser sessions while Raicho is stopped.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIRECTORY}/../.." && pwd)"
cd "${REPOSITORY_ROOT}"
# shellcheck source=deploy/credentials/state.bash
source "${SCRIPT_DIRECTORY}/state.bash"

OPERATION="${1:-}"
if [[ ${#} != 1 || ! ${OPERATION} =~ ^(init|reset|revoke|status)$ ]]; then
    echo 'Usage: bash deploy/credentials/login.bash init|reset|revoke|status' >&2
    exit 2
fi
select_deployment
claim_state_directory
COMPOSE=(docker compose -p "${PROJECT}" -f compose.yaml -f compose.login.yaml)

PASSWORD=''
if [[ ${OPERATION} == init || ${OPERATION} == reset ]]; then
    if [[ -t 0 ]]; then
        read -rsp 'New Raicho password (12 to 1024 bytes): ' PASSWORD
        echo
        read -rsp 'Repeat the password: ' CONFIRMATION
        echo
        if [[ ${PASSWORD} != "${CONFIRMATION}" ]]; then
            fail 'the passwords differ'
        fi
    else
        IFS= read -r PASSWORD || [[ -n ${PASSWORD} ]] || fail 'no password on standard input'
    fi
fi

# The server holds SQLite's instance lock, so it stops for the command and restarts if it was running.
RUNNING="$("${COMPOSE[@]}" ps --quiet --status running raicho)"
"${COMPOSE[@]}" stop raicho
printf '%s\n' "${PASSWORD}" | "${COMPOSE[@]}" run --rm --no-deps -T login "${OPERATION}"
if [[ -n ${RUNNING} ]]; then
    "${COMPOSE[@]}" up -d --no-deps --wait --wait-timeout 120 raicho
    echo 'Raicho restarted.'
else
    echo 'Raicho remains stopped.'
fi
