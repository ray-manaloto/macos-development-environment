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
BLOCKED_PATTERNS=(
  'brew install'
  'npm install -g'
  'npm i -g'
  'bun add -g'
  'bun install -g'
  'pipx install'
  'cargo install'
  'go install'
  'pip install --user'
  'pip install -g'
  'gem install'
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qi "$pattern"; then
    # Allow if it's a known exception (e.g., pip install -e for editable local packages)
    if echo "$COMMAND" | grep -qi "pip install -e"; then
      exit 0
    fi

    echo "BLOCKED: Direct global install detected ('$pattern')."
    echo "This project uses mise as the tool authority."
    echo "Check if the tool is in the mise registry: mise registry | grep <tool>"
    echo "Then add it to mise config: mise use -g <backend>:<tool>"
    echo "See the mise-tool-management skill for backend selection guidance."
    exit 1
  fi
done

# Also warn about direnv usage when mise is active
if echo "$COMMAND" | grep -qi "direnv"; then
  echo "WARNING: direnv detected. This project uses mise for environment management."
  echo "Using both direnv and mise causes PATH conflicts."
  echo "See mise-enforcement skill for migration guidance."
  exit 1
fi

exit 0
