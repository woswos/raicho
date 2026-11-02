#!/usr/bin/env bash
# Print a target guide, with headings, commands, and variables in the colors that Make exports.
set -euo pipefail

if ((${#} != 1)); then
    echo 'Usage: guide.bash GUIDE' >&2
    exit 2
fi
sed -E \
    -e "s/^# (.*)$/${COLOR_CYAN:-}\1${COLOR_RESET:-}/" \
    -e "s/make [a-z<>-]+/${COLOR_GREEN:-}&${COLOR_RESET:-}/g" \
    -e "s/(RAICHO|COMPOSE|PR)_[A-Z_]+|(VERBOSE|FOLLOW)=1|(TEST|SERVICE)=/${COLOR_YELLOW:-}&${COLOR_RESET:-}/g" \
    "${1}"
