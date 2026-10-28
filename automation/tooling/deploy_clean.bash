#!/usr/bin/env bash
# Permanently remove one deployment: its containers, networks, volumes, and state directory. Then clean.
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
# Every state directory belongs to its caller, so the scan skips only what the caller neither owns
# nor can read, such as the UID-10001 token directory, and fails on anything else it cannot read.
NESTED_LOCK=''
if [[ -e ${STATE_DIRECTORY} ]]; then
    NESTED_LOCK="$(find "${STATE_DIRECTORY}" -mindepth 1 \( ! -user "$(id -u)" ! -readable -prune \) \
        -o \( -name operation.lock ! -path "${LOCK_PATH}" -print -quit \))" \
        || fail "could not inspect ${STATE_DIRECTORY} for another deployment's state"
fi
if [[ -n ${NESTED_LOCK} ]]; then
    fail "${STATE_DIRECTORY} holds another deployment's state in ${NESTED_LOCK%/operation.lock}"
fi

# A subshell keeps the glob options local.
remove_state_contents() (
    shopt -s nullglob dotglob
    for ENTRY in "${STATE_DIRECTORY}"/*; do
        if [[ ${ENTRY} == "${LOCK_PATH}" ]]; then
            continue
        fi
        if [[ -d ${ENTRY} && ! -L ${ENTRY} ]]; then
            remove_directory "${ENTRY}" || exit 1
        else
            rm -f -- "${ENTRY}" || exit 1
        fi
    done
)

listing() {
    list "${1}" --format "${2}" --filter "label=${PROJECT_LABEL}=${PROJECT}" \
        || fail "could not list the deployment's ${1}s"
}

# Command substitution keeps a failed listing from reading as an empty deployment.
CONTAINER_NAMES="$(listing container '{{.Names}}')"
NETWORK_NAMES="$(listing network '{{.Name}}')"
VOLUME_NAMES="$(listing volume '{{.Name}}')"
mapfile -t CONTAINERS < <(printf '%s' "${CONTAINER_NAMES}")
mapfile -t NETWORKS < <(printf '%s' "${NETWORK_NAMES}")
mapfile -t VOLUMES < <(printf '%s' "${VOLUME_NAMES}")
if ((${#CONTAINERS[@]} + ${#NETWORKS[@]} + ${#VOLUMES[@]} == 0)) && [[ ! -e ${STATE_DIRECTORY} ]]; then
    echo "Deployment ${PROJECT} has nothing to remove"
    clean
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

# A missing state directory is created only to hold the lock, so a credential command
# cannot start on the deployment while it is removed.
umask 077
mkdir -p -- "${STATE_DIRECTORY}"
exec {LOCK_DESCRIPTOR}>>"${LOCK_PATH}"
if ! flock --exclusive --nonblock "${LOCK_DESCRIPTOR}"; then
    fail 'a credential operation is running'
fi
docker compose -p "${PROJECT}" -f "${REPOSITORY_ROOT}/compose.yaml" down --remove-orphans
# Removing the token before the volumes keeps them paired if this step fails. The lock
# stays until the volumes are gone, so a credential command cannot start on them meanwhile.
if [[ -e ${STATE_DIRECTORY} ]] && ! remove_state_contents; then
    fail "kept ${STATE_DIRECTORY} and the volumes; fix its file ownership and run make deploy-clean again"
fi
if ! remove_project "${PROJECT}"; then
    fail "could not remove every resource of ${PROJECT}; run make deploy-clean again"
fi
# Only the lock remains, so non-recursive removal cannot reach anything created meanwhile.
if ! { rm -f -- "${LOCK_PATH}" && rmdir -- "${STATE_DIRECTORY}"; }; then
    fail "removed the volumes but kept ${STATE_DIRECTORY}; remove it and run make deploy-clean again"
fi
echo "Removed deployment ${PROJECT}, its volumes, and its state directory"
clean
