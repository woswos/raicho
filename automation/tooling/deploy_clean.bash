#!/usr/bin/env bash
# Permanently remove one deployment: its containers, networks, volumes, and state directory. Then clean.
set -euo pipefail

# shellcheck source=automation/tooling/clean.bash
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/clean.bash"
# shellcheck source=deploy/credentials/state_lock.bash
source "${REPOSITORY_ROOT}/deploy/credentials/state_lock.bash"

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
PROJECT_MARKER="${STATE_DIRECTORY}/project"
if [[ -L ${LOCK_PATH} ]] || { [[ -e ${LOCK_PATH} ]] && [[ ! -f ${LOCK_PATH} ]]; }; then
    fail "${LOCK_PATH} must be a regular file"
fi
# The shared lock covers the scan and this deployment's own lock, so a credential command cannot
# claim state inside it until the removal ends. A missing state directory only holds the lock.
umask 077
lock_state_layout
# A credential command creates and marks state under the same lock, so check both only now.
STATE_EXISTED=false
if [[ -e ${STATE_DIRECTORY} ]]; then
    STATE_EXISTED=true
    # The credential wrapper writes this marker, so an override cannot point at unrelated files.
    if [[ -L ${PROJECT_MARKER} || ! -f ${PROJECT_MARKER} || $(<"${PROJECT_MARKER}") != "${PROJECT}" ]]; then
        fail "${STATE_DIRECTORY} is not marked as the state of ${PROJECT}; run make deploy-connector-status first"
    fi
fi
# A failed removal leaves the lock and this marker, so running deploy-clean again accepts them.
if [[ ${STATE_EXISTED} == false ]]; then
    mkdir -p -- "${STATE_DIRECTORY}"
    # A default ACL overrides the umask, so set the modes explicitly.
    chmod 700 -- "${STATE_DIRECTORY}"
    printf '%s\n' "${PROJECT}" >"${PROJECT_MARKER}"
fi
exec {LOCK_DESCRIPTOR}>>"${LOCK_PATH}"
chmod 600 -- "${LOCK_PATH}"
if ! flock --exclusive --nonblock "${LOCK_DESCRIPTOR}"; then
    fail 'a credential operation is running'
fi
# Every state directory belongs to its caller, so the scan skips only what the caller neither owns
# nor can read, such as the UID-10001 token directory, and fails on anything else it cannot read.
NESTED_LOCK="$(find "${STATE_DIRECTORY}" -mindepth 1 \( ! -user "$(id -u)" ! -readable -prune \) \
    -o \( -name operation.lock ! -path "${LOCK_PATH}" -print -quit \))" \
    || fail "could not inspect ${STATE_DIRECTORY} for another deployment's state"
if [[ -n ${NESTED_LOCK} ]]; then
    fail "${STATE_DIRECTORY} holds another deployment's state in ${NESTED_LOCK%/operation.lock}"
fi
unlock_state_layout

# Removing a lock file under the shared lock keeps a credential command from creating a new one
# at the same path while it disappears.
forget_created_state() {
    if [[ ${STATE_EXISTED} == false ]]; then
        lock_state_layout
        rm -f -- "${LOCK_PATH}" "${PROJECT_MARKER}"
        rmdir -- "${STATE_DIRECTORY}"
        unlock_state_layout
    fi
}

# A subshell keeps the glob options local.
remove_state_contents() (
    shopt -s nullglob dotglob
    for ENTRY in "${STATE_DIRECTORY}"/*; do
        if [[ ${ENTRY} == "${LOCK_PATH}" || ${ENTRY} == "${PROJECT_MARKER}" ]]; then
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
if ((${#CONTAINERS[@]} + ${#NETWORKS[@]} + ${#VOLUMES[@]} == 0)) && [[ ${STATE_EXISTED} == false ]]; then
    forget_created_state
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
if [[ ${STATE_EXISTED} == true ]]; then
    echo "  state directory ${STATE_DIRECTORY}, including the connector token"
fi
ANSWER=''
read -r -p "Type ${PROJECT} to confirm: " ANSWER || true
if [[ ${ANSWER} != "${PROJECT}" ]]; then
    forget_created_state
    echo 'Cancelled. Nothing was removed.' >&2
    exit 1
fi

docker compose -p "${PROJECT}" -f "${REPOSITORY_ROOT}/compose.yaml" down --remove-orphans
# Removing the token before the volumes keeps them paired if this step fails. The lock
# stays until the volumes are gone, so a credential command cannot start on them meanwhile.
if ! remove_state_contents; then
    fail "kept ${STATE_DIRECTORY} and the volumes; fix its file ownership and run make deploy-clean again"
fi
if ! remove_project "${PROJECT}"; then
    fail "could not remove every resource of ${PROJECT}; run make deploy-clean again"
fi
# Only the lock and marker remain, so non-recursive removal cannot reach anything created meanwhile.
lock_state_layout
if ! { rm -f -- "${LOCK_PATH}" "${PROJECT_MARKER}" && rmdir -- "${STATE_DIRECTORY}"; }; then
    fail "removed the volumes but kept ${STATE_DIRECTORY}; remove it and run make deploy-clean again"
fi
unlock_state_layout
echo "Removed deployment ${PROJECT}, its volumes, and its state directory"
clean
