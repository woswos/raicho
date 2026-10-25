#!/usr/bin/env bash
# Exercise the production connector only with a fresh profile and disposable credentials.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIRECTORY}/../../.." && pwd)"
cd "${REPOSITORY_ROOT}"
# shellcheck source=automation/acceptance/raicho_credential_deployment.bash
source automation/acceptance/raicho_credential_deployment.bash
prepare_credential_deployment connector
HOLDER="${RAICHO_PROJECT}-address-holder"
PROBE=(docker run --rm -i --read-only --user 10001:10001 --cap-drop ALL
    --security-opt no-new-privileges:true
    --workdir / --mount "type=bind,source=${REPOSITORY_ROOT}/automation,target=/automation,readonly"
    --mount "type=bind,source=${REPOSITORY_ROOT}/protocol,target=/protocol,readonly")

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
    local NETWORK="${RAICHO_PROJECT}_connector-application"
    local SUBNET
    local OPTIONS=(--internal --label "com.docker.compose.project=${RAICHO_PROJECT}"
        --label com.docker.compose.network=connector-application)
    docker network create "${OPTIONS[@]}" "${NETWORK}" >/dev/null
    SUBNET="$(docker network inspect --format '{{(index .IPAM.Config 0).Subnet}}' "${NETWORK}")"
    docker network rm "${NETWORK}" >/dev/null
    docker network create --subnet "${SUBNET}" "${OPTIONS[@]}" "${NETWORK}" >/dev/null
}

address() {
    docker inspect --format "{{(index .NetworkSettings.Networks \"${RAICHO_PROJECT}_${2}\").IPAddress}}" "${1}"
}

cleanup() {
    local RESULT="${?}"
    trap - EXIT
    if ((RESULT != 0)); then
        "${COMPOSE[@]}" ps --all || true
        check snapshot || true
    fi
    docker rm -f "${HOLDER}" >/dev/null 2>&1 || true
    remove_credential_deployment || RESULT=1
    exit "${RESULT}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

connected() {
    GENERATION="$(check wait --previous-generation "${GENERATION:-}")"
    echo 'Production connector is authenticated and heartbeating'
}

thunderbird_check() {
    "${COMPOSE[@]}" exec -T thunderbird python3 -B - "${@}" \
        <"${REPOSITORY_ROOT}/automation/acceptance/connector/raicho_thunderbird_checks.py"
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
for NETWORK in connector-application connector-thunderbird; do
    if [[ $(docker network inspect --format '{{.Internal}}' "${RAICHO_PROJECT}_${NETWORK}") != true ]]; then
        echo "FAIL: ${NETWORK} must deny external routing and DNS forwarding" >&2
        exit 1
    fi
done
docker inspect "${SERVER}" "${THUNDERBIRD}" | fixture mounts
fixture database --revision 1
"${COMPOSE[@]}" exec -T thunderbird python3 -B - <"${REPOSITORY_ROOT}/extension/tests/raicho_inspect_connector_xpi.py"
thunderbird_check seed
check idle
check browser
"${PROBE[@]}" --network "${RAICHO_PROJECT}_connector-thunderbird" --entrypoint python3 \
    raicho-tools:local -B -m automation.acceptance.connector.raicho_connector_checks routes
"${PROBE[@]}" --network "${RAICHO_PROJECT}_connector-thunderbird" --entrypoint python3 \
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
thunderbird_check persist

THUNDERBIRD="$("${COMPOSE[@]}" ps -q thunderbird)"
docker network disconnect "${RAICHO_PROJECT}_connector-thunderbird" "${THUNDERBIRD}"
check wait --status disconnected --timeout 75
docker network connect --alias thunderbird "${RAICHO_PROJECT}_connector-thunderbird" "${THUNDERBIRD}"
connected

SERVER="$("${COMPOSE[@]}" ps -q raicho)"
GATEWAY="$("${COMPOSE[@]}" ps -q gateway)"
OLD_ADDRESS="$(address "${SERVER}" connector-application)"
"${COMPOSE[@]}" stop raicho
"${COMPOSE[@]}" rm -f raicho
docker run -d --name "${HOLDER}" --network "${RAICHO_PROJECT}_connector-application" \
    --ip "${OLD_ADDRESS}" --read-only --user 10001:10001 --cap-drop ALL \
    --security-opt no-new-privileges:true --entrypoint sleep raicho-tools:local 600 >/dev/null
"${COMPOSE[@]}" up -d --no-deps --wait --wait-timeout 120 raicho
SERVER="$("${COMPOSE[@]}" ps -q raicho)"
NEW_ADDRESS="$(address "${SERVER}" connector-application)"
if [[ ${NEW_ADDRESS} == "${OLD_ADDRESS}" || $("${COMPOSE[@]}" ps -q gateway) != "${GATEWAY}" ]]; then
    echo 'FAIL: DNS recovery requires a changed Raicho address and unchanged gateway' >&2
    exit 1
fi
connected
docker rm -f "${HOLDER}" >/dev/null
echo 'Gateway dynamically resolved a recreated Raicho container at a different address'

COMPOSE_PROJECT_NAME="${RAICHO_PROJECT}" bash automation/acceptance/runtime/raicho_check_admin_isolation.bash
connected

COMPOSE+=(-f compose/compose.connector_upgrade.yaml)
"${COMPOSE[@]}" run --rm upgrade-extension
"${COMPOSE[@]}" up -d --no-deps --force-recreate --wait --wait-timeout 120 thunderbird
connected
thunderbird_check persist 65535.0.0
echo 'Thunderbird upgraded the managed connector in the same profile'
fixture database --revision 1
"${COMPOSE[@]}" logs --no-color raicho thunderbird gateway | privacy logs
privacy diagnostics
privacy database
echo 'Connector passed: ten-minute idle, authentication, recovery, DNS refresh, isolation, upgrade, and privacy'
