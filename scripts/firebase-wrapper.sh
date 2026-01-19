#!/usr/bin/env bash
set -euo pipefail

self_path="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
log_dir="$HOME/Library/Logs/firebase-tools"

find_firebase() {
  local entry=""
  local candidate=""
  IFS=':' read -r -a entries <<< "$PATH"
  for entry in "${entries[@]}"; do
    candidate="$entry/firebase"
    if [[ "$candidate" == "$self_path" ]]; then
      continue
    fi
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

firebase_bin="${FIREBASE_REAL:-}"
if [[ -z "$firebase_bin" ]]; then
  firebase_bin="$(find_firebase || true)"
fi

if [[ -z "$firebase_bin" ]]; then
  echo "firebase CLI not found in PATH." >&2
  exit 1
fi

set +e
"$firebase_bin" "$@"
status=$?
set -e

if [[ -f "firebase-debug.log" ]]; then
  mkdir -p "$log_dir"
  ts="$(date '+%Y%m%d_%H%M%S')"
  mv "firebase-debug.log" "$log_dir/firebase-debug-$ts.log" 2>/dev/null || true
fi

exit "$status"
