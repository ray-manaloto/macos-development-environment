#!/usr/bin/env bash
set -euo pipefail

TARGET_FILE="${MDE_MISE_SOPS_FILE:-$HOME/.config/mise/secrets.sops.json}"
VAULT="${MDE_OP_VAULT:-Personal}"
TITLE="${MDE_OP_SOPS_TITLE:-mde-secrets.sops.json}"
TAGS="${MDE_OP_SOPS_TAGS:-mde,secrets,sops,backup}"
INCLUDE_AGE_KEY="${MDE_OP_INCLUDE_AGE_KEY:-0}"
AGE_KEY_FILE="${FNOX_AGE_KEY_FILE:-$HOME/.config/mise/age.txt}"
AGE_KEY_TITLE="${MDE_OP_AGE_KEY_TITLE:-mde-age-key.txt}"

usage() {
  cat <<'EOF'
Usage: mde-sops-secrets-backup-1password.sh

Backs up the encrypted mise SOPS secrets file into a 1Password Document item.
Set MDE_OP_INCLUDE_AGE_KEY=1 only if you explicitly want to back up the age key
as a second document.
EOF
}

require_cmd() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    printf 'missing required command: %s\n' "$name" >&2
    exit 1
  fi
}

require_op_session() {
  if op vault list >/dev/null 2>&1; then
    return 0
  fi

  cat >&2 <<'EOF'
1Password CLI does not have an active signed-in session for vault/document access.
Run `eval "$(op signin)"` in an interactive shell first, then rerun this script.
EOF
  exit 1
}

upsert_document() {
  local title="$1"
  local file_path="$2"
  local item_id

  item_id="$(
    op document list --vault "$VAULT" --format json | \
      jq -r --arg title "$title" '.[] | select(.title == $title) | .id' | \
      head -n1
  )"

  if [[ -n "$item_id" ]]; then
    op document edit "$item_id" "$file_path" \
      --vault "$VAULT" \
      --title "$title" \
      --file-name "$(basename "$file_path")" \
      --tags "$TAGS" >/dev/null
  else
    op document create "$file_path" \
      --vault "$VAULT" \
      --title "$title" \
      --file-name "$(basename "$file_path")" \
      --tags "$TAGS" >/dev/null
  fi
}

main() {
  case "${1:-}" in
    -h|--help)
      usage
      exit 0
      ;;
  esac

  require_cmd op
  require_cmd jq

  if [[ ! -f "$TARGET_FILE" ]]; then
    printf 'sops secret file missing: %s\n' "$TARGET_FILE" >&2
    exit 1
  fi

  require_op_session

  upsert_document "$TITLE" "$TARGET_FILE"
  printf 'backed up %s to 1Password vault %s as %s\n' "$TARGET_FILE" "$VAULT" "$TITLE"

  if [[ "$INCLUDE_AGE_KEY" == "1" ]]; then
    if [[ ! -f "$AGE_KEY_FILE" ]]; then
      printf 'age key missing: %s\n' "$AGE_KEY_FILE" >&2
      exit 1
    fi
    upsert_document "$AGE_KEY_TITLE" "$AGE_KEY_FILE"
    printf 'backed up %s to 1Password vault %s as %s\n' "$AGE_KEY_FILE" "$VAULT" "$AGE_KEY_TITLE"
  fi
}

main "$@"
