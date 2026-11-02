# Sourced by acceptance runners that own a disposable deployment with generated credentials.

# shellcheck source=automation/acceptance/project_record.bash
source automation/acceptance/project_record.bash

HARDENED_RUN=(docker run --rm -i --read-only --cap-drop ALL --security-opt no-new-privileges:true --workdir /)

prepare_credential_deployment() {
    export RAICHO_PROJECT
    RAICHO_PROJECT="raicho-${1}-$(date -u +%Y%m%d%H%M%S)-${RANDOM}"
    export RAICHO_STATE_DIRECTORY
    RAICHO_STATE_DIRECTORY="$(mktemp -d "${TMPDIR:-/tmp}/raicho-${1}.XXXXXXXX")"
    export RAICHO_CREDENTIAL_DIRECTORY="${RAICHO_STATE_DIRECTORY}/credentials"
    export RAICHO_COMPOSE_TEST=1
    mkdir -m 700 "${RAICHO_CREDENTIAL_DIRECTORY}"
    record_project "${RAICHO_PROJECT}" "${RAICHO_STATE_DIRECTORY}"
    # Project cleanup finds Docker resources only by their Compose project label.
    HARDENED_RUN+=(--label "com.docker.compose.project=${RAICHO_PROJECT}")
    docker volume create --label "com.docker.compose.project=${RAICHO_PROJECT}" \
        --label com.docker.compose.volume=raicho-data "${RAICHO_PROJECT}_raicho-data" >/dev/null
    COMPOSE=(docker compose -p "${RAICHO_PROJECT}" -f compose.yaml
        -f compose.credentials.yaml -f automation/acceptance/runtime/compose.test.yaml)
}

database() {
    "${COMPOSE[@]}" run --rm --no-deps -T provisioner connector "${@}"
}

files() {
    "${COMPOSE[@]}" run --rm --no-deps -T credential-files "${1}" /credentials
}

fixture() {
    "${HARDENED_RUN[@]}" --network none --user 0:0 \
        --cap-add CHOWN --cap-add DAC_OVERRIDE --cap-add FOWNER \
        --mount "type=bind,source=${REPOSITORY_ROOT}/automation,target=/automation,readonly" \
        --mount "type=bind,source=${RAICHO_STATE_DIRECTORY},target=/fixture" \
        --mount "type=volume,source=${RAICHO_PROJECT}_raicho-data,target=/database" \
        --entrypoint python3 raicho-tools:local \
        -B -m automation.acceptance.credentials.checks "${@}"
}

remove_credential_deployment() {
    local RESULT=0
    if ! fixture mutate cleanup; then RESULT=1; fi
    if ! "${COMPOSE[@]}" down --volumes --remove-orphans; then RESULT=1; fi
    rm -f -- "${RAICHO_STATE_DIRECTORY}/operation.lock" "${RAICHO_STATE_DIRECTORY}/project"
    rmdir -- "${RAICHO_STATE_DIRECTORY}" || RESULT=1
    return "${RESULT}"
}

# Runners redefine these hooks to report extra diagnostics or release their own resources.
on_failure() { :; }
on_cleanup() { :; }

cleanup_credential_deployment() {
    local RESULT="${?}"
    trap - EXIT
    if ((RESULT != 0)); then
        "${COMPOSE[@]}" ps --all || true
        on_failure || true
    fi
    on_cleanup || true
    remove_credential_deployment || RESULT=1
    exit "${RESULT}"
}

install_cleanup() {
    trap cleanup_credential_deployment EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
}
