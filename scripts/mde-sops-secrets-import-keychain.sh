#!/usr/bin/env bash
set -euo pipefail

TARGET_FILE="${MDE_MISE_SOPS_FILE:-$HOME/.config/mise/secrets.sops.json}"
AGE_KEY_FILE="${FNOX_AGE_KEY_FILE:-$HOME/.config/mise/age.txt}"
FNOX_CONFIG_FILE="${MDE_FNOX_CONFIG_FILE:-}"
PROVIDER="${MDE_FNOX_IMPORT_PROVIDER:-keychain}"

usage() {
  cat <<'EOF'
Usage: mde-sops-secrets-import-keychain.sh

Decrypts the global mise SOPS secrets file and imports the key/value set into
the selected fnox provider. Defaults to keychain.
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
  local decrypted_json
  local -a fnox_args

  case "${1:-}" in
    -h|--help)
      usage
      exit 0
      ;;
  esac

  require_cmd sops
  require_cmd fnox

  if [[ ! -f "$TARGET_FILE" ]]; then
    printf 'sops secret file missing: %s\n' "$TARGET_FILE" >&2
    exit 1
  fi

  if [[ ! -f "$AGE_KEY_FILE" ]]; then
    printf 'age key missing: %s\n' "$AGE_KEY_FILE" >&2
    exit 1
  fi

  export FNOX_AGE_KEY_FILE="$AGE_KEY_FILE"
  export SOPS_AGE_KEY_FILE="$AGE_KEY_FILE"

  decrypted_json="$(mktemp)"
  trap 'rm -f "${decrypted_json:-}"' EXIT
  sops decrypt "$TARGET_FILE" > "$decrypted_json"

  if [[ "$PROVIDER" == "keychain" ]]; then
    while IFS=$'\t' read -r key value; do
      if [[ -n "$FNOX_CONFIG_FILE" ]]; then
        printf '%s' "$value" | fnox set --config "$FNOX_CONFIG_FILE" --provider keychain "$key"
      else
        printf '%s' "$value" | fnox set --provider keychain "$key"
      fi
    done < <(jq -r 'to_entries[] | [.key, .value] | @tsv' "$decrypted_json")
    exit 0
  fi

  fnox_args=(import --provider "$PROVIDER" --force json)
  if [[ -n "$FNOX_CONFIG_FILE" ]]; then
    fnox_args=(import --config "$FNOX_CONFIG_FILE" --provider "$PROVIDER" --force json)
  fi

  fnox "${fnox_args[@]}" < "$decrypted_json"
}

main "$@"
