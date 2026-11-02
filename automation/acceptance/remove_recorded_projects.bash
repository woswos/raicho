#!/usr/bin/env bash
# Remove the disposable projects this CI job's acceptance runners recorded, even after a cancellation.
set -euo pipefail

ACCEPTANCE_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=automation/acceptance/project_record.bash
source "${ACCEPTANCE_DIRECTORY}/project_record.bash"
# shellcheck source=automation/tooling/clean.bash
source "${ACCEPTANCE_DIRECTORY}/../tooling/clean.bash"

RECORD="${RAICHO_ACCEPTANCE_RECORD:?set RAICHO_ACCEPTANCE_RECORD to the acceptance record}"
OWN_GROUP="$(process_field "$$" "${GROUP_FIELD}")"

# Killing this script's own group would also kill the CI runner. State directories sit beside the record.
valid_entry() {
    local GROUP="${1}" START="${2}" RUNNER="${3}" RUNNER_START="${4}" PROJECT="${5}" STATE_DIRECTORY="${6}"
    [[ ${GROUP} =~ ^[1-9][0-9]*$ && ${GROUP} != "${OWN_GROUP}" && ${START} =~ ^[0-9]+$ ]] \
        && [[ ${RUNNER} =~ ^[1-9][0-9]*$ && ${RUNNER_START} =~ ^[0-9]+$ ]] \
        && [[ ${PROJECT} =~ ${DISPOSABLE_PROJECT} ]] \
        && [[ -z ${STATE_DIRECTORY} || ${STATE_DIRECTORY%/*} == "${RECORD%/*}" ]] \
        && [[ -z ${STATE_DIRECTORY} || ${STATE_DIRECTORY##*/} == raicho-*.???????? ]]
}

# Linux can reuse the ID of an exited process, so a recorded process counts only while its start time
# and process group still match.
running_in_group() {
    local PROCESS="${1}" START="${2}" GROUP="${3}"
    [[ ${START} != 0 && $(process_field "${PROCESS}" "${START_FIELD}") == "${START}" ]] \
        && [[ $(process_field "${PROCESS}" "${GROUP_FIELD}") == "${GROUP}" ]]
}

# The runner can outlive a leader that was killed on its own.
stop_runner() {
    local GROUP="${1}" START="${2}" RUNNER="${3}" RUNNER_START="${4}"
    if running_in_group "${GROUP}" "${START}" "${GROUP}" \
        || running_in_group "${RUNNER}" "${RUNNER_START}" "${GROUP}"; then
        kill -KILL -- "-${GROUP}" 2>/dev/null || true
    fi
}

remove_project_images() {
    local PROJECT="${1}" LISTED IMAGES
    LISTED="$(docker image ls --format '{{.Repository}}:{{.Tag}}' --filter "reference=${PROJECT}:*")" || return 1
    mapfile -t IMAGES < <(printf '%s' "${LISTED}")
    if ((${#IMAGES[@]} > 0)); then
        docker image rm "${IMAGES[@]}" >/dev/null || return 1
        echo "Removed the images of ${PROJECT}"
    fi
}

remove_state_directory() {
    local STATE_DIRECTORY="${1}"
    if [[ -z ${STATE_DIRECTORY} || ! -e ${STATE_DIRECTORY} ]]; then
        return 0
    fi
    if [[ -L ${STATE_DIRECTORY} || ! -d ${STATE_DIRECTORY} || ! -O ${STATE_DIRECTORY} ]]; then
        echo "FAIL: ${STATE_DIRECTORY} is not a state directory this user owns" >&2
        return 1
    fi
    remove_directory "${STATE_DIRECTORY}"
}

# A failed Docker step must not leave the state directory's credentials behind, so every step runs.
remove_recorded_project() {
    local PROJECT="${1}" STATE_DIRECTORY="${2}" RESULT=0 KIND
    # remove_project stops at its first failure, so each kind gets its own call.
    for KIND in container volume network; do
        remove_project "${PROJECT}" "${KIND}" || RESULT=1
    done
    remove_project_images "${PROJECT}" || RESULT=1
    remove_state_directory "${STATE_DIRECTORY}" || RESULT=1
    return "${RESULT}"
}

if [[ ! -e ${RECORD} ]]; then
    exit 0
fi
mapfile -t ENTRIES <"${RECORD}"
RESULT=0
for ENTRY in "${ENTRIES[@]}"; do
    IFS=$'\t' read -r GROUP START RUNNER RUNNER_START PROJECT STATE_DIRECTORY <<<"${ENTRY}"
    if ! valid_entry "${GROUP}" "${START}" "${RUNNER}" "${RUNNER_START}" "${PROJECT}" "${STATE_DIRECTORY}"; then
        echo "FAIL: refused acceptance record entry '${ENTRY}'" >&2
        RESULT=1
        continue
    fi
    # A runner left behind by a cancelled step would recreate what this removes.
    stop_runner "${GROUP}" "${START}" "${RUNNER}" "${RUNNER_START}"
    if ! remove_recorded_project "${PROJECT}" "${STATE_DIRECTORY}"; then
        echo "FAIL: could not remove every resource of ${PROJECT}" >&2
        RESULT=1
    fi
done
exit "${RESULT}"
