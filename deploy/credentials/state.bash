# shellcheck shell=bash
# Sourced by the credential wrapper, make deploy-clean, and make mrproper.

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
