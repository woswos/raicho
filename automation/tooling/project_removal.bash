# shellcheck shell=bash
# Sourced by make clean, which make mrproper and make deploy-clean run.

PROJECT_LABEL=com.docker.compose.project

list() {
    local KIND="${1}"
    shift
    if [[ ${KIND} == container ]]; then
        docker container ls --all "${@}"
    else
        docker "${KIND}" ls "${@}"
    fi
}

# Docker deletes a --rm container itself after stop returns, and its volumes stay in use until then.
wait_for_removal() {
    local WAITED
    for ((WAITED = 0; WAITED < 30; WAITED++)); do
        if ! docker container inspect "${1}" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    echo "FAIL: Docker did not remove container ${1}" >&2
    return 1
}

remove_project() {
    local PROJECT="${1}" KIND LISTED IDS SELF_REMOVING CONTAINER
    shift
    for KIND in "${@}"; do
        LISTED="$(list "${KIND}" --quiet --filter "label=${PROJECT_LABEL}=${PROJECT}")" || return 1
        mapfile -t IDS < <(printf '%s' "${LISTED}")
        if ((${#IDS[@]} == 0)); then
            continue
        fi
        if [[ ${KIND} == container ]]; then
            LISTED="$(docker container inspect --format '{{.HostConfig.AutoRemove}} {{.Id}}' "${IDS[@]}")" || return 1
            # A graceful stop protects the volumes that mrproper keeps.
            docker container stop "${IDS[@]}" >/dev/null || return 1
            mapfile -t SELF_REMOVING < <(sed -n 's/^true //p' <<<"${LISTED}")
            for CONTAINER in "${SELF_REMOVING[@]}"; do
                wait_for_removal "${CONTAINER}" || return 1
            done
            mapfile -t IDS < <(sed -n 's/^false //p' <<<"${LISTED}")
        fi
        if ((${#IDS[@]} > 0)); then
            docker "${KIND}" rm "${IDS[@]}" >/dev/null || return 1
        fi
        echo "Removed the ${KIND}s of ${PROJECT}"
    done
}
