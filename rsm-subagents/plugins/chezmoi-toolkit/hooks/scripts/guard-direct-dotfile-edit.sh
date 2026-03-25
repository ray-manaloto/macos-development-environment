#!/usr/bin/env bash
# guard-direct-dotfile-edit.sh — Block direct edits to chezmoi-managed dotfiles
#
# Enforces the source-first workflow: edits must go through chezmoi source,
# not by directly modifying deployed files in ~/.
#
# Reads TOOL_INPUT_COMMAND from environment (never as a shell argument,
# to prevent injection via shell metacharacters).

set -euo pipefail

# Read from environment — safe from shell injection
COMMAND="${TOOL_INPUT_COMMAND:-}"

# Skip empty commands
[[ -z "$COMMAND" ]] && exit 0

# Collapse multi-line commands to first line only for matching.
# Multi-line commands could bypass guards if each line is matched
# independently (e.g., "chezmoi edit\nvim ~/.bashrc").
FIRST_LINE="${COMMAND%%$'\n'*}"

# Allow if the command itself IS a chezmoi command
if [[ "$FIRST_LINE" =~ ^chezmoi\ (edit|cd|add|source-path) ]]; then
  exit 0
fi

# Allow if operating on chezmoi source directory
if [[ "$FIRST_LINE" == *".local/share/chezmoi"* ]]; then
  exit 0
fi

# Patterns that indicate direct editing of deployed dotfiles
MANAGED_PATTERNS=(
  'vim ~/\.'
  'nvim ~/\.'
  'nano ~/\.'
  'hx ~/\.'
  'code ~/\.'
  'sed -i.* ~/\.'
  'perl -pi.* ~/\.'
  'tee ~/\.'
)

# Patterns for redirect/copy operations targeting dotfiles
REDIRECT_PATTERNS=(
  'echo .* >> ~/\.'
  'cat .* > ~/\.'
  'cp .* ~/\.'
  'mv .* ~/\.'
)

for pattern in "${MANAGED_PATTERNS[@]}" "${REDIRECT_PATTERNS[@]}"; do
  if [[ "$FIRST_LINE" =~ $pattern ]]; then
    echo "BLOCKED: Direct edit of deployed dotfile detected."
    echo "This project enforces chezmoi source-first workflow."
    echo ""
    echo "Instead of editing the deployed file directly, use:"
    echo "  chezmoi edit <filepath>     # Edit in source with your \$EDITOR"
    echo "  chezmoi add <filepath>      # Add/update file in source"
    echo "  chezmoi cd                  # Navigate to source directory"
    echo ""
    echo "See the chezmoi-workflows skill for detailed guidance."
    exit 1
  fi
done

exit 0
