#!/usr/bin/env bash
# Remove regenerable build output and interrupted acceptance deployments.
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIRECTORY}/../.." && pwd)"
cd "${REPOSITORY_ROOT}"

PROJECT_LABEL=com.docker.compose.project
DISPOSABLE_PROJECT='^raicho-[a-z]+-[0-9]+-[0-9]+$'
DISPOSABLE_IMAGE='^raicho-[a-z]+-[0-9]+-[0-9]+[:-]'
CACHE_VOLUME=raicho-tools_cache
TEMPORARY_DIRECTORY="${TMPDIR:-/tmp}"

remove_ignored_output() {
    local IGNORED IGNORED_PATH
    mapfile -t -d '' IGNORED < <(
        git ls-files -z --others --ignored --directory --exclude-per-directory=.gitignore
    )
    for IGNORED_PATH in "${IGNORED[@]}"; do
        if [[ ${IGNORED_PATH} == .raicho/* ]]; then
            continue
        fi
        rm -rf -- "${IGNORED_PATH}"
        echo "Removed ${IGNORED_PATH}"
    done
}

list() {
    local KIND="${1}"
    shift
    if [[ ${KIND} == container ]]; then
        docker container ls --all "${@}"
    else
        docker "${KIND}" ls "${@}"
    fi
}

remove_project() {
    local PROJECT="${1}" KIND IDS
    for KIND in container volume network; do
        mapfile -t IDS < <(list "${KIND}" --quiet --filter "label=${PROJECT_LABEL}=${PROJECT}")
        if ((${#IDS[@]} == 0)); then
            continue
        fi
        if [[ ${KIND} == container ]]; then
            docker container rm --force "${IDS[@]}" >/dev/null
        else
            docker "${KIND}" rm "${IDS[@]}" >/dev/null
        fi
    done
    echo "Removed acceptance project ${PROJECT}"
}

remove_disposable_projects() {
    local PROJECTS PROJECT KIND
    mapfile -t PROJECTS < <(
        for KIND in container volume network; do
            list "${KIND}" --format "{{.Label \"${PROJECT_LABEL}\"}}"
        done | grep -E "${DISPOSABLE_PROJECT}" | sort -u
    )
    for PROJECT in "${PROJECTS[@]}"; do
        remove_project "${PROJECT}"
    done
}

remove_state_directories() {
    local DIRECTORY
    for DIRECTORY in "${TEMPORARY_DIRECTORY}"/raicho-*.????????; do
        if [[ ! -d ${DIRECTORY} || -L ${DIRECTORY} || ! -O ${DIRECTORY} ]]; then
            continue
        fi
        if ! rm -rf -- "${DIRECTORY}" 2>/dev/null; then
            # Acceptance fixtures leave root-owned credential files behind.
            docker run --rm --pull never --network none --user 0:0 \
                --mount "type=bind,source=${DIRECTORY},target=/state" \
                --entrypoint find raicho-tools:local /state -mindepth 1 -delete || true
            if ! rmdir -- "${DIRECTORY}" 2>/dev/null; then
                echo "Kept ${DIRECTORY}: remove it as the user that owns its files" >&2
                continue
            fi
        fi
        echo "Removed ${DIRECTORY}"
    done
}

remove_cache() {
    if ! docker volume inspect "${CACHE_VOLUME}" >/dev/null 2>&1; then
        return 0
    fi
    if docker volume rm "${CACHE_VOLUME}" >/dev/null 2>&1; then
        echo "Removed cache volume ${CACHE_VOLUME}"
    else
        echo "Kept cache volume ${CACHE_VOLUME}, which a container still uses" >&2
    fi
}

remove_images() {
    local IMAGE
    for IMAGE in "${@}"; do
        if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
            continue
        fi
        if docker image rm "${IMAGE}" >/dev/null 2>&1; then
            echo "Removed image ${IMAGE}"
        else
            echo "Kept image ${IMAGE}, which a container still uses" >&2
        fi
    done
}

clean() {
    local DISPOSABLE_IMAGES
    remove_ignored_output
    remove_disposable_projects
    remove_state_directories
    remove_cache
    mapfile -t DISPOSABLE_IMAGES < <(
        docker image ls --format '{{.Repository}}:{{.Tag}}' | grep -E "${DISPOSABLE_IMAGE}"
    )
    remove_images "${DISPOSABLE_IMAGES[@]}"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
    clean
    echo 'Clean finished. Project images, the raicho deployment, its volumes, and .raicho/ were kept.'
fi
