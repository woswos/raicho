# shellcheck shell=bash
# Sourced by acceptance runners and remove_recorded_projects.bash, which reads what they record.

process_group() {
    local STATUS FIELDS
    STATUS="$(<"/proc/${1}/stat")" || return 1
    # The command name in parentheses may contain spaces, so count fields after it.
    read -r -a FIELDS <<<"${STATUS##*) }"
    echo "${FIELDS[2]}"
}

# A cancelled CI step kills only its entry shell and leaves the runner without its cleanup.
record_project() {
    if [[ -z ${RAICHO_ACCEPTANCE_RECORD:-} ]]; then
        return 0
    fi
    local GROUP
    GROUP="$(process_group "$$")"
    printf '%s\t%s\t%s\n' "${GROUP}" "${1}" "${2:-}" >>"${RAICHO_ACCEPTANCE_RECORD}"
}
