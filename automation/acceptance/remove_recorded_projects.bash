#!/usr/bin/env bash
# Remove the disposable projects this CI job's acceptance runners recorded, even after a cancellation.
set -euo pipefail

ACCEPTANCE_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=automation/acceptance/project_record.bash
source "${ACCEPTANCE_DIRECTORY}/project_record.bash"
# shellcheck source=automation/tooling/clean.bash
source "${ACCEPTANCE_DIRECTORY}/../tooling/clean.bash"

RECORD="${RAICHO_ACCEPTANCE_RECORD:?set RAICHO_ACCEPTANCE_RECORD to the acceptance record}"
OWN_GROUP="$(process_group "$$")"

# Killing this script's own group would also kill the CI runner.
valid_entry() {
    local GROUP="${1}" PROJECT="${2}" STATE_DIRECTORY="${3}"
    [[ ${GROUP} =~ ^[1-9][0-9]*$ && ${GROUP} != "${OWN_GROUP}" && ${PROJECT} =~ ${DISPOSABLE_PROJECT} ]] \
        && [[ -z ${STATE_DIRECTORY} || ${STATE_DIRECTORY##*/} == raicho-*.???????? ]]
}

# Probe, fixture, and holder containers carry no project label but keep its networks and volumes in use.
remove_attached_containers() {
    local PROJECT="${1}" KIND LISTED NAMES NAME CONTAINERS='' IDS
    for KIND in network volume; do
        LISTED="$(list "${KIND}" --format '{{.Name}}' --filter "label=${PROJECT_LABEL}=${PROJECT}")" || return 1
        mapfile -t NAMES < <(printf '%s' "${LISTED}")
        for NAME in "${NAMES[@]}"; do
            CONTAINERS+="$(list container --quiet --filter "${KIND}=${NAME}")"$'\n' || return 1
        done
    done
    mapfile -t IDS < <(sort -u <<<"${CONTAINERS}" | sed '/^$/d')
    if ((${#IDS[@]} > 0)); then
        docker container rm --force "${IDS[@]}" >/dev/null || return 1
    fi
}

remove_recorded_project() {
    local PROJECT="${1}" STATE_DIRECTORY="${2}" LISTED IMAGES
    remove_attached_containers "${PROJECT}" || return 1
    remove_project "${PROJECT}" container volume network || return 1
    LISTED="$(docker image ls --format '{{.Repository}}:{{.Tag}}' --filter "reference=${PROJECT}:*")" || return 1
    mapfile -t IMAGES < <(printf '%s' "${LISTED}")
    remove_images "${IMAGES[@]}"
    if [[ -z ${STATE_DIRECTORY} || ! -e ${STATE_DIRECTORY} ]]; then
        return 0
    fi
    if [[ -L ${STATE_DIRECTORY} || ! -d ${STATE_DIRECTORY} || ! -O ${STATE_DIRECTORY} ]]; then
        echo "FAIL: ${STATE_DIRECTORY} is not a state directory this user owns" >&2
        return 1
    fi
    remove_directory "${STATE_DIRECTORY}"
}

if [[ ! -e ${RECORD} ]]; then
    exit 0
fi
mapfile -t ENTRIES <"${RECORD}"
RESULT=0
for ENTRY in "${ENTRIES[@]}"; do
    IFS=$'\t' read -r GROUP PROJECT STATE_DIRECTORY <<<"${ENTRY}"
    if ! valid_entry "${GROUP}" "${PROJECT}" "${STATE_DIRECTORY}"; then
        echo "FAIL: refused acceptance record entry '${ENTRY}'" >&2
        RESULT=1
        continue
    fi
    # A runner left behind by a cancelled step would recreate what this removes.
    kill -KILL -- "-${GROUP}" 2>/dev/null || true
    if ! remove_recorded_project "${PROJECT}" "${STATE_DIRECTORY}"; then
        echo "FAIL: could not remove every resource of ${PROJECT}" >&2
        RESULT=1
    fi
done
exit "${RESULT}"
