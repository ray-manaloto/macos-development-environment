#!/usr/bin/env bash
# guard-install.sh — Intercept global install commands that bypass mise
#
# Checks if a Bash tool use contains a direct global installer command
# (brew install, npm -g, pipx install, etc.) and blocks it with a
# suggestion to use mise instead.
#
# Reads TOOL_INPUT_COMMAND from environment (never as a shell argument,
# to prevent injection via shell metacharacters).

set -euo pipefail

# Read from environment — safe from shell injection
COMMAND="${TOOL_INPUT_COMMAND:-}"

# Skip empty commands
[[ -z "$COMMAND" ]] && exit 0

# Use first line only to prevent multi-line bypass
FIRST_LINE="${COMMAND%%$'\n'*}"

# Patterns that indicate bypassing mise for tool installation
# Uses bash regex matching with word boundaries
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

# Patterns that are exceptions (allowed through)
PIP_ALLOW_PATTERNS=(
  '\bpip install -e\b'
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$FIRST_LINE" | grep -qiE "$pattern"; then
    # Check pip-specific exceptions only for pip-related blocked patterns
    if echo "$pattern" | grep -qi "pip"; then
      for allow in "${PIP_ALLOW_PATTERNS[@]}"; do
        if echo "$FIRST_LINE" | grep -qiE "$allow"; then
          exit 0
        fi
      done
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
if echo "$FIRST_LINE" | grep -qiE '\bdirenv (allow|hook|exec)\b'; then
  echo "WARNING: direnv activation detected. This project uses mise for environment management."
  echo "Using both direnv and mise causes PATH conflicts."
  echo "See mise-enforcement skill for migration guidance."
  exit 1
fi

exit 0
