#!/usr/bin/env bash
# Serialize offline database and token-file changes so interrupted rotations are resumable.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIRECTORY}/../.." && pwd)"
cd "${REPOSITORY_ROOT}"
# shellcheck source=deploy/credentials/state.bash
source "${SCRIPT_DIRECTORY}/state.bash"

OPERATION="${1:-}"
if [[ ${#} != 1 || ! ${OPERATION} =~ ^(init|rotate|reactivate|revoke|verify|status)$ ]]; then
    echo 'Usage: bash deploy/credentials/connector.bash init|rotate|reactivate|revoke|verify|status' >&2
    exit 2
fi
select_deployment
if [[ ${RAICHO_COMPOSE_TEST:-0} != 0 && ${PROJECT} != raicho-credentials-* && ${PROJECT} != raicho-connector-* ]]; then
    fail 'the test override requires a disposable raicho-credentials- or raicho-connector- project'
fi
claim_state_directory
export RAICHO_CREDENTIAL_DIRECTORY="${STATE_DIRECTORY}/credentials"
if [[ -L ${RAICHO_CREDENTIAL_DIRECTORY} ]]; then
    fail 'credential directory must not be a symbolic link'
fi
mkdir -p -- "${RAICHO_CREDENTIAL_DIRECTORY}"
sync -f "${STATE_DIRECTORY}"
COMPOSE=(docker compose -p "${PROJECT}" -f compose.yaml -f compose.credentials.yaml)
if [[ ${RAICHO_COMPOSE_TEST:-0} != 0 ]]; then
    COMPOSE+=(-f automation/acceptance/runtime/compose.test.yaml)
fi

files() {
    "${COMPOSE[@]}" run --rm --no-deps -T credential-files "${1}" /credentials
}

database() {
    "${COMPOSE[@]}" run --rm --no-deps -T provisioner connector "${@}"
}

"${COMPOSE[@]}" stop raicho thunderbird
if [[ ${OPERATION} == reactivate ]]; then
    STATUS="$(database status)"
    if [[ ${STATUS} == 'connector: revoked' ]]; then
        ARCHIVE="$(mktemp -d "${STATE_DIRECTORY}/revoked.XXXXXXXX")"
        # A same-parent rename needs no write access inside the UID-10001 directory.
        mv -T -- "${RAICHO_CREDENTIAL_DIRECTORY}" "${ARCHIVE}"
        sync -f "${STATE_DIRECTORY}"
        mkdir -m 700 -- "${RAICHO_CREDENTIAL_DIRECTORY}"
        sync -f "${STATE_DIRECTORY}"
        echo "Preserved revoked configuration in ${ARCHIVE}"
    elif [[ ${STATUS} != 'connector: active' ]]; then
        fail 'reactivation requires an existing revoked credential or an active retry'
    fi
fi
case "${OPERATION}" in
    revoke | status)
        database "${OPERATION}"
        echo 'Core services remain stopped.'
        exit 0
        ;;
    verify)
        files check >/dev/null
        ;;
    init | rotate | reactivate)
        CANDIDATE="$(files "${OPERATION}")"
        case "${CANDIDATE}" in
            pending)
                ARGUMENTS=("${OPERATION}" --token-file /credentials/connector.pending)
                if [[ ${OPERATION} == rotate ]]; then
                    ARGUMENTS+=(--current-token-file /credentials/connector.token)
                fi
                database "${ARGUMENTS[@]}"
                files publish >/dev/null
                ;;
            current)
                if [[ ${OPERATION} == init ]]; then
                    database init --token-file /credentials/connector.token
                fi
                ;;
            *)
                fail 'credential preparation returned an invalid state'
                ;;
        esac
        ;;
esac
database verify --token-file /credentials/connector.token
"${COMPOSE[@]}" up -d --no-deps --force-recreate --wait --wait-timeout 120 raicho gateway thunderbird
"${COMPOSE[@]}" exec -T thunderbird test -r /run/secrets/raicho_connector_token
"${COMPOSE[@]}" run --rm --no-deps -T credential-check
files finish >/dev/null
echo 'Credential keys, Thunderbird connection, and heartbeat verified. Services recreated.'
