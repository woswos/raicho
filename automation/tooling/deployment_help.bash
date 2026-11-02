#!/usr/bin/env bash
# Print the deployment guide, then the deployment that the deploy- targets select.
set -euo pipefail

HEADING="${COLOR_CYAN:-}"
COMMAND="${COLOR_GREEN:-}"
VALUE="${COLOR_YELLOW:-}"
RESET="${COLOR_RESET:-}"

bash "$(dirname "${BASH_SOURCE[0]}")/guide.bash" "$(dirname "${BASH_SOURCE[0]}")/deployment_help.txt"

row() {
    printf '  %-18s %s%s%s\n' "${1}" "${2}" "${3}" "${RESET}"
}

echo
printf '%s%s%s\n' "${HEADING}" 'Current deployment' "${RESET}"
row project "${VALUE}" "${DEPLOYMENT_PROJECT}"
row 'state directory' "${VALUE}" "${DEPLOYMENT_STATE}"
if [[ -n ${DEPLOYMENT_ENROLLED:-} ]]; then
    row connector "${COMMAND}" enrolled
else
    row connector "${VALUE}" 'not enrolled'
fi
row address "${VALUE}" "http://127.0.0.1:${RAICHO_PORT:-8080}"
