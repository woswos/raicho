#!/usr/bin/env bash
# Exercise the production connector only with a fresh profile and disposable credentials.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIRECTORY}/../../.." && pwd)"
cd "${REPOSITORY_ROOT}"
export RAICHO_PROJECT
RAICHO_PROJECT="raicho-connector-$(date -u +%Y%m%d%H%M%S)-${RANDOM}"
export RAICHO_STATE_DIRECTORY
RAICHO_STATE_DIRECTORY="$(mktemp -d /tmp/raicho-connector.XXXXXXXX)"
export RAICHO_CREDENTIAL_DIRECTORY="${RAICHO_STATE_DIRECTORY}/credentials"
export RAICHO_COMPOSE_TEST=1
mkdir -m 700 "${RAICHO_CREDENTIAL_DIRECTORY}"
COMPOSE=(docker compose -p "${RAICHO_PROJECT}" -f compose/compose.yaml
    -f compose/compose.credentials.yaml -f compose/compose.runtime_test.yaml)
HOLDER="${RAICHO_PROJECT}-address-holder"
PROBE=(docker run --rm -i --read-only --user 10001:10001 --cap-drop ALL
    --security-opt no-new-privileges:true
    --workdir / --mount "type=bind,source=${REPOSITORY_ROOT}/automation,target=/automation,readonly")

fixture() {
    docker run --rm -i --network none --read-only --user 0:0 \
        --cap-drop ALL --cap-add CHOWN --cap-add DAC_OVERRIDE --cap-add FOWNER \
        --security-opt no-new-privileges:true \
        --mount "type=bind,source=${REPOSITORY_ROOT}/automation/acceptance/credentials/raicho_credential_checks.py,target=/checks.py,readonly" \
        --mount "type=bind,source=${RAICHO_STATE_DIRECTORY},target=/fixture" \
        --mount "type=volume,source=${RAICHO_PROJECT}_raicho-data,target=/database" \
        --entrypoint python3 raicho-tools:local -B /checks.py "${@}"
}

check() {
    "${PROBE[@]}" --network "${RAICHO_PROJECT}_application" --entrypoint python3 \
        raicho-tools:local -B -m automation.acceptance.connector.raicho_connector_checks "${@}"
}

privacy() {
    local NETWORK=none
    if [[ ${1} == diagnostics ]]; then NETWORK="${RAICHO_PROJECT}_application"; fi
    "${PROBE[@]}" --network "${NETWORK}" \
        --mount "type=bind,source=${RAICHO_CREDENTIAL_DIRECTORY}/connector.token,target=/fixture/credentials/connector.token,readonly" \
        --mount "type=volume,source=${RAICHO_PROJECT}_raicho-data,target=/database,readonly" \
        --entrypoint python3 raicho-tools:local -B -m automation.acceptance.connector.raicho_connector_privacy "${1}"
}

prepare_network() {
    local NETWORK="${RAICHO_PROJECT}_application"
    local SUBNET
    local LABELS=(--label "com.docker.compose.project=${RAICHO_PROJECT}"
        --label com.docker.compose.network=application)
    docker network create "${LABELS[@]}" "${NETWORK}" >/dev/null
    SUBNET="$(docker network inspect --format '{{(index .IPAM.Config 0).Subnet}}' "${NETWORK}")"
    docker network rm "${NETWORK}" >/dev/null
    docker network create --subnet "${SUBNET}" "${LABELS[@]}" "${NETWORK}" >/dev/null
}

