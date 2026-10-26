#!/usr/bin/env bash
# Verify unattended startup, persistence, and isolation in a disposable runtime deployment.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIRECTORY}/../../.." && pwd)"
cd "${REPOSITORY_ROOT}"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-raicho-runtime-$(date -u +%Y%m%d%H%M%S)-${RANDOM}}"
export COMPOSE_FILE=compose.yaml:automation/acceptance/runtime/compose.test.yaml
if [[ ${COMPOSE_PROJECT_NAME} == raicho ]]; then
    echo 'FAIL: the runtime check removes its project; choose a disposable COMPOSE_PROJECT_NAME' >&2
    exit 1
fi

cleanup() {
    local RESULT="${?}"
    trap - EXIT
    if ((RESULT != 0)); then
        docker compose logs --no-color || true
    fi
    if ! docker compose down --volumes --remove-orphans; then
        RESULT=1
    fi
    exit "${RESULT}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

docker compose --profile test build
docker compose up -d --wait --wait-timeout 120 raicho thunderbird
docker compose run --rm smoke http
docker compose stop raicho thunderbird
docker compose run --rm smoke seed
docker compose up -d --force-recreate --wait --wait-timeout 120 raicho thunderbird
docker compose run --rm smoke http
docker compose run --rm smoke persistence
bash automation/acceptance/runtime/check_admin_isolation.bash
docker compose stop thunderbird
docker compose run --rm smoke http
echo 'Runtime passed: startup, persistence across recreation, administrative isolation, and independent readiness.'
