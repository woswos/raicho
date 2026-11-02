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
    local GROUP START RUNNER_START
    GROUP="$(process_field "$$" "${GROUP_FIELD}")"
    # A zero start time matches no process, so cleanup then identifies the group by this runner alone.
    START="$(process_field "${GROUP}" "${START_FIELD}")" || START=0
    RUNNER_START="$(process_field "$$" "${START_FIELD}")"
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "${GROUP}" "${START}" "$$" "${RUNNER_START}" "${1}" "${2:-}" \
        >>"${RAICHO_ACCEPTANCE_RECORD}"
}
