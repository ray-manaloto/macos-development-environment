#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET_FILE="${MDE_MISE_SOPS_FILE:-$HOME/.config/mise/secrets.sops.json}"
AGE_KEY_FILE="${FNOX_AGE_KEY_FILE:-$HOME/.config/mise/age.txt}"
FNOX_CONFIG_FILE="${MDE_FNOX_CONFIG_FILE:-}"

usage() {
  cat <<'EOF'
Usage: mde-sops-secrets-refresh.sh

Exports the current merged fnox secret set and rewrites the global
mise-managed SOPS file used for shell runtime secret loading.
EOF
}

require_cmd() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    printf 'missing required command: %s\n' "$name" >&2
    exit 1
  fi
}

main() {
  local export_json plaintext_json encrypted_json recipient
  local -a fnox_args
  export_json="$(mktemp)"
  plaintext_json="$(mktemp)"
  encrypted_json="$(mktemp)"
  trap 'rm -f "${export_json:-}" "${plaintext_json:-}" "${encrypted_json:-}"' EXIT

  case "${1:-}" in
    -h|--help)
      usage
      exit 0
      ;;
  esac

  require_cmd fnox
  require_cmd jq
  require_cmd sops
  require_cmd age-keygen

  if [[ ! -f "$AGE_KEY_FILE" ]]; then
    printf 'age key missing: %s\n' "$AGE_KEY_FILE" >&2
    exit 1
  fi

  export MISE_ENV_CACHE="${MISE_ENV_CACHE:-1}"
  export FNOX_CONFIG_DIR="${FNOX_CONFIG_DIR:-$HOME/.config/fnox}"
  export FNOX_AGE_KEY_FILE="$AGE_KEY_FILE"
  export SOPS_AGE_KEY_FILE="$AGE_KEY_FILE"

  recipient="$(age-keygen -y "$AGE_KEY_FILE")"
  mkdir -p "$(dirname "$TARGET_FILE")"

  fnox_args=(export --format json)
  if [[ -n "$FNOX_CONFIG_FILE" ]]; then
    fnox_args+=(--config "$FNOX_CONFIG_FILE")
  fi

  fnox "${fnox_args[@]}" > "$export_json"
  jq -e '.secrets | type == "object"' "$export_json" >/dev/null
  jq '.secrets' "$export_json" > "$plaintext_json"

  sops encrypt \
    --input-type json \
    --output-type json \
    --age "$recipient" \
    "$plaintext_json" > "$encrypted_json"

  chmod 600 "$encrypted_json"
  mv "$encrypted_json" "$TARGET_FILE"

  sops decrypt "$TARGET_FILE" | jq -e 'type == "object"' >/dev/null
  printf 'updated %s\n' "$TARGET_FILE"
}

main "$@"
