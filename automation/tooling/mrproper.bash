#!/usr/bin/env bash
# Clean, then remove every Raicho container, network, and image, keeping deployment volumes and .raicho/.
set -euo pipefail

# shellcheck source=automation/tooling/clean.bash
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/clean.bash"
# shellcheck source=deploy/credentials/state.bash
source "${REPOSITORY_ROOT}/deploy/credentials/state.bash"

PROJECT_IMAGES=(raicho-tools:local raicho-server:local raicho-gateway:local raicho-thunderbird:local)

projects() {
    local DIRECTORY NAME WORKING_DIRECTORY
    echo raicho
    for DIRECTORY in .raicho/*/; do
        NAME="$(basename "${DIRECTORY}")"
        if [[ -d ${DIRECTORY} && ! -L ${DIRECTORY%/} && ${NAME} =~ ${PROJECT_NAME} ]]; then
            echo "${NAME}"
        fi
    done
    # Deployments that were never enrolled have no state directory, so find them by the checkout that started them.
    while IFS=$'\t' read -r NAME WORKING_DIRECTORY; do
        if [[ ${NAME} =~ ${PROJECT_NAME} && ${WORKING_DIRECTORY}/ == "${REPOSITORY_ROOT}"/* ]]; then
            echo "${NAME}"
        fi
    done <<<"${CONTAINER_PROJECTS}"
    echo raicho-tools
}

# Capturing the listing first keeps a Docker failure from reading as no projects.
CONTAINER_PROJECTS="$(list container --format "{{.Label \"${PROJECT_LABEL}\"}}\t{{.Label \"${PROJECT_LABEL}.working_dir\"}}")"
mapfile -t PROJECTS < <(projects | sort -u)
for PROJECT in "${PROJECTS[@]}"; do
    remove_project "${PROJECT}" container network
done
clean
remove_images "${PROJECT_IMAGES[@]}"
echo 'Mrproper finished. Deployment volumes and .raicho/ were kept.'
