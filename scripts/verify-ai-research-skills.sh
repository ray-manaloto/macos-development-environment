#!/usr/bin/env bash
set -euo pipefail

MARKETPLACE_NAME="${MDE_AI_RESEARCH_MARKETPLACE_NAME:-ai-research-skills}"

CLAUDE_MARKETPLACE_FILE="${MDE_CLAUDE_MARKETPLACE_FILE:-$HOME/.claude/plugins/known_marketplaces.json}"
CLAUDE_PLUGINS_FILE="${MDE_CLAUDE_PLUGINS_FILE:-$HOME/.claude/plugins/installed_plugins.json}"

PLUGINS=(
  model-architecture
  tokenization
  fine-tuning
  mechanistic-interpretability
  data-processing
  post-training
  safety-alignment
  distributed-training
  infrastructure
  optimization
  evaluation
  inference-serving
  mlops
  agents
  rag
  prompt-engineering
  observability
  multimodal
  emerging-techniques
)

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

json_has_key() {
  local file="$1"
  local key="$2"

  if [[ ! -f "$file" ]]; then
    return 1
  fi

  if have_cmd python3; then
    python3 - "$file" "$key" <<'PY'
import json
import sys

path, key = sys.argv[1:3]
try:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
except Exception:
    sys.exit(1)

if isinstance(data, dict) and key in data:
    sys.exit(0)

sys.exit(1)
PY
    return $?
  fi

  if have_cmd rg; then
    rg -q "\"${key}\"" "$file"
    return $?
  fi

  grep -q "\"${key}\"" "$file"
}

json_plugins_has_key() {
  local file="$1"
  local key="$2"

  if [[ ! -f "$file" ]]; then
    return 1
  fi

  if have_cmd python3; then
    python3 - "$file" "$key" <<'PY'
import json
import sys

path, key = sys.argv[1:3]
try:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
except Exception:
    sys.exit(1)

plugins = data.get("plugins", {}) if isinstance(data, dict) else {}
sys.exit(0 if key in plugins else 1)
PY
    return $?
  fi

  if have_cmd rg; then
    rg -q "\"${key}\"" "$file"
    return $?
  fi

  grep -q "\"${key}\"" "$file"
}

marketplace_installed() {
  json_has_key "$CLAUDE_MARKETPLACE_FILE" "$MARKETPLACE_NAME"
}

plugin_installed() {
  local plugin="$1"
  json_plugins_has_key "$CLAUDE_PLUGINS_FILE" "${plugin}@${MARKETPLACE_NAME}"
}

main() {
  setup_path
  local failures=0

  if [[ ! -f "$CLAUDE_MARKETPLACE_FILE" ]]; then
    log "missing marketplace registry: $CLAUDE_MARKETPLACE_FILE"
    failures=1
  elif marketplace_installed; then
    log "ok: marketplace ${MARKETPLACE_NAME}"
  else
    log "missing marketplace ${MARKETPLACE_NAME}"
    failures=1
  fi

  if [[ ! -f "$CLAUDE_PLUGINS_FILE" ]]; then
    log "missing plugin registry: $CLAUDE_PLUGINS_FILE"
    failures=1
  else
    for plugin in "${PLUGINS[@]}"; do
      if plugin_installed "$plugin"; then
        log "ok: plugin ${plugin}@${MARKETPLACE_NAME}"
      else
        log "missing plugin: ${plugin}@${MARKETPLACE_NAME}"
        failures=1
      fi
    done
  fi

  if [[ "$failures" -ne 0 ]]; then
    log "AI research skills verification FAILED."
    exit 1
  fi

  log "AI research skills verification PASSED."
}

main "$@"