cleanup() {
    local RESULT="${?}"
    trap - EXIT
    if ((RESULT != 0)); then
        "${COMPOSE[@]}" ps --all || true
        check snapshot || true
    fi
    docker rm -f "${HOLDER}" >/dev/null 2>&1 || true
    if ! fixture mutate cleanup; then RESULT=1; fi
    if ! "${COMPOSE[@]}" down --volumes --remove-orphans; then RESULT=1; fi
    rm -f -- "${RAICHO_STATE_DIRECTORY}/operation.lock"
    rmdir -- "${RAICHO_STATE_DIRECTORY}" || RESULT=1
    exit "${RESULT}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

connected() {
    GENERATION="$(check wait --previous-generation "${GENERATION:-}")"
    echo 'Production connector is authenticated and heartbeating'
}

docker compose -f compose/compose.tools.yaml build
"${COMPOSE[@]}" build raicho thunderbird gateway
prepare_network
bash runtime/credentials/raicho_connector.bash init
connected
SERVER="$("${COMPOSE[@]}" ps -q raicho)"
THUNDERBIRD="$("${COMPOSE[@]}" ps -q thunderbird)"
GATEWAY="$("${COMPOSE[@]}" ps -q gateway)"
docker inspect --format '{{.Name}} {{.Image}}' "${SERVER}" "${THUNDERBIRD}" "${GATEWAY}"
docker inspect "${SERVER}" "${THUNDERBIRD}" "${GATEWAY}" | check deployment
docker inspect "${SERVER}" "${THUNDERBIRD}" | fixture mounts
fixture database --revision 1
"${COMPOSE[@]}" exec -T thunderbird python3 -B - <"${SCRIPT_DIRECTORY}/raicho_inspect_connector_xpi.py"
check idle
check browser
"${PROBE[@]}" --network "${RAICHO_PROJECT}_thunderbird" --entrypoint python3 \
    raicho-tools:local -B -m automation.acceptance.connector.raicho_connector_checks routes
"${PROBE[@]}" --network "${RAICHO_PROJECT}_thunderbird" --entrypoint python3 \
    raicho-tools:local -B -m automation.acceptance.connector.raicho_connector_rejection
SAME_GENERATION="$(check wait --minimum-heartbeats 1)"
if [[ ${SAME_GENERATION} != "${GENERATION}" ]]; then
    echo 'FAIL: invalid authentication displaced the active connector' >&2
    exit 1
fi

for SERVICE in thunderbird gateway raicho; do
    "${COMPOSE[@]}" restart "${SERVICE}"
    connected
    "${COMPOSE[@]}" up -d --no-deps --force-recreate --wait --wait-timeout 120 "${SERVICE}"
    connected
done

THUNDERBIRD="$("${COMPOSE[@]}" ps -q thunderbird)"
docker network disconnect "${RAICHO_PROJECT}_thunderbird" "${THUNDERBIRD}"
check wait --status disconnected --timeout 75
docker network connect --alias thunderbird "${RAICHO_PROJECT}_thunderbird" "${THUNDERBIRD}"
connected

SERVER="$("${COMPOSE[@]}" ps -q raicho)"
GATEWAY="$("${COMPOSE[@]}" ps -q gateway)"
OLD_ADDRESS="$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "${SERVER}")"
"${COMPOSE[@]}" stop raicho
"${COMPOSE[@]}" rm -f raicho
docker run -d --name "${HOLDER}" --network "${RAICHO_PROJECT}_application" \
    --ip "${OLD_ADDRESS}" --read-only --user 10001:10001 --cap-drop ALL \
    --security-opt no-new-privileges:true --entrypoint sleep raicho-tools:local 600 >/dev/null
"${COMPOSE[@]}" up -d --no-deps --wait --wait-timeout 120 raicho
SERVER="$("${COMPOSE[@]}" ps -q raicho)"
NEW_ADDRESS="$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "${SERVER}")"
if [[ ${NEW_ADDRESS} == "${OLD_ADDRESS}" || $("${COMPOSE[@]}" ps -q gateway) != "${GATEWAY}" ]]; then
    echo 'FAIL: DNS recovery requires a changed Raicho address and unchanged gateway' >&2
    exit 1
fi
connected
docker rm -f "${HOLDER}" >/dev/null
echo 'Gateway dynamically resolved a recreated Raicho container at a different address'

COMPOSE_PROJECT_NAME="${RAICHO_PROJECT}" bash automation/acceptance/runtime/raicho_check_admin_isolation.bash
connected
"${COMPOSE[@]}" logs --no-color raicho thunderbird gateway | fixture logs
fixture database --revision 1
"${COMPOSE[@]}" logs --no-color raicho thunderbird gateway | privacy logs
privacy diagnostics
privacy database
echo 'Connector passed: ten-minute idle, authentication, recovery, DNS refresh, isolation, and privacy'
