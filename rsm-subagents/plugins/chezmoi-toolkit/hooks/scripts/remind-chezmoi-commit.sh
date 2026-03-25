#!/usr/bin/env bash
# remind-chezmoi-commit.sh — Remind to commit after chezmoi apply
#
# After a successful chezmoi apply, check if the source directory has
# uncommitted changes and remind the user to commit/push.
#
# Called by PostToolUse:Bash hook with the command as $1.

set -euo pipefail

COMMAND="${1:-}"

# Only trigger after chezmoi apply (not dry-run)
if ! echo "$COMMAND" | grep -qE 'chezmoi (apply|re-add|add)'; then
  exit 0
fi

# Skip if it was a dry-run
if echo "$COMMAND" | grep -q '\-\-dry-run'; then
  exit 0
fi

# Check if chezmoi source has uncommitted changes
SOURCE_DIR="$(chezmoi source-path 2>/dev/null || echo "")"
if [[ -z "$SOURCE_DIR" ]] || [[ ! -d "$SOURCE_DIR" ]]; then
  exit 0
fi

# Check git status in source directory
if (cd "$SOURCE_DIR" && git status --porcelain 2>/dev/null | grep -q .); then
  echo "REMINDER: Chezmoi source has uncommitted changes."
  echo "Run: chezmoi git -- add -A && chezmoi git -- commit -m 'Update dotfiles'"
  echo "Then: chezmoi git -- push"
fi

exit 0
