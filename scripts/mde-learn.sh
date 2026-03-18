#!/usr/bin/env bash
# mde-learn.sh — Learning lifecycle wrapper for claude-flow memory and neural patterns.
# Uses mise-managed claude-flow CLI (not npx).
set -euo pipefail

export GIT_TERMINAL_PROMPT=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SWARM_DIR="$REPO_ROOT/.swarm"
MEMORY_DB="$SWARM_DIR/memory.db"
CF_TIMEOUT="${MDE_LEARN_TIMEOUT:-45}"

CF="claude-flow"
if ! command -v "$CF" >/dev/null 2>&1; then
  CF="npx @claude-flow/cli@latest"
fi

# Portable timeout: prefer gtimeout (brew coreutils), fall back to perl
run_with_timeout() {
  local secs="$1"; shift
  if command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$secs" "$@"
    return
  fi
  if command -v timeout >/dev/null 2>&1; then
    timeout "$secs" "$@"
    return
  fi
  # perl fallback for macOS without coreutils
  perl -e "
    alarm $secs;
    \$SIG{ALRM} = sub { kill 'TERM', \$pid; exit 124 };
    \$pid = fork // die;
    if (\$pid == 0) { exec @ARGV; die \"exec: \$!\" }
    waitpid(\$pid, 0);
    exit (\$? >> 8);
  " "$@"
}

cf_run() {
  run_with_timeout "$CF_TIMEOUT" $CF "$@" </dev/null
}

ensure_db() {
  if [[ ! -f "$MEMORY_DB" ]]; then
    mkdir -p "$SWARM_DIR"
    cf_run memory init --force 2>/dev/null || true
  fi
}

cmd_init() {
  mkdir -p "$SWARM_DIR"
  cf_run memory init --force || true
  if [[ -f "$MEMORY_DB" ]]; then
    echo "Learning DB ready: $MEMORY_DB"
  else
    echo "Learning DB initialized (path may vary by claude-flow version)"
  fi
}

cmd_search() {
  local query="${1:?Usage: mde-learn.sh search <query>}"
  ensure_db
  cf_run memory search --query "$query" --namespace patterns 2>/dev/null || true
}

cmd_store() {
  local key="${1:?Usage: mde-learn.sh store <key> <value>}"
  local value="${2:?Usage: mde-learn.sh store <key> <value>}"
  ensure_db
  local out
  out="$(cf_run memory store --key "$key" --value "$value" --namespace patterns 2>&1)" || true
  echo "$out"
  if echo "$out" | grep -q "stored successfully\|Data stored"; then
    return 0
  fi
  # If output contains the key, treat as success even without explicit message
  if echo "$out" | grep -q "$key"; then
    return 0
  fi
  return 1
}

cmd_consolidate() {
  ensure_db
  echo "Consolidating memory..."
  cf_run memory list --namespace patterns --limit 1 2>/dev/null || true
  echo "Running neural optimize..."
  cf_run neural optimize 2>/dev/null || true
  echo "Consolidation complete."
}

cmd_status() {
  ensure_db
  echo "=== Learning Status ==="
  echo "--- Memory Stats ---"
  cf_run memory stats 2>/dev/null || cf_run memory list --namespace patterns --limit 5 2>/dev/null || echo "(no stats available)"
  echo ""
  echo "--- Neural Status ---"
  cf_run neural status 2>/dev/null || echo "(neural system not initialized)"
}

case "${1:-}" in
  init)        cmd_init ;;
  search)      shift; cmd_search "$@" ;;
  store)       shift; cmd_store "$@" ;;
  consolidate) cmd_consolidate ;;
  status)      cmd_status ;;
  *)
    echo "Usage: mde-learn.sh <init|search|store|consolidate|status>" >&2
    echo "" >&2
    echo "Subcommands:" >&2
    echo "  init          Initialize learning memory DB" >&2
    echo "  search <q>    Search memory for patterns" >&2
    echo "  store <k> <v> Store a pattern (namespace=patterns)" >&2
    echo "  consolidate   Run memory consolidation + neural optimize" >&2
    echo "  status        Show learning stats" >&2
    exit 1
    ;;
esac
