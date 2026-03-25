#!/usr/bin/env bash
# remind-chezmoi-commit.sh — Remind to commit after chezmoi apply
#
# After a successful chezmoi apply, check if the source directory has
# uncommitted changes and remind the user to commit/push.
#
# Reads TOOL_INPUT_COMMAND from environment (never as a shell argument).

set -euo pipefail

# Read from environment — safe from shell injection
COMMAND="${TOOL_INPUT_COMMAND:-}"

# Only trigger after chezmoi apply/re-add/add (not mentions in comments)
# Use first line only to avoid multi-line false positives
FIRST_LINE="${COMMAND%%$'\n'*}"

if [[ ! "$FIRST_LINE" =~ ^chezmoi\ (apply|re-add|add)( |$) ]]; then
  exit 0
fi

# Skip if it was a dry-run
if [[ "$FIRST_LINE" == *"--dry-run"* ]]; then
  exit 0
fi

# Check if chezmoi source has uncommitted changes (in subshell to avoid cwd mutation)
SOURCE_DIR="$(chezmoi source-path 2>/dev/null || echo "")"
if [[ -z "$SOURCE_DIR" ]] || [[ ! -d "$SOURCE_DIR" ]]; then
  exit 0
fi

if (cd "$SOURCE_DIR" && git status --porcelain 2>/dev/null | grep -q .); then
  echo "REMINDER: Chezmoi source has uncommitted changes."
  echo "Run: chezmoi git -- add -A && chezmoi git -- commit -m 'Update dotfiles'"
  echo "Then: chezmoi git -- push"
fi

exit 0
