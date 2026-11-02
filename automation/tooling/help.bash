#!/usr/bin/env bash
# Print the target guide, then the deployment that the deploy- targets select when Make names one.
set -euo pipefail

HEADING="${COLOR_CYAN:-}"
COMMAND="${COLOR_GREEN:-}"
VALUE="${COLOR_YELLOW:-}"
RESET="${COLOR_RESET:-}"

sed -E \
    -e "s/^# (.*)$/${HEADING}\1${RESET}/" \
    -e "s/make [a-z<>-]+/${COMMAND}&${RESET}/g" \
    -e "s/(RAICHO|COMPOSE|PR)_[A-Z_]+|(VERBOSE|FOLLOW)=1|(TEST|SERVICE)=/${VALUE}&${RESET}/g" \
    "$(dirname "${BASH_SOURCE[0]}")/help.txt"

if [[ -z ${DEPLOYMENT_PROJECT:-} ]]; then
    exit 0
fi

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
