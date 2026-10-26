#!/usr/bin/env bash
# Permanently remove one deployment: its containers, networks, volumes, and state directory.
set -euo pipefail

# shellcheck source=automation/tooling/clean.bash
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/clean.bash"

fail() {
    echo "FAIL: ${1}" >&2
    exit 1
}

PROJECT="${RAICHO_PROJECT:-${COMPOSE_PROJECT_NAME:-raicho}}"
STATE_DIRECTORY="${RAICHO_STATE_DIRECTORY:-${REPOSITORY_ROOT}/.raicho/${PROJECT}}"
if [[ ! ${PROJECT} =~ ^[a-z0-9][a-z0-9_-]*$ || ${PROJECT} == raicho-tools || ${STATE_DIRECTORY} != /* ]]; then
    fail "invalid project ${PROJECT} or state directory ${STATE_DIRECTORY}"
fi
# The fallback removal runs as root, so it must never reach a directory the caller does not own.
if [[ -L ${STATE_DIRECTORY} ]] || { [[ -e ${STATE_DIRECTORY} ]] \
    && { [[ ! -d ${STATE_DIRECTORY} ]] || [[ $(stat -c '%u:%a' -- "${STATE_DIRECTORY}") != "$(id -u):700" ]]; }; }; then
    fail "${STATE_DIRECTORY} must be a private directory owned by the caller"
fi
LOCK_PATH="${STATE_DIRECTORY}/operation.lock"
if [[ -L ${LOCK_PATH} ]] || { [[ -e ${LOCK_PATH} ]] && [[ ! -f ${LOCK_PATH} ]]; }; then
    fail "${LOCK_PATH} must be a regular file"
fi

FILTER="label=${PROJECT_LABEL}=${PROJECT}"
mapfile -t CONTAINERS < <(list container --format '{{.Names}}' --filter "${FILTER}")
mapfile -t NETWORKS < <(list network --format '{{.Name}}' --filter "${FILTER}")
mapfile -t VOLUMES < <(list volume --format '{{.Name}}' --filter "${FILTER}")
if ((${#CONTAINERS[@]} + ${#NETWORKS[@]} + ${#VOLUMES[@]} == 0)) && [[ ! -e ${STATE_DIRECTORY} ]]; then
    echo "Deployment ${PROJECT} has nothing to remove"
    exit 0
fi

echo "This permanently deletes deployment ${PROJECT}:"
for CONTAINER in "${CONTAINERS[@]}"; do
    echo "  container ${CONTAINER}"
done
for NETWORK in "${NETWORKS[@]}"; do
    echo "  network ${NETWORK}"
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

if [[ -d ${STATE_DIRECTORY} ]]; then
    umask 077
    exec {LOCK_DESCRIPTOR}>>"${LOCK_PATH}"
    if ! flock --exclusive --nonblock "${LOCK_DESCRIPTOR}"; then
        fail 'a credential operation is running'
    fi
fi
docker compose -p "${PROJECT}" -f "${REPOSITORY_ROOT}/compose.yaml" down --remove-orphans
# Removing the token before the volumes keeps them paired if this step fails.
if [[ -e ${STATE_DIRECTORY} ]] && ! remove_directory "${STATE_DIRECTORY}"; then
    fail "kept ${STATE_DIRECTORY} and the volumes; fix its file ownership and run make deploy-clean again"
fi
remove_project "${PROJECT}"
echo "Removed deployment ${PROJECT}, its volumes, and its state directory"
