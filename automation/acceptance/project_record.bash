# shellcheck shell=bash
# Sourced by acceptance runners and remove_recorded_projects.bash, which reads what they record.

GROUP_FIELD=2
START_FIELD=19

# Prints one /proc/PID/stat field, counted after the command name because that name may contain spaces.
process_field() {
    local STATUS FIELDS
    STATUS="$(cat "/proc/${1}/stat" 2>/dev/null)" || return 1
    read -r -a FIELDS <<<"${STATUS##*) }"
    echo "${FIELDS[${2}]}"
}

# A cancelled CI step kills only its entry shell and leaves the runner without its cleanup.
record_project() {
    if [[ -z ${RAICHO_ACCEPTANCE_RECORD:-} ]]; then
        return 0
    fi
    local GROUP START
    GROUP="$(process_field "$$" "${GROUP_FIELD}")"
    # Cleanup never kills a group recorded with a zero start time, because nothing identifies its leader.
    START="$(process_field "${GROUP}" "${START_FIELD}")" || START=0
    printf '%s\t%s\t%s\t%s\n' "${GROUP}" "${START}" "${1}" "${2:-}" >>"${RAICHO_ACCEPTANCE_RECORD}"
}
