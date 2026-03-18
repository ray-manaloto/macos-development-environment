#!/usr/bin/env bash
# Test: Declarative-first tool management (mise config as single source of truth)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0
fail=0

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "PASS: $label"; pass=$((pass + 1))
  else
    echo "FAIL: $label"; fail=$((fail + 1))
  fi
}

check_not() {
  local label="$1"; shift
  if ! "$@" >/dev/null 2>&1; then
    echo "PASS: $label"; pass=$((pass + 1))
  else
    echo "FAIL: $label"; fail=$((fail + 1))
  fi
}

# 1. No ~/package.json (bun hoisting guard)
check_not "no ~/package.json (bun hoisting guard)" test -f "$HOME/package.json"
check_not "no ~/node_modules (bun hoisting guard)" test -d "$HOME/node_modules"

# 2. No deprecated ubi: backend in mise config
MISE_CONFIG="${HOME}/.config/mise/config.toml"
if [[ -f "$MISE_CONFIG" ]]; then
  # Only check [tools] section entries, not task run strings
  check_not "no deprecated ubi: backend in mise config" grep -qE '^"ubi:' "$MISE_CONFIG"
fi

# 3. GIT_TERMINAL_PROMPT=0 in install scripts
for script in "$REPO_ROOT/scripts/install-langchain-cli-tools.sh" \
              "$REPO_ROOT/scripts/install-agent-stack.sh"; do
  if [[ -f "$script" ]]; then
    check "GIT_TERMINAL_PROMPT=0 in $(basename "$script")" grep -q 'GIT_TERMINAL_PROMPT=0' "$script"
  fi
done

# 4. Install scripts are slim (under 200 lines each)
for script in "$REPO_ROOT/scripts/install-langchain-cli-tools.sh" \
              "$REPO_ROOT/scripts/install-agent-stack.sh"; do
  if [[ -f "$script" ]]; then
    line_count=$(wc -l < "$script" | tr -d ' ')
    check "$(basename "$script") under 200 lines (got $line_count)" test "$line_count" -lt 200
  fi
done

# 5. No update_agent_tools in maintenance script
check_not "no update_agent_tools in maintenance script" \
  grep -q 'update_agent_tools' "$REPO_ROOT/scripts/macos-dev-maintenance.sh"

# 6. glow not in Brewfile (managed by mise)
if [[ -f "$REPO_ROOT/Brewfile" ]]; then
  check_not "glow not in Brewfile (managed by mise)" grep -q '^brew "glow"' "$REPO_ROOT/Brewfile"
fi

# 7. chezmoi mise config template exists
check "chezmoi mise config template exists" \
  test -f "$REPO_ROOT/.chezmoisource/dot_config/mise/config.toml.tmpl"

# 8. No MDE_UPDATE_AGENT_TOOLS in maintenance script
check_not "no MDE_UPDATE_AGENT_TOOLS var in maintenance" \
  grep -q 'MDE_UPDATE_AGENT_TOOLS' "$REPO_ROOT/scripts/macos-dev-maintenance.sh"

echo ""
echo "Results: $pass passed, $fail failed"
exit "$fail"
