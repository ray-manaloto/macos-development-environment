#!/usr/bin/env bash
set -euo pipefail

# Clone agent framework repos for offline research
# Reads source group from configs/mde-reference-sources.json
# Clones into .artifacts/reference-mirror/agent-learning-frameworks/

export GIT_TERMINAL_PROMPT=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MIRROR_ROOT="$REPO_ROOT/.artifacts/reference-mirror/agent-learning-frameworks"
CONFIG="$REPO_ROOT/configs/mde-reference-sources.json"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required but not found. Install via mise or brew." >&2
  exit 1
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "ERROR: Config not found: $CONFIG" >&2
  exit 1
fi

# Get source IDs for the agent-learning-frameworks group
SOURCE_IDS=$(jq -r '
  .source_groups[]
  | select(.id == "agent-learning-frameworks")
  | .source_ids[]
' "$CONFIG")

if [[ -z "$SOURCE_IDS" ]]; then
  echo "ERROR: No source IDs found for agent-learning-frameworks group" >&2
  exit 1
fi

cloned=0
refreshed=0
failed=0
skipped=0

mkdir -p "$MIRROR_ROOT"

while IFS= read -r source_id; do
  # Get source details - only process upstream-repo kind
  source_json=$(jq -r --arg id "$source_id" '
    .sources[] | select(.id == $id and .kind == "upstream-repo")
  ' "$CONFIG")

  if [[ -z "$source_json" ]]; then
    continue
  fi

  url=$(echo "$source_json" | jq -r '.url')
  # Derive directory name: remove -repo suffix from source id
  dir_name="${source_id%-repo}"
  clone_dir="$MIRROR_ROOT/$dir_name"

  if [[ "$DRY_RUN" == true ]]; then
    if [[ -d "$clone_dir/.git" ]]; then
      echo "[dry-run] Would refresh: $dir_name ($url)"
    else
      echo "[dry-run] Would clone:   $dir_name ($url)"
    fi
    continue
  fi

  if [[ -d "$clone_dir/.git" ]]; then
    # Refresh existing clone
    echo "Refreshing $dir_name ..."
    if git -C "$clone_dir" pull --ff-only 2>/dev/null; then
      refreshed=$((refreshed + 1))
    else
      echo "  WARNING: pull --ff-only failed for $dir_name (continuing)"
      failed=$((failed + 1))
    fi
  else
    # Fresh clone
    echo "Cloning $dir_name ..."
    if git clone --depth 1 --single-branch "$url" "$clone_dir" 2>/dev/null; then
      cloned=$((cloned + 1))
    else
      echo "  WARNING: clone failed for $dir_name ($url)"
      failed=$((failed + 1))
    fi
  fi
done <<< "$SOURCE_IDS"

if [[ "$DRY_RUN" == true ]]; then
  echo ""
  echo "Dry run complete. No changes made."
else
  echo ""
  echo "=== Summary ==="
  echo "Cloned:    $cloned"
  echo "Refreshed: $refreshed"
  echo "Failed:    $failed"
fi

exit 0
