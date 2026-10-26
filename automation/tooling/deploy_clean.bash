#!/usr/bin/env bash
# Permanently remove one deployment: its containers, networks, volumes, and state directory.
set -euo pipefail

# shellcheck source=automation/tooling/clean.bash
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/clean.bash"

PROJECT="${RAICHO_PROJECT:-${COMPOSE_PROJECT_NAME:-raicho}}"
STATE_DIRECTORY="${RAICHO_STATE_DIRECTORY:-${REPOSITORY_ROOT}/.raicho/${PROJECT}}"
if [[ ! ${PROJECT} =~ ^[a-z0-9][a-z0-9_-]*$ || ${STATE_DIRECTORY} != /* || -L ${STATE_DIRECTORY} ]]; then
    echo "FAIL: invalid project ${PROJECT} or state directory ${STATE_DIRECTORY}" >&2
    exit 1
fi

FILTER="label=${PROJECT_LABEL}=${PROJECT}"
mapfile -t CONTAINERS < <(list container --format '{{.Names}}' --filter "${FILTER}")
mapfile -t VOLUMES < <(list volume --format '{{.Name}}' --filter "${FILTER}")
mapfile -t NETWORKS < <(list network --format '{{.Name}}' --filter "${FILTER}")
if ((${#CONTAINERS[@]} + ${#VOLUMES[@]} + ${#NETWORKS[@]} == 0)) && [[ ! -e ${STATE_DIRECTORY} ]]; then
    echo "Deployment ${PROJECT} has nothing to remove"
    exit 0
fi

echo "This permanently deletes deployment ${PROJECT}:"
for CONTAINER in "${CONTAINERS[@]}"; do
    echo "  container ${CONTAINER}"
done
for VOLUME in "${VOLUMES[@]}"; do
    echo "  volume ${VOLUME}"
done
if [[ -e ${STATE_DIRECTORY} ]]; then
    echo "  state directory ${STATE_DIRECTORY}, including the connector token"
fi
ANSWER=''
read -r -p "Type ${PROJECT} to confirm: " ANSWER || true
if [[ ${ANSWER} != "${PROJECT}" ]]; then
    echo 'Cancelled. Nothing was removed.' >&2
    exit 1
fi

LOCK_PATH="${STATE_DIRECTORY}/operation.lock"
if [[ -f ${LOCK_PATH} && ! -L ${LOCK_PATH} ]]; then
    exec {LOCK_DESCRIPTOR}>>"${LOCK_PATH}"
    if ! flock --exclusive --nonblock "${LOCK_DESCRIPTOR}"; then
        echo 'FAIL: a credential operation is running' >&2
        exit 1
    fi
fi
docker compose -p "${PROJECT}" -f "${REPOSITORY_ROOT}/compose.yaml" down --volumes --remove-orphans
mapfile -t VOLUMES < <(list volume --quiet --filter "${FILTER}")
if ((${#VOLUMES[@]} > 0)); then
    docker volume rm "${VOLUMES[@]}" >/dev/null
fi
if [[ -e ${STATE_DIRECTORY} ]] && ! remove_directory "${STATE_DIRECTORY}"; then
    echo "FAIL: kept ${STATE_DIRECTORY}; remove it as the user that owns its files" >&2
    exit 1
fi
echo "Removed deployment ${PROJECT}, its volumes, and its state directory"
