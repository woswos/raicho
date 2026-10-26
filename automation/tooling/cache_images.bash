#!/usr/bin/env bash
# Build images with the GitHub Actions layer cache, matching the Compose builds that reuse them.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."
for IMAGE in "${@}"; do
    ARGUMENTS=()
    case "${IMAGE}" in
        server)
            ARGUMENTS=(--file deploy/raicho/Dockerfile --tag raicho-server:local
                --build-arg "RAICHO_COMMIT=${RAICHO_COMMIT:-unknown}")
            ;;
        gateway) ARGUMENTS=(--file deploy/gateway/Dockerfile --tag raicho-gateway:local) ;;
        thunderbird) ARGUMENTS=(--file deploy/thunderbird/Dockerfile --tag raicho-thunderbird:local) ;;
        *)
            echo "FAIL: unknown image ${IMAGE}" >&2
            exit 1
            ;;
    esac
    if [[ -n ${ACTIONS_RUNTIME_TOKEN:-} ]]; then
        ARGUMENTS+=(--cache-from "type=gha,scope=${IMAGE}")
        if [[ -n ${RAICHO_IMAGE_CACHE_WRITE:-} ]]; then
            ARGUMENTS+=(--cache-to "type=gha,scope=${IMAGE},mode=max")
        fi
    fi
    docker buildx build --load --progress quiet "${ARGUMENTS[@]}" . >/dev/null
    echo "Built ${IMAGE}"
done
