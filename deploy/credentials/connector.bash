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
require_private_directory "${STATE_DIRECTORY}"
umask 077
lock_state_layout
# make deploy-clean deletes everything inside a deployment's state directory, so state cannot nest.
# The walk follows the physical path, so a symlinked parent cannot hide another deployment.
PARENT="$(dirname -- "$(realpath -m -- "${STATE_DIRECTORY}")")"
while [[ ${PARENT} != / ]]; do
    if [[ -e ${PARENT}/operation.lock ]]; then
        fail "${STATE_DIRECTORY} is inside another deployment's state directory ${PARENT}"
    fi
    PARENT="$(dirname -- "${PARENT}")"
done
if [[ ! -e ${STATE_DIRECTORY} ]]; then
    mkdir -p -- "${STATE_DIRECTORY}"
    # A default ACL overrides the umask, so set the mode explicitly.
    chmod 700 -- "${STATE_DIRECTORY}"
fi
LOCK_PATH="${STATE_DIRECTORY}/operation.lock"
require_private_file "${LOCK_PATH}"
exec {LOCK_DESCRIPTOR}>>"${LOCK_PATH}"
# A default ACL overrides the umask, so set the lock mode explicitly.
chmod 600 -- "${LOCK_PATH}"
if ! flock --exclusive --nonblock "${LOCK_DESCRIPTOR}"; then
    fail 'another credential operation is running'
fi
# make deploy-clean deletes a state directory only when this marker names its project.
PROJECT_MARKER="${STATE_DIRECTORY}/project"
if [[ -L ${PROJECT_MARKER} ]] || { [[ -e ${PROJECT_MARKER} ]] && [[ ! -f ${PROJECT_MARKER} ]]; }; then
    fail 'the project marker must be a regular file'
fi
if [[ ! -e ${PROJECT_MARKER} ]]; then
    printf '%s\n' "${PROJECT}" >"${PROJECT_MARKER}"
elif [[ $(<"${PROJECT_MARKER}") != "${PROJECT}" ]]; then
    fail "${STATE_DIRECTORY} belongs to project $(<"${PROJECT_MARKER}"), not ${PROJECT}"
fi
unlock_state_layout
STATE_DIRECTORY="$(cd "${STATE_DIRECTORY}" && pwd -P)"
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
