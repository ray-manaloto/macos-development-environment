#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_SLUG="$(basename "$REPO_ROOT")"

make_temp_dir() {
  local prefix="$1"
  local dir
  dir="$(mktemp -d "/tmp/${prefix}.XXXXXX" 2>/dev/null || mktemp -d -t "$prefix")"
  chmod 0777 "$dir"
  printf '%s\n' "$dir"
}

RUN_ID="mde-devcontainer-smoke-$(date +%Y%m%d%H%M%S)-$$"
ID_LABEL="mde.devcontainer.smoke=$RUN_ID"
REPO_LABEL="mde.devcontainer.repo=$REPO_SLUG"
WORKSPACE_LABEL="mde.devcontainer.workspace=$REPO_ROOT"
export MDE_DEVCONTAINER_IMAGE="${MDE_DEVCONTAINER_IMAGE:-mde-devcontainer:local}"
USER_DATA_DIR="$(make_temp_dir mde-devcontainer-user)"
CONTAINER_DATA_DIR="$(make_temp_dir mde-devcontainer-data)"
CONTAINER_SYSTEM_DATA_DIR="$(make_temp_dir mde-devcontainer-system)"
SESSION_DATA_DIR="$(make_temp_dir mde-devcontainer-session)"
CLI_TMPDIR="$(make_temp_dir mde-devcontainer-cli)"
export TMPDIR="$CLI_TMPDIR"

cleanup() {
  "$REPO_ROOT/scripts/devcontainer-cleanup.sh" >/dev/null 2>&1 || true
  rm -rf \
    "$CLI_TMPDIR" \
    "$USER_DATA_DIR" \
    "$CONTAINER_DATA_DIR" \
    "$CONTAINER_SYSTEM_DATA_DIR" \
    "$SESSION_DATA_DIR"
}
trap cleanup EXIT

cd "$REPO_ROOT"
"$REPO_ROOT/scripts/devcontainer-cleanup.sh"

devcontainer up \
  --workspace-folder "$REPO_ROOT" \
  --user-data-folder "$USER_DATA_DIR" \
  --container-data-folder "$CONTAINER_DATA_DIR" \
  --container-system-data-folder "$CONTAINER_SYSTEM_DATA_DIR" \
  --container-session-data-folder "$SESSION_DATA_DIR" \
  --remove-existing-container \
  --id-label "$ID_LABEL" \
  --id-label "$REPO_LABEL" \
  --id-label "$WORKSPACE_LABEL"

devcontainer exec \
  --workspace-folder "$REPO_ROOT" \
  --id-label "$ID_LABEL" \
  --id-label "$REPO_LABEL" \
  --id-label "$WORKSPACE_LABEL" \
  bash -lc '
    set -euo pipefail
    export PATH="$HOME/.local/bin:$HOME/.local/share/mise/bin:$HOME/.local/share/mise/shims:$PATH"

    [[ "$(whoami)" == "vscode" ]]
    [[ "${MDE_PLATFORM:-}" == "devcontainer" ]]
    [[ "${MDE_ENV_AUTOLOAD:-}" == "0" ]]
    [[ "${MDE_AUTOLOAD_SECRETS:-}" == "0" ]]
    [[ -f "$HOME/.local/state/macos-development-environment/devcontainer-bootstrap.sha256" ]]

    scripts/ensure-managed-configs.sh --check
    mise run mde:verify
    mise run mde:drift

    status_json="$(mise run mde:status)"
    printf "%s\n" "$status_json" | jq -e . >/dev/null

    bash .devcontainer/post-create.sh
    scripts/ensure-managed-configs.sh --check
    mise run mde:drift
  '
