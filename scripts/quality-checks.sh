#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

list_scripts() {
  find "$ROOT_DIR/scripts" -type f -maxdepth 1 -print
}

run_bash_syntax() {
  local failed=0
  while IFS= read -r file; do
    if [[ "$file" == *.sh || "$file" == */agent-hud ]]; then
      bash -n "$file" || failed=1
    fi
  done < <(list_scripts)
  return "$failed"
}

run_shellcheck() {
  if ! command -v shellcheck >/dev/null 2>&1; then
    echo "shellcheck not installed; skipping"
    return 0
  fi
  local scripts=()
  mapfile -t scripts < <(list_scripts)
  if (( ${#scripts[@]} == 0 )); then
    return 0
  fi
  shellcheck -x "${scripts[@]}"
}

run_bash_syntax
run_shellcheck

echo "Quality checks completed."
