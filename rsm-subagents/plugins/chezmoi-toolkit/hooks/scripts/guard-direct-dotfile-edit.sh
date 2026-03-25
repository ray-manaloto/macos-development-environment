#!/usr/bin/env bash
# guard-direct-dotfile-edit.sh — Block direct edits to chezmoi-managed dotfiles
#
# Enforces the source-first workflow: edits must go through chezmoi source,
# not by directly modifying deployed files in ~/.
#
# Called by PreToolUse:Bash hook with the command as $1.

set -euo pipefail

COMMAND="${1:-}"

# Skip empty commands
[[ -z "$COMMAND" ]] && exit 0

# Patterns that indicate direct editing of deployed dotfiles
# These are files commonly managed by chezmoi
MANAGED_PATTERNS=(
  'vim ~/\.'
  'nvim ~/\.'
  'nano ~/\.'
  'hx ~/\.'
  'code ~/\.'
  'echo.*>>.*~/\.'
  'cat.*>.*~/\.'
  'sed -i.*~/\.'
  'perl -pi.*~/\.'
  'tee ~/\.'
  'cp .* ~/\.'
  'mv .* ~/\.'
)

for pattern in "${MANAGED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    # Allow if the command itself IS a chezmoi command (not just mentions it in a string)
    if echo "$COMMAND" | grep -qE '^(chezmoi (edit|cd|add|source-path)|.*\.local/share/chezmoi)'; then
      exit 0
    fi

    # Allow if editing non-dotfile paths under ~/
    # (the pattern already requires ~/\. so this catches dotfiles only)

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
