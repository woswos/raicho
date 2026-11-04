# shellcheck shell=bash
# Sourced by the credential and login wrappers, make deploy-clean, and make mrproper.

PROJECT_NAME='^[a-z0-9][a-z0-9_-]*$'

fail() {
    echo "FAIL: ${1}" >&2
    exit 1
}

# Make selects the deployment from the same variables.
select_deployment() {
    PROJECT="${RAICHO_PROJECT:-${COMPOSE_PROJECT_NAME:-raicho}}"
    STATE_DIRECTORY="${RAICHO_STATE_DIRECTORY:-${REPOSITORY_ROOT}/.raicho/${PROJECT}}"
    if [[ ! ${PROJECT} =~ ${PROJECT_NAME} || ${PROJECT} == raicho-tools || ${STATE_DIRECTORY} != /* ]]; then
        fail "invalid project ${PROJECT} or state directory ${STATE_DIRECTORY}"
    fi
}

require_private_directory() {
    if [[ -L ${1} ]] || { [[ -e ${1} ]] \
        && { [[ ! -d ${1} ]] || [[ $(stat -c '%u:%a' -- "${1}") != "$(id -u):700" ]]; }; }; then
        fail "${1} must be a private directory owned by the caller"
    fi
}

require_private_file() {
    if [[ -L ${1} ]] || { [[ -e ${1} ]] \
        && { [[ ! -f ${1} ]] || [[ $(stat -c '%u:%a' -- "${1}") != "$(id -u):600" ]]; }; }; then
        fail "${1} must be a private regular file owned by the caller"
    fi
}

# One lock per host user covers every checkout and state directory, so a command cannot check
# for overlapping deployments while another one is still claiming its state directory.
lock_state_layout() {
    local LAYOUT_DIRECTORY="${TMPDIR:-/tmp}/raicho-state-$(id -u)"
    mkdir -p -- "${LAYOUT_DIRECTORY}"
    if [[ -L ${LAYOUT_DIRECTORY} || $(stat -c '%u' -- "${LAYOUT_DIRECTORY}") != "$(id -u)" ]]; then
        fail "${LAYOUT_DIRECTORY} must be a directory owned by the caller"
    fi
    # A default ACL overrides the umask, so set the mode explicitly.
    chmod 700 -- "${LAYOUT_DIRECTORY}"
    exec {LAYOUT_DESCRIPTOR}>>"${LAYOUT_DIRECTORY}/layout.lock"
    if ! flock --exclusive --nonblock "${LAYOUT_DESCRIPTOR}"; then
        fail 'another credential or deploy-clean command is checking state directories; try again'
    fi
}

unlock_state_layout() {
    exec {LAYOUT_DESCRIPTOR}>&-
}

# Creates or checks the deployment's private state directory and holds its operation lock
# until the caller exits, so credential and login operations never overlap.
claim_state_directory() {
    require_private_directory "${STATE_DIRECTORY}"
    umask 077
    lock_state_layout
    # make deploy-clean deletes everything inside a deployment's state directory, so state cannot nest.
    # The walk follows the physical path, so a symlinked parent cannot hide another deployment.
    PARENT="$(dirname -- "$(realpath -m -- "${STATE_DIRECTORY}")")"
    while [[ ${PARENT} != / ]]; do
        if [[ -e ${PARENT}/operation.lock ]]; then
            fail "${STATE_DIRECTORY} is inside another deployment's state directory ${PARENT}"
        fi
        PARENT="$(dirname -- "${PARENT}")"
    done
    if [[ ! -e ${STATE_DIRECTORY} ]]; then
        mkdir -p -- "${STATE_DIRECTORY}"
        # A default ACL overrides the umask, so set the mode explicitly.
        chmod 700 -- "${STATE_DIRECTORY}"
    fi
    LOCK_PATH="${STATE_DIRECTORY}/operation.lock"
    require_private_file "${LOCK_PATH}"
    exec {LOCK_DESCRIPTOR}>>"${LOCK_PATH}"
    # A default ACL overrides the umask, so set the lock mode explicitly.
    chmod 600 -- "${LOCK_PATH}"
    if ! flock --exclusive --nonblock "${LOCK_DESCRIPTOR}"; then
        fail 'another credential operation is running'
    fi
    # make deploy-clean deletes a state directory only when this marker names its project.
    PROJECT_MARKER="${STATE_DIRECTORY}/project"
    if [[ -L ${PROJECT_MARKER} ]] || { [[ -e ${PROJECT_MARKER} ]] && [[ ! -f ${PROJECT_MARKER} ]]; }; then
        fail 'the project marker must be a regular file'
    fi
    if [[ ! -e ${PROJECT_MARKER} ]]; then
        printf '%s\n' "${PROJECT}" >"${PROJECT_MARKER}"
    elif [[ $(<"${PROJECT_MARKER}") != "${PROJECT}" ]]; then
        fail "${STATE_DIRECTORY} belongs to project $(<"${PROJECT_MARKER}"), not ${PROJECT}"
    fi
    unlock_state_layout
    STATE_DIRECTORY="$(cd "${STATE_DIRECTORY}" && pwd -P)"
}
