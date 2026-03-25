#!/usr/bin/env bash
# guard-install.sh — Intercept global install commands that bypass mise
#
# Checks if a Bash tool use contains a direct global installer command
# (brew install, npm -g, pipx install, etc.) and blocks it with a
# suggestion to use mise instead.
#
# Called by PreToolUse:Bash hook with the command as $1.

set -euo pipefail

COMMAND="${1:-}"

# Skip empty commands
[[ -z "$COMMAND" ]] && exit 0

# Patterns that indicate bypassing mise for tool installation
# Patterns that indicate bypassing mise for tool installation
# Uses word-boundary matching (-E with \b) to avoid false positives
BLOCKED_PATTERNS=(
  '\bbrew install\b'
  '\bnpm install -g\b'
  '\bnpm i -g\b'
  '\bbun add -g\b'
  '\bbun install -g\b'
  '\bpipx install\b'
  '\bcargo install\b'
  '\bgo install\b'
  '\bpip install --user\b'
  '\bgem install\b'
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    # Allow editable local packages (pip install -e .)
    if echo "$COMMAND" | grep -qiE '\bpip install -e\b'; then
      exit 0
    fi

    echo "BLOCKED: Direct global install detected."
    echo "This project uses mise as the tool authority."
    echo "Check if the tool is in the mise registry: mise registry | grep <tool>"
    echo "Then add it to mise config: mise use -g <backend>:<tool>"
    echo "See the mise-tool-management skill for backend selection guidance."
    exit 1
  fi
done

# Block direnv activation commands (allow references in comments/docs)
if echo "$COMMAND" | grep -qiE '\bdirenv (allow|hook|exec)\b'; then
  echo "WARNING: direnv activation detected. This project uses mise for environment management."
  echo "Using both direnv and mise causes PATH conflicts."
  echo "See mise-enforcement skill for migration guidance."
  exit 1
fi

exit 0
