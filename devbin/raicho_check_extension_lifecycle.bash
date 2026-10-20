#!/usr/bin/env bash
# Use only fresh, disposable profiles to establish real Thunderbird extension behavior.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIRECTORY}/.." && pwd)"
cd "${REPOSITORY_ROOT}"

PROJECT="raicho-lifecycle-$(date -u +%Y%m%d%H%M%S)-${RANDOM}"
INITIAL_IMAGE="${PROJECT}:initial"
UPGRADE_IMAGE="${PROJECT}:upgrade"
export RAICHO_TEST_TOOLING_IMAGE="${PROJECT}:tools"
export RAICHO_EXTENSION_TEST_IMAGE="${INITIAL_IMAGE}"
COMPOSE=(docker compose -p "${PROJECT}" -f compose/compose.extension_test.yaml)
IDLE_SECONDS="${RAICHO_EXTENSION_IDLE_SECONDS:-90}"
if [[ ! ${IDLE_SECONDS} =~ ^[0-9]{2,4}$ ]] || ((10#${IDLE_SECONDS} < 60 || 10#${IDLE_SECONDS} > 3600)); then
    echo 'FAIL: RAICHO_EXTENSION_IDLE_SECONDS must be between 60 and 3600' >&2
    exit 1
fi
IDLE_SECONDS="$((10#${IDLE_SECONDS}))"

cleanup() {
    local RESULT="${?}"
    trap - EXIT
    if ((RESULT != 0)); then
        "${COMPOSE[@]}" ps --all || true
    fi
    if ! "${COMPOSE[@]}" down --volumes --remove-orphans; then
        RESULT=1
    fi
    docker image rm "${INITIAL_IMAGE}" "${UPGRADE_IMAGE}" \
        "${RAICHO_TEST_TOOLING_IMAGE}" >/dev/null 2>&1 || true
    exit "${RESULT}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

docker build --platform linux/amd64 -f containers/tooling/Dockerfile \
    -t "${RAICHO_TEST_TOOLING_IMAGE}" .

for VERSION in 0.1.0 0.1.1; do
    IMAGE="${INITIAL_IMAGE}"
    if [[ ${VERSION} == 0.1.1 ]]; then
        IMAGE="${UPGRADE_IMAGE}"
    fi
    docker build --platform linux/amd64 -f containers/thunderbird/Dockerfile \
        --build-arg RAICHO_EXTENSION_SOURCE=extension/lifecycle_probe \
        --build-arg "RAICHO_EXTENSION_VERSION=${VERSION}" -t "${IMAGE}" .
done

docker run --rm --read-only --network none --tmpfs /tmp:mode=1777 \
    --cap-drop ALL --security-opt no-new-privileges:true \
    --user 10001:10001 --workdir /opt/raicho/tests/extension_lifecycle \
    --entrypoint python3 "${RAICHO_TEST_TOOLING_IMAGE}" \
    -B -m unittest discover -s . -p '*_tests.py'

"${COMPOSE[@]}" up -d --wait --wait-timeout 120 probe thunderbird
CONTAINER="$("${COMPOSE[@]}" ps -q thunderbird)"
if [[ $(docker inspect --format '{{.HostConfig.ReadonlyRootfs}}' "${CONTAINER}") != true ]]; then
    echo 'FAIL: Thunderbird root filesystem must be read-only' >&2
    exit 1
fi
if [[ $(docker inspect --format '{{len .HostConfig.PortBindings}}' "${CONTAINER}") != 0 ]]; then
    echo 'FAIL: lifecycle fixture must not publish host ports' >&2
    exit 1
fi
"${COMPOSE[@]}" exec -T thunderbird python3 -B /test/runtime_check.py seed
"${COMPOSE[@]}" run --rm check --expected-version 0.1.0 --minimum-heartbeats 2 \
    --save-baseline /config/installed.json
echo "Checking persistent background activity for ${IDLE_SECONDS} seconds"
"${COMPOSE[@]}" run --rm check --expected-version 0.1.0 --minimum-heartbeats 2 \
    --baseline /config/installed.json --same-session --minimum-elapsed "${IDLE_SECONDS}" \
    --timeout "$((IDLE_SECONDS + 120))" --save-baseline /config/idle.json

"${COMPOSE[@]}" restart thunderbird
"${COMPOSE[@]}" run --rm check --expected-version 0.1.0 --minimum-heartbeats 2 \
    --baseline /config/idle.json --save-baseline /config/restarted.json
"${COMPOSE[@]}" exec -T thunderbird python3 -B /test/runtime_check.py persist
export RAICHO_EXTENSION_TEST_IMAGE="${UPGRADE_IMAGE}"
"${COMPOSE[@]}" up -d --no-deps --force-recreate --wait --wait-timeout 120 thunderbird
"${COMPOSE[@]}" run --rm check --expected-version 0.1.1 --minimum-heartbeats 2 \
    --baseline /config/restarted.json
"${COMPOSE[@]}" exec -T thunderbird python3 -B /test/runtime_check.py persist
echo 'Lifecycle passed: unattended install, managed settings, idle, restart, and profile upgrade'
