# Sourced by acceptance runners that own a disposable deployment with generated credentials.

prepare_credential_deployment() {
    export RAICHO_PROJECT
    RAICHO_PROJECT="raicho-${1}-$(date -u +%Y%m%d%H%M%S)-${RANDOM}"
    export RAICHO_STATE_DIRECTORY
    RAICHO_STATE_DIRECTORY="$(mktemp -d "/tmp/raicho-${1}.XXXXXXXX")"
    export RAICHO_CREDENTIAL_DIRECTORY="${RAICHO_STATE_DIRECTORY}/credentials"
    export RAICHO_COMPOSE_TEST=1
    mkdir -m 700 "${RAICHO_CREDENTIAL_DIRECTORY}"
    COMPOSE=(docker compose -p "${RAICHO_PROJECT}" -f compose/compose.yaml
        -f compose/compose.credentials.yaml -f compose/compose.runtime_test.yaml)
}

fixture() {
    docker run --rm -i --network none --read-only --user 0:0 \
        --cap-drop ALL --cap-add CHOWN --cap-add DAC_OVERRIDE --cap-add FOWNER \
        --security-opt no-new-privileges:true --workdir / \
        --mount "type=bind,source=${REPOSITORY_ROOT}/automation,target=/automation,readonly" \
        --mount "type=bind,source=${RAICHO_STATE_DIRECTORY},target=/fixture" \
        --mount "type=volume,source=${RAICHO_PROJECT}_raicho-data,target=/database" \
        --entrypoint python3 raicho-tools:local \
        -B -m automation.acceptance.credentials.raicho_credential_checks "${@}"
}

remove_credential_deployment() {
    local RESULT=0
    if ! fixture mutate cleanup; then RESULT=1; fi
    if ! "${COMPOSE[@]}" down --volumes --remove-orphans; then RESULT=1; fi
    rm -f -- "${RAICHO_STATE_DIRECTORY}/operation.lock"
    rmdir -- "${RAICHO_STATE_DIRECTORY}" || RESULT=1
    return "${RESULT}"
}
