#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MARKETPLACE_REPO="${MDE_AI_RESEARCH_MARKETPLACE_REPO:-zechenzhangAGI/AI-research-SKILLs}"
MARKETPLACE_NAME="${MDE_AI_RESEARCH_MARKETPLACE_NAME:-ai-research-skills}"

CLAUDE_MARKETPLACE_FILE="${MDE_CLAUDE_MARKETPLACE_FILE:-$HOME/.claude/plugins/known_marketplaces.json}"
CLAUDE_PLUGINS_FILE="${MDE_CLAUDE_PLUGINS_FILE:-$HOME/.claude/plugins/installed_plugins.json}"

FORCE_INSTALL="${MDE_AI_RESEARCH_FORCE:-0}"

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

load_keychain_secret() {
  local label="$1"
  local env_var="$2"
  local value=""

  if [[ -n "${!env_var:-}" || ! $(command -v security 2>/dev/null) ]]; then
    return 0
  fi

  value="$(security find-generic-password -s "$label" -w 2>/dev/null || true)"
  if [[ -n "$value" ]]; then
    printf -v "$env_var" '%s' "$value"
    export "$env_var"
  fi
}

load_op_secret() {
  local ref_var="$1"
  local env_var="$2"
  local ref=""
  local token=""
  local value=""

  ref="${!ref_var:-}"
  if [[ -z "$ref" || -n "${!env_var:-}" ]]; then
    return 0
  fi

  if [[ -n "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]]; then
    token="$OP_SERVICE_ACCOUNT_TOKEN"
  elif have_cmd security; then
    token="$(security find-generic-password -s mde-op-sa -w 2>/dev/null || true)"
  fi

  if [[ -z "$token" || ! $(command -v op 2>/dev/null) ]]; then
    return 0
  fi

  export OP_SERVICE_ACCOUNT_TOKEN="$token"
  value="$(op read "$ref" 2>/dev/null || true)"
  if [[ -n "$value" ]]; then
    printf -v "$env_var" '%s' "$value"
    export "$env_var"
  fi
}

ensure_node() {
  if have_cmd node; then
    return 0
  fi

  if have_cmd mise; then
    log "node not found; installing via mise."
    mise install -q node@latest
    mise use -g node@latest
    mise reshim
    return 0
  fi

  log "missing node runtime and mise is unavailable."
  return 1
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

run_claude() {
  local cmd="$1"
  local -a flags=()

  if [[ -n "${MDE_CLAUDE_PRINT_FLAGS:-}" ]]; then
    read -r -a flags <<< "${MDE_CLAUDE_PRINT_FLAGS}"
  fi

  claude --print "${flags[@]}" "$cmd"
}

main() {
  setup_path

  if ! have_cmd claude; then
    log "missing command: claude"
    exit 1
  fi

  ensure_node

  load_op_secret MDE_OP_ANTHROPIC_API_KEY_REF ANTHROPIC_API_KEY
  load_keychain_secret "mde-anthropic-api-key" ANTHROPIC_API_KEY

  if ! marketplace_installed; then
    log "Adding marketplace ${MARKETPLACE_REPO}."
    run_claude "/plugin marketplace add ${MARKETPLACE_REPO}"
  else
    log "ok: marketplace ${MARKETPLACE_NAME}"
  fi

  log "Updating marketplace ${MARKETPLACE_NAME}."
  run_claude "/plugin marketplace update ${MARKETPLACE_NAME}"

  local failures=0
  for plugin in "${PLUGINS[@]}"; do
    if [[ "$FORCE_INSTALL" != "1" ]] && plugin_installed "$plugin"; then
      log "ok: plugin ${plugin}@${MARKETPLACE_NAME}"
      continue
    fi
    log "Installing plugin ${plugin}@${MARKETPLACE_NAME}."
    if ! run_claude "/plugin install ${plugin}@${MARKETPLACE_NAME}"; then
      log "failed: plugin ${plugin}@${MARKETPLACE_NAME}"
      failures=1
    fi
  done

  if [[ -x "$SCRIPT_DIR/verify-ai-research-skills.sh" ]]; then
    log "Validating AI research skills."
    if ! "$SCRIPT_DIR/verify-ai-research-skills.sh"; then
      failures=1
    fi
  fi

  if [[ "$failures" -ne 0 ]]; then
    log "AI research skills install FAILED."
    exit 1
  fi

  log "AI research skills install PASSED."
}

main "$@"
