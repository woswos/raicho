#!/usr/bin/env bash
# Test fictional mail only in a fresh profile on an isolated Docker network.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIRECTORY}/../../.." && pwd)"
cd "${REPOSITORY_ROOT}"

NATIVE=false
if [[ ${#} == 1 && ${1} == --native ]]; then
    NATIVE=true
elif [[ ${#} != 0 ]]; then
    echo 'Usage: check_mail_compatibility.bash [--native]' >&2
    exit 2
fi

PROJECT="raicho-mail-$(date -u +%Y%m%d%H%M%S)-${RANDOM}"
export RAICHO_TEST_TOOLING_IMAGE="${PROJECT}:tools"
export RAICHO_MAIL_TEST_IMAGE="${PROJECT}:thunderbird"
COMPOSE=(docker compose -p "${PROJECT}" -f compose/compose.mailprobe_test.yaml)
if [[ ${NATIVE} == true ]]; then
    COMPOSE+=(-f compose/compose.mailprobe_admin.yaml)
fi

cleanup() {
    local RESULT="${?}"
    trap - EXIT
    if ((RESULT != 0)); then
        "${COMPOSE[@]}" ps --all || true
    fi
    if ! "${COMPOSE[@]}" down --volumes --remove-orphans; then
        RESULT=1
    fi
    docker image rm "${RAICHO_MAIL_TEST_IMAGE}" "${RAICHO_TEST_TOOLING_IMAGE}" \
        >/dev/null 2>&1 || true
    exit "${RESULT}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

docker build --platform linux/amd64 -f containers/tooling/Dockerfile \
    -t "${RAICHO_TEST_TOOLING_IMAGE}" .
docker build --platform linux/amd64 -f containers/thunderbird/Dockerfile \
    -t "${RAICHO_MAIL_TEST_IMAGE}" .

for SUITE in proxy profile probe; do
    docker run --rm --read-only --network none --tmpfs /tmp:mode=1777 \
        --cap-drop ALL --security-opt no-new-privileges:true \
        --user 10001:10001 \
        --env PYTHONPATH=/opt/raicho/extension/mailprobe/tests/proxy:/opt/raicho/extension/mailprobe/tests/profile:/opt/raicho/extension/mailprobe/tests/probe \
        --entrypoint python3 "${RAICHO_TEST_TOOLING_IMAGE}" \
        -B -m unittest discover -s "/opt/raicho/extension/mailprobe/tests/${SUITE}" -p '*_tests.py'
done

"${COMPOSE[@]}" run --rm extension
"${COMPOSE[@]}" up -d --wait --wait-timeout 120 greenmail probe mail-proxy
"${COMPOSE[@]}" run --rm driver prepare
"${COMPOSE[@]}" up -d --wait --wait-timeout 120 thunderbird

if [[ $(docker network inspect --format '{{.Internal}}' "${PROJECT}_mail-test") != true ]]; then
    echo 'FAIL: Mail fixture network must deny external routing' >&2
    exit 1
fi
for SERVICE in greenmail probe mail-proxy thunderbird; do
    CONTAINER="$("${COMPOSE[@]}" ps -q "${SERVICE}")"
    NETWORK_NAME="$(docker inspect --format '{{range $NAME, $NETWORK := .NetworkSettings.Networks}}{{$NAME}}{{end}}' "${CONTAINER}")"
    if [[ ${NETWORK_NAME} != "${PROJECT}_mail-test" ]]; then
        echo "FAIL: ${SERVICE} must use only the isolated fixture network" >&2
        exit 1
    fi
    if [[ $(docker inspect --format '{{len .HostConfig.PortBindings}}' "${CONTAINER}") != 0 ]]; then
        echo "FAIL: ${SERVICE} must not publish host ports" >&2
        exit 1
    fi
done

"${COMPOSE[@]}" run --rm driver inventory
"${COMPOSE[@]}" run --rm driver drafts
if [[ ${NATIVE} == true ]]; then
    "${COMPOSE[@]}" run --rm driver command --action open_permission_page
    CONTAINER="$("${COMPOSE[@]}" ps -q thunderbird)"
    ADMIN_ADDRESS="$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "${CONTAINER}")"
    printf 'On the Linux Docker host, open http://%s:6080/vnc.html?autoconnect=true&resize=scale\n' "${ADMIN_ADDRESS}"
    echo 'In Thunderbird, request the probe send permission and click Allow.'
    echo 'Press Enter after Thunderbird grants the messages.send permission.'
    read -r
    "${COMPOSE[@]}" run --rm driver permission_verify
    "${COMPOSE[@]}" run --rm driver delivery
fi
"${COMPOSE[@]}" restart thunderbird
if [[ ${NATIVE} == true ]]; then
    echo 'After Thunderbird restarts, choose Later if it asks to send unsent messages.'
    echo 'Keep the queued fixture message in Outbox. Press Enter when the mail window is ready.'
    read -r
fi
"${COMPOSE[@]}" run --rm driver restart

if [[ ${NATIVE} == true ]]; then
    "${COMPOSE[@]}" run --rm driver native_prepare
    CONTAINER="$("${COMPOSE[@]}" ps -q thunderbird)"
    ADMIN_ADDRESS="$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "${CONTAINER}")"
    printf 'On the Linux Docker host, open http://%s:6080/vnc.html?autoconnect=true&resize=scale\n' "${ADMIN_ADDRESS}"
    echo 'Open the selected draft in Thunderbird, verify the alias and attachment,'
    echo 'then follow the native_prepare instructions to edit and save it.'
    echo 'Press Ctrl+S and leave the compose window open. Press Enter here to verify it.'
    read -r
    "${COMPOSE[@]}" run --rm driver native_verify
    echo 'Fault injection may display native errors. Dismiss errors with OK, never Retry or Send Now.'
    "${COMPOSE[@]}" run --rm driver faults
    "${COMPOSE[@]}" run --rm driver settlement
else
    "${COMPOSE[@]}" run --rm driver record_skips
    echo 'Draft-only unattended run. Delivery, native editing, and faults were not run.'
fi

"${COMPOSE[@]}" run --rm driver evidence
"${COMPOSE[@]}" exec -T mail-proxy python3 -B -m unittest mail_fixture_integration
echo 'Mail compatibility evidence collected. Removing the disposable deployment.'
