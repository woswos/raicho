#!/usr/bin/env bash
# Exercise credential recovery only in an isolated deployment with disposable secrets.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIRECTORY}/../../../.." && pwd)"
cd "${REPOSITORY_ROOT}"

export RAICHO_PROJECT
RAICHO_PROJECT="raicho-credentials-$(date -u +%Y%m%d%H%M%S)-${RANDOM}"
export RAICHO_STATE_DIRECTORY
RAICHO_STATE_DIRECTORY="$(mktemp -d /tmp/raicho-credentials.XXXXXXXX)"
export RAICHO_CREDENTIAL_DIRECTORY="${RAICHO_STATE_DIRECTORY}/credentials"
export RAICHO_COMPOSE_TEST=1
mkdir -m 700 "${RAICHO_CREDENTIAL_DIRECTORY}"
COMPOSE=(docker compose -p "${RAICHO_PROJECT}" -f compose/compose.yaml
    -f compose/compose.credentials.yaml -f compose/compose.runtime_test.yaml)

fixture() {
    docker run --rm -i --network none --read-only --user 0:0 \
        --cap-drop ALL --cap-add CHOWN --cap-add DAC_OVERRIDE --cap-add FOWNER \
        --security-opt no-new-privileges:true \
        --mount "type=bind,source=${SCRIPT_DIRECTORY}/raicho_credential_checks.py,target=/checks.py,readonly" \
        --mount "type=bind,source=${RAICHO_STATE_DIRECTORY},target=/fixture" \
        --mount "type=volume,source=${RAICHO_PROJECT}_raicho-data,target=/database" \
        --entrypoint python3 raicho-tools:local -B /checks.py "${@}"
}

cleanup() {
    local RESULT="${?}"
    trap - EXIT
    if ((RESULT != 0)); then
        "${COMPOSE[@]}" ps --all || true
    fi
    if ! fixture mutate cleanup; then
        RESULT=1
    fi
    if ! "${COMPOSE[@]}" down --volumes --remove-orphans; then
        RESULT=1
    fi
    rm -f -- "${RAICHO_STATE_DIRECTORY}/operation.lock"
    rmdir -- "${RAICHO_STATE_DIRECTORY}" || RESULT=1
    exit "${RESULT}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

operate() {
    bash runtime/credentials/raicho_connector.bash "${1}"
}

database() {
    "${COMPOSE[@]}" run --rm --no-deps -T provisioner connector "${@}"
}

files() {
    "${COMPOSE[@]}" run --rm --no-deps -T credential_files "${1}" /credentials
}

prepare_rotation() {
    "${COMPOSE[@]}" stop raicho thunderbird
    files rotate >/dev/null
    database rotate --token-file /credentials/connector.pending \
        --current-token-file /credentials/connector.token
}

expect_failure() {
    if "${@}"; then
        echo 'FAIL: operation unexpectedly succeeded' >&2
        exit 1
    fi
}

docker compose -f compose/compose.tools.yaml build
"${COMPOSE[@]}" build raicho gateway thunderbird
operate init
fixture database --revision 1
"${COMPOSE[@]}" logs --no-color raicho thunderbird | fixture logs
SERVER="$("${COMPOSE[@]}" ps -q raicho)"
THUNDERBIRD="$("${COMPOSE[@]}" ps -q thunderbird)"
docker inspect "${SERVER}" "${THUNDERBIRD}" | fixture mounts
expect_failure database status
(
    exec {FIXTURE_LOCK}>"${RAICHO_STATE_DIRECTORY}/operation.lock"
    flock --exclusive --nonblock "${FIXTURE_LOCK}"
    expect_failure operate status
)
if [[ $("${COMPOSE[@]}" ps -q raicho) != "${SERVER}" ]]; then
    echo 'FAIL: rejected concurrent operation changed the running server' >&2
    exit 1
fi
operate init
fixture database --revision 1

for MUTATION in hide unsafe_mode unsafe_owner mismatch; do
    fixture mutate "${MUTATION}"
    expect_failure operate verify
    case "${MUTATION}" in
        hide | mismatch) fixture mutate restore ;;
        unsafe_mode) fixture mutate safe_mode ;;
        unsafe_owner) fixture mutate safe_owner ;;
    esac
done
operate verify

prepare_rotation
expect_failure database verify --token-file /credentials/connector.token
database verify --token-file /credentials/connector.pending
fixture database --revision 2 --token connector.pending
operate rotate
fixture database --revision 2

prepare_rotation
fixture mutate mid_publish
operate rotate
fixture database --revision 3
operate rotate
fixture database --revision 4

operate revoke
fixture database --revision 5 --revoked
expect_failure database verify --token-file /credentials/connector.token
expect_failure operate init
"${COMPOSE[@]}" up -d --no-deps --force-recreate --wait --wait-timeout 120 raicho thunderbird
fixture database --revision 5 --revoked
"${COMPOSE[@]}" stop raicho thunderbird
expect_failure database verify --token-file /credentials/connector.token
expect_failure database init --token-file /credentials/connector.token
operate reactivate
fixture database --revision 6
operate reactivate
fixture database --revision 6
"${COMPOSE[@]}" logs --no-color raicho thunderbird | fixture logs

prepare_rotation
operate revoke
fixture database --revision 8 --token connector.pending --revoked
operate reactivate
fixture database --revision 9

prepare_rotation
files publish >/dev/null
operate revoke
fixture database --revision 11 --revoked
operate reactivate
fixture database --revision 12

operate revoke
fixture mutate hide
operate reactivate
fixture database --revision 14
echo 'Credentials passed: provisioning, persistence, rotation recovery, isolation, and revocation'
