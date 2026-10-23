#!/usr/bin/env bash
# Serialize offline database and secret-file changes so interrupted rotations are resumable.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIRECTORY}/../.." && pwd)"
cd "${REPOSITORY_ROOT}"

OPERATION="${1:-}"
if [[ ${#} != 1 || ! ${OPERATION} =~ ^(init|rotate|reactivate|revoke|verify|status)$ ]]; then
    echo 'Usage: bash runtime/credentials/raicho_connector.bash init|rotate|reactivate|revoke|verify|status' >&2
    exit 1
fi
PROJECT="${RAICHO_PROJECT:-${COMPOSE_PROJECT_NAME:-raicho}}"
STATE_DIRECTORY="${RAICHO_STATE_DIRECTORY:-${REPOSITORY_ROOT}/.raicho/${PROJECT}}"
if [[ ! ${PROJECT} =~ ^[a-z0-9][a-z0-9_-]*$ || ${STATE_DIRECTORY} != /* || -L ${STATE_DIRECTORY} ]]; then
    echo 'FAIL: use a valid Compose project and an absolute, non-symlink state directory' >&2
    exit 1
fi
if [[ ${RAICHO_COMPOSE_TEST:-0} != 0 && ${PROJECT} != raicho-credentials-* && ${PROJECT} != raicho-connector-* ]]; then
    echo 'FAIL: the test override requires a disposable raicho-credentials- or raicho-connector- project' >&2
    exit 1
fi
umask 077
mkdir -p -- "${STATE_DIRECTORY}"
if [[ $(stat -c '%u:%a' -- "${STATE_DIRECTORY}") != "$(id -u):700" ]]; then
    echo 'FAIL: state directory must belong to the caller and use mode 0700' >&2
    exit 1
fi
LOCK_PATH="${STATE_DIRECTORY}/operation.lock"
if [[ -L ${LOCK_PATH} ]] || { [[ -e ${LOCK_PATH} ]] &&
    { [[ ! -f ${LOCK_PATH} ]] || [[ $(stat -c '%u:%a' -- "${LOCK_PATH}") != "$(id -u):600" ]]; }; }; then
    echo 'FAIL: operation lock must be a private regular file owned by the caller' >&2
    exit 1
fi
exec {LOCK_DESCRIPTOR}>>"${LOCK_PATH}"
if ! flock --exclusive --nonblock "${LOCK_DESCRIPTOR}"; then
    echo 'FAIL: another credential operation is running' >&2
    exit 1
fi
STATE_DIRECTORY="$(cd "${STATE_DIRECTORY}" && pwd -P)"
export RAICHO_CREDENTIAL_DIRECTORY="${STATE_DIRECTORY}/credentials"
if [[ -L ${RAICHO_CREDENTIAL_DIRECTORY} ]]; then
    echo 'FAIL: credential directory must not be a symbolic link' >&2
    exit 1
fi
mkdir -p -- "${RAICHO_CREDENTIAL_DIRECTORY}"
sync -f "${STATE_DIRECTORY}"
COMPOSE=(docker compose -p "${PROJECT}" -f compose/compose.yaml -f compose/compose.credentials.yaml)
if [[ ${RAICHO_COMPOSE_TEST:-0} == 1 ]]; then
    COMPOSE+=(-f compose/compose.runtime_test.yaml)
fi

files() {
    "${COMPOSE[@]}" run --rm --no-deps -T credential_files "${1}" /credentials
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
        echo 'FAIL: reactivation requires an existing revoked credential or an active retry' >&2
        exit 1
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
                echo 'FAIL: credential preparation returned an invalid state' >&2
                exit 1
                ;;
        esac
        ;;
esac
database verify --token-file /credentials/connector.token
"${COMPOSE[@]}" up -d --no-deps --force-recreate --wait --wait-timeout 120 raicho gateway thunderbird
"${COMPOSE[@]}" exec -T thunderbird test -r /run/secrets/raicho_connector_token
"${COMPOSE[@]}" run --rm --no-deps -T credential_check
files finish >/dev/null
echo 'Credential digest, Thunderbird connection, and heartbeat verified. Services recreated.'
