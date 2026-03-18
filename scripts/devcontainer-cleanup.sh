#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_SLUG="${MDE_DEVCONTAINER_REPO_SLUG:-$(basename "$REPO_ROOT")}"
WORKSPACE_SOURCE="${MDE_DEVCONTAINER_WORKSPACE_SOURCE:-$REPO_ROOT}"
WORKSPACE_TARGET="${MDE_DEVCONTAINER_WORKSPACE_TARGET:-/workspaces/$REPO_SLUG}"

collect_container_ids() {
  docker ps -aq \
    --filter "label=mde.devcontainer.smoke" \
    --filter "label=desktop.docker.io/mounts/0/Source=$WORKSPACE_SOURCE" \
    --filter "label=desktop.docker.io/mounts/0/Target=$WORKSPACE_TARGET" \
    2>/dev/null || true

  docker ps -aq \
    --filter "label=mde.devcontainer.repo=$REPO_SLUG" \
    --filter "label=mde.devcontainer.workspace=$WORKSPACE_SOURCE" \
    2>/dev/null || true
}

main() {
  local ids=""

  ids="$(collect_container_ids | awk 'NF && !seen[$0]++')"
  [[ -n "$ids" ]] || return 0

  printf '%s\n' "$ids" | xargs docker rm -f >/dev/null
}

main "$@"
