#!/usr/bin/env bash
# Prove that loopback administration cannot be reached from the application network.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIRECTORY}/../../.." && pwd)"
cd "${REPOSITORY_ROOT}"

if [[ -z ${COMPOSE_PROJECT_NAME:-} || ${COMPOSE_PROJECT_NAME} == raicho ]]; then
    echo 'FAIL: set COMPOSE_PROJECT_NAME to an explicit disposable project' >&2
    exit 1
fi

BASE_COMPOSE=(docker compose -p "${COMPOSE_PROJECT_NAME}" -f compose.yaml -f automation/acceptance/runtime/compose.test.yaml)
if [[ -n ${RAICHO_CREDENTIAL_DIRECTORY:-} ]]; then
    BASE_COMPOSE+=(-f compose.credentials.yaml)
fi
ADMIN_COMPOSE=("${BASE_COMPOSE[@]}" -f compose.admin.yaml)
PROBE=(docker run --rm --pull never --read-only --cap-drop ALL --security-opt no-new-privileges:true --entrypoint curl)
CURL_OPTIONS=(--noproxy '*' --connect-timeout 3 --max-time 5 --silent --show-error --output /dev/null)
export RAICHO_ADMIN_PORT=0

expect_connection_failure() {
    local ALLOWED_STATUSES="${1}"
    shift
    local RESULT=0 CONNECTIONS
    # The probe is expected to fail, so curl's own error message is noise.
    CONNECTIONS="$("${@}" --write-out '%{num_connects}' 2>/dev/null)" || RESULT="${?}"
    if [[ " ${ALLOWED_STATUSES} " != *" ${RESULT} "* || ${CONNECTIONS} != 0 ]]; then
        echo "FAIL: expected no connection (${ALLOWED_STATUSES}), got status ${RESULT}, connections ${CONNECTIONS}" >&2
        return 1
    fi
}

restore_default() {
    local RESULT="${?}"
    trap - EXIT
    if ! "${BASE_COMPOSE[@]}" up -d --force-recreate --wait --wait-timeout 120 thunderbird; then
        echo 'FAIL: could not restore Thunderbird without administration' >&2
        RESULT=1
    fi
    exit "${RESULT}"
}

RAICHO_CONTAINER="$("${BASE_COMPOSE[@]}" ps -q raicho)"
RAICHO_IMAGE="$(docker inspect --format '{{.Image}}' "${RAICHO_CONTAINER}")"
trap restore_default EXIT
"${ADMIN_COMPOSE[@]}" up -d --force-recreate --wait --wait-timeout 120 thunderbird
THUNDERBIRD_CONTAINER="$("${ADMIN_COMPOSE[@]}" ps -q thunderbird)"
mapfile -t THUNDERBIRD_ADDRESSES < <(docker inspect --format '{{range .NetworkSettings.Networks}}{{println .IPAddress}}{{end}}' "${THUNDERBIRD_CONTAINER}" | sed '/^$/d')
ADMIN_ADDRESS="$("${ADMIN_COMPOSE[@]}" port thunderbird 6080)"
if ((${#THUNDERBIRD_ADDRESSES[@]} != 2)); then
    echo 'FAIL: expected Thunderbird on its egress and connector networks' >&2
    exit 1
fi
for THUNDERBIRD_ADDRESS in "${THUNDERBIRD_ADDRESSES[@]}"; do
    if [[ ! ${THUNDERBIRD_ADDRESS} =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo 'FAIL: expected IPv4 Thunderbird network addresses' >&2
        exit 1
    fi
done
if [[ ! ${ADMIN_ADDRESS} =~ ^127\.0\.0\.1:[0-9]+$ ]]; then
    echo "FAIL: administration must publish on host loopback: ${ADMIN_ADDRESS}" >&2
    exit 1
fi

"${PROBE[@]}" --network host "${RAICHO_IMAGE}" "${CURL_OPTIONS[@]}" --fail \
    --retry 6 --retry-delay 1 --retry-connrefused "http://${ADMIN_ADDRESS}/vnc.html"
for THUNDERBIRD_ADDRESS in "${THUNDERBIRD_ADDRESSES[@]}"; do
    expect_connection_failure '7 28' "${BASE_COMPOSE[@]}" exec -T raicho curl \
        "${CURL_OPTIONS[@]}" "http://${THUNDERBIRD_ADDRESS}:6080/vnc.html"
done
"${PROBE[@]}" --network host "${RAICHO_IMAGE}" "${CURL_OPTIONS[@]}" --fail \
    "http://${ADMIN_ADDRESS}/vnc.html"
echo 'Administration is reachable on host loopback and isolated from Raicho'

"${BASE_COMPOSE[@]}" up -d --force-recreate --wait --wait-timeout 120 thunderbird
trap - EXIT
THUNDERBIRD_CONTAINER="$("${BASE_COMPOSE[@]}" ps -q thunderbird)"
PUBLISHED_ADMIN="$(docker inspect --format '{{if index .NetworkSettings.Ports "6080/tcp"}}published{{end}}' "${THUNDERBIRD_CONTAINER}")"
if [[ -n ${PUBLISHED_ADMIN} ]]; then
    echo 'FAIL: administration port remains published without the override' >&2
    exit 1
fi
expect_connection_failure '7' "${PROBE[@]}" --network "container:${THUNDERBIRD_CONTAINER}" \
    "${RAICHO_IMAGE}" "${CURL_OPTIONS[@]}" http://127.0.0.1:6080/vnc.html
echo 'Administration is unpublished and its listener is closed without the override'
