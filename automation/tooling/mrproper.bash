#!/usr/bin/env bash
# Clean, then remove every Raicho container, network, and image, keeping deployment volumes and .raicho/.
set -euo pipefail

# shellcheck source=automation/tooling/clean.bash
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/clean.bash"

PROJECT_NAME='^[a-z0-9][a-z0-9_-]*$'
PROJECT_IMAGES=(raicho-tools:local raicho-server:local raicho-gateway:local raicho-thunderbird:local)

projects() {
    local DIRECTORY NAME
    echo raicho
    for DIRECTORY in .raicho/*/; do
        NAME="$(basename "${DIRECTORY}")"
        if [[ -d ${DIRECTORY} && ! -L ${DIRECTORY%/} && ${NAME} =~ ${PROJECT_NAME} ]]; then
            echo "${NAME}"
        fi
    done
    echo raicho-tools
}

stop_project() {
    local PROJECT="${1}" CONTAINERS NETWORKS
    mapfile -t CONTAINERS < <(list container --quiet --filter "label=${PROJECT_LABEL}=${PROJECT}")
    mapfile -t NETWORKS < <(list network --quiet --filter "label=${PROJECT_LABEL}=${PROJECT}")
    if ((${#CONTAINERS[@]} > 0)); then
        docker container stop "${CONTAINERS[@]}" >/dev/null
        docker container rm "${CONTAINERS[@]}" >/dev/null
    fi
    if ((${#NETWORKS[@]} > 0)); then
        docker network rm "${NETWORKS[@]}" >/dev/null
    fi
    if ((${#CONTAINERS[@]} + ${#NETWORKS[@]} > 0)); then
        echo "Removed the containers and networks of ${PROJECT}"
    fi
}

mapfile -t PROJECTS < <(projects | sort -u)
for PROJECT in "${PROJECTS[@]}"; do
    stop_project "${PROJECT}"
done
clean
remove_images "${PROJECT_IMAGES[@]}"
echo 'Mrproper finished. Deployment volumes and .raicho/ were kept.'
