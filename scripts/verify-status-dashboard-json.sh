#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATUS_SCRIPT="$SCRIPT_DIR/status-dashboard.sh"

if [[ ! -x "$STATUS_SCRIPT" ]]; then
  echo "status-dashboard script missing: $STATUS_SCRIPT" >&2
  exit 1
fi

json_output="$("$STATUS_SCRIPT" --json)"

if command -v jq >/dev/null 2>&1; then
  printf '%s\n' "$json_output" | jq -e . >/dev/null
  exit 0
fi

if command -v python3 >/dev/null 2>&1; then
  printf '%s\n' "$json_output" | python3 -c 'import json,sys; json.load(sys.stdin)'
  exit 0
fi

echo "strict JSON verification requires jq or python3" >&2
exit 1
