#!/usr/bin/env bash
# Run one Make step, reporting what it does and how long it took.
set -euo pipefail

if ((${#} < 2)); then
    echo 'Usage: step.bash TARGET COMMAND...' >&2
    exit 2
fi
TARGET="${1}"
shift

describe() {
    case "${TARGET}" in
        build-*) echo "building|built|${TARGET#build-}" ;;
        deploy-up) echo 'starting|started|deployment' ;;
        deploy-admin) echo 'starting|started|deployment with the Thunderbird desktop' ;;
        deploy-restart) echo 'restarting|restarted|deployment' ;;
        deploy-down) echo 'stopping|stopped|deployment' ;;
        deploy-clean) echo 'removing|removed|deployment' ;;
        deploy-connector-*) echo "running|ran|connector ${TARGET#deploy-connector-}" ;;
        deploy-login-*) echo "running|ran|login ${TARGET#deploy-login-}" ;;
        tooling-image) echo 'building|built|tooling image' ;;
        images) echo 'building|built|runtime images' ;;
        test-*) echo "testing|tested|${TARGET#test-}" ;;
        acceptance-*) echo "testing|tested|${TARGET#acceptance-} acceptance" ;;
        lint-pr) echo 'checking|checked|pull request' ;;
        lint-spelling) echo 'checking|checked|spelling' ;;
        lint-repo) echo 'linting|linted|repository' ;;
        lint-*) echo "linting|linted|${TARGET#lint-}" ;;
        format-check) echo 'checking|checked|formatting' ;;
        format-check-*) echo "checking|checked|${TARGET#format-check-} formatting" ;;
        format) echo 'formatting|formatted|sources' ;;
        format-spelling) echo 'fixing|fixed|typos' ;;
        format-*) echo "formatting|formatted|${TARGET#format-}" ;;
        typecheck) echo 'checking|checked|TypeScript types' ;;
        generate-protocol) echo 'generating|generated|protocol bindings' ;;
        check-protocol) echo 'checking|checked|protocol bindings' ;;
        check-patch-coverage) echo 'checking|checked|patch coverage' ;;
        coverage) echo 'measuring|measured|coverage' ;;
        benchmark) echo 'benchmarking|benchmarked|Rust code' ;;
        audit) echo 'auditing|audited|dependencies' ;;
        clean) echo 'cleaning|cleaned|up' ;;
        mrproper) echo 'removing|removed|everything' ;;
        *) echo "running|ran|${TARGET}" ;;
    esac
}

elapsed() {
    local SECONDS_TAKEN=$(($(date +%s) - STARTED))
    if ((SECONDS_TAKEN == 1)); then
        echo '1 second'
    else
        echo "${SECONDS_TAKEN} seconds"
    fi
}

IFS='|' read -r DOING DONE LABEL <<<"$(describe)"
printf '%s%s %s%s\n' "${COLOR_BLUE:-}" "${DOING}" "${LABEL}" "${COLOR_RESET:-}"
STARTED="$(date +%s)"
if "${@}"; then
    printf '%s%s %s, took %s%s\n' "${COLOR_GREEN:-}" "${DONE}" "${LABEL}" "$(elapsed)" "${COLOR_RESET:-}"
else
    STATUS="${?}"
    printf '%s%s %s failed after %s%s\n' "${COLOR_RED:-}" "${DOING}" "${LABEL}" "$(elapsed)" "${COLOR_RESET:-}" >&2
    exit "${STATUS}"
fi
