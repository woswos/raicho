# shellcheck shell=bash
# Sourced by the credential wrapper and make deploy-clean.

# One lock per host user covers every checkout and state directory, so a command cannot check
# for overlapping deployments while another one is still claiming its state directory.
lock_state_layout() {
    local LAYOUT_DIRECTORY="${TMPDIR:-/tmp}/raicho-state-$(id -u)"
    mkdir -p -- "${LAYOUT_DIRECTORY}"
    if [[ -L ${LAYOUT_DIRECTORY} || $(stat -c '%u' -- "${LAYOUT_DIRECTORY}") != "$(id -u)" ]]; then
        echo "FAIL: ${LAYOUT_DIRECTORY} must be a directory owned by the caller" >&2
        exit 1
    fi
    # A default ACL overrides the umask, so set the mode explicitly.
    chmod 700 -- "${LAYOUT_DIRECTORY}"
    exec {LAYOUT_DESCRIPTOR}>>"${LAYOUT_DIRECTORY}/layout.lock"
    if ! flock --exclusive --nonblock "${LAYOUT_DESCRIPTOR}"; then
        echo 'FAIL: another credential or deploy-clean command is checking state directories; try again' >&2
        exit 1
    fi
}

unlock_state_layout() {
    exec {LAYOUT_DESCRIPTOR}>&-
}
