# Sourced by the connector runner and its network tests.

prepare_network() {
    local NETWORK="${RAICHO_PROJECT}_connector-application"
    local SUBNET
    local OPTIONS=(--internal --label "com.docker.compose.project=${RAICHO_PROJECT}"
        --label com.docker.compose.network=connector-application)
    docker network create "${OPTIONS[@]}" "${NETWORK}" >/dev/null
    SUBNET="$(docker network inspect --format '{{(index .IPAM.Config 0).Subnet}}' "${NETWORK}")"
    docker network rm "${NETWORK}" >/dev/null
    docker network create --subnet "${SUBNET}" "${OPTIONS[@]}" "${NETWORK}" >/dev/null
}
