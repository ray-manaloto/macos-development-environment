#!/usr/bin/env bash
set -euo pipefail

export UV_NO_MANAGED_PYTHON="${UV_NO_MANAGED_PYTHON:-1}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$HOME/Library/Caches/uv}"
mkdir -p "$UV_CACHE_DIR" 2>/dev/null || true
export GOBIN="${GOBIN:-$HOME/.local/bin}"
mkdir -p "$GOBIN" 2>/dev/null || true

export PYO3_USE_ABI3_FORWARD_COMPATIBILITY="${PYO3_USE_ABI3_FORWARD_COMPATIBILITY:-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PIXI_ENV="${PIXI_ENV:-agent-stack}"
INCLUDE_OPTIONAL="${INCLUDE_OPTIONAL:-1}"

TOOL_PYTHON_VERSION="${TOOL_PYTHON_VERSION:-3.12}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required command: $1" >&2
    return 1
  fi
}


cleanup_claude_cli() {
  local cleanup="$SCRIPT_DIR/cleanup-claude-cli.sh"
  if [[ -x "$cleanup" ]]; then
    "$cleanup" >/dev/null 2>&1 || true
    return 0
  fi

  local bun_claude="$HOME/.bun/bin/claude"
  if [[ -e "$bun_claude" ]]; then
    rm -f "$bun_claude" || true
  fi
}

cleanup_gemini_cli() {
  local cleanup="$SCRIPT_DIR/cleanup-gemini-cli.sh"
  if [[ -x "$cleanup" ]]; then
    "$cleanup" >/dev/null 2>&1 || true
    return 0
  fi

  local bun_gemini="$HOME/.bun/bin/gemini"
  if [[ -e "$bun_gemini" ]]; then
    rm -f "$bun_gemini" || true
  fi
}

ensure_mise() {
  require_cmd mise || {
    echo "mise is required. Install with: curl https://mise.run | sh" >&2
    exit 1
  }
  eval "$(mise activate bash)"
}

ensure_runtimes() {
  mise install -q python@latest python@${TOOL_PYTHON_VERSION} node@latest bun@latest go@latest
  mise use -g python@latest node@latest bun@latest go@latest
  mise reshim
}

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    uv self update >/dev/null 2>&1 || true
    return 0
  fi
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    return 0
  fi
  return 1
}

ensure_pixi() {
  if command -v pixi >/dev/null 2>&1; then
    pixi self-update >/dev/null 2>&1 || true
    return 0
  fi
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL https://pixi.sh/install.sh | bash
    return 0
  fi
  return 1
}

tool_python_path() {
  if command -v mise >/dev/null 2>&1; then
    local base=""
    base="$(mise where python@${TOOL_PYTHON_VERSION} 2>/dev/null || true)"
    if [[ -n "$base" && -x "$base/bin/python3" ]]; then
      printf '%s' "$base/bin/python3"
      return 0
    fi
  fi
  return 1
}


install_python_tool() {
  local pkg="$1"

  if command -v pixi >/dev/null 2>&1; then
    if PIXI_NO_PROGRESS=1 pixi global install -e "$PIXI_ENV" \
      --pinning-strategy no-pin "$pkg" >/dev/null 2>&1; then
      return 0
    fi
  fi

  if command -v uv >/dev/null 2>&1; then
    local uv_python=""
    uv_python="$(tool_python_path || true)"
    if [[ -n "$uv_python" ]]; then
      if UV_PYTHON="$uv_python" uv tool install --upgrade "$pkg"; then
        return 0
      fi
    else
      if uv tool install --upgrade "$pkg"; then
        return 0
      fi
    fi
  fi

  if command -v pip >/dev/null 2>&1; then
    pip install --upgrade "$pkg"
    return 0
  fi

  return 1
}

install_node_tool() {
  local pkg="$1"
  shift

  if bun add -g "${pkg}@latest"; then
    return 0
  fi

  for fallback in "$@"; do
    if bun add -g "${fallback}@latest"; then
      return 0
    fi
  done

  return 1
}


load_keychain_secret() {
  local label="$1"
  if command -v security >/dev/null 2>&1; then
    security find-generic-password -s "$label" -w 2>/dev/null || true
  fi
}

set_env_line() {
  local env_file="$1"
  local key="$2"
  local value="$3"
  local overwrite="$4"
  local tmp=""

  if [[ -z "$value" ]]; then
    return 1
  fi

  if [[ "$overwrite" == "1" ]]; then
    tmp="$(mktemp)"
    if [[ -f "$env_file" ]]; then
      grep -v "^${key}=" "$env_file" > "$tmp" || true
    fi
    printf '%s=%s\n' "$key" "$value" >> "$tmp"
    mv "$tmp" "$env_file"
    chmod 600 "$env_file" 2>/dev/null || true
    return 0
  fi

  if grep -q "^${key}=" "$env_file" 2>/dev/null; then
    return 1
  fi

  printf '%s=%s\n' "$key" "$value" >> "$env_file"
  chmod 600 "$env_file" 2>/dev/null || true
  return 0
}

configure_fabric_env() {
  local setup="${MDE_FABRIC_SETUP:-1}"
  local overwrite="${MDE_FABRIC_OVERWRITE:-0}"
  local profile="${MDE_FABRIC_PROFILE:-anthropic}"
  local config_dir="${MDE_FABRIC_CONFIG_DIR:-$HOME/.config/fabric}"
  local env_file="${MDE_FABRIC_ENV_FILE:-}"
  local env_dir=""
  local wrote=0

  if [[ "$setup" != "1" ]]; then
    return 0
  fi

  if [[ -z "$env_file" ]]; then
    case "$profile" in
      ""|default|main|base)
        env_file="$config_dir/.env"
        ;;
      *)
        env_file="$config_dir/.env.$profile"
        ;;
    esac
  fi

  env_dir="$(dirname "$env_file")"
  mkdir -p "$env_dir" 2>/dev/null || true

  if [[ -e "$config_dir/.env" && ! -L "$config_dir/.env" && "$env_file" != "$config_dir/.env" ]]; then
    mv "$config_dir/.env" "$config_dir/.env.all" 2>/dev/null || true
  fi

  if [[ "$env_file" != "$config_dir/.env" ]]; then
    ln -sfn "$env_file" "$config_dir/.env"
  fi

  if [[ ! -f "$env_file" ]]; then
    : > "$env_file"
    chmod 600 "$env_file" 2>/dev/null || true
  fi

  local keys=()
  local value=""
  case "$profile" in
    anthropic)
      keys=(ANTHROPIC_API_KEY ANTHROPIC_USE_OAUTH_LOGIN)
      ;;
    gemini)
      keys=(GEMINI_API_KEY)
      ;;
    openai)
      keys=(OPENAI_API_KEY)
      ;;
    all|full)
      keys=(OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY OPENROUTER_API_KEY GROQ_API_KEY MISTRAL_API_KEY DEEPSEEK_API_KEY SILICON_API_KEY GROKAI_API_KEY LM_STUDIO_API_BASE_URL OLLAMA_URL ANTHROPIC_USE_OAUTH_LOGIN)
      ;;
    *)
      keys=(ANTHROPIC_API_KEY)
      ;;
  esac

  for key in "${keys[@]}"; do
    value="${!key:-}"
    if [[ -z "$value" ]]; then
      case "$key" in
        OPENAI_API_KEY)
          value="$(load_keychain_secret mde-openai-api-key)"
          ;;
        ANTHROPIC_API_KEY)
          value="$(load_keychain_secret mde-anthropic-api-key)"
          ;;
        GEMINI_API_KEY)
          value="$(load_keychain_secret mde-gemini-api-key)"
          ;;
      esac
    fi
    if set_env_line "$env_file" "$key" "$value" "$overwrite"; then
      wrote=1
    fi
  done

  local default_vendor="${MDE_FABRIC_DEFAULT_VENDOR:-}"
  local default_model="${MDE_FABRIC_DEFAULT_MODEL:-}"
  local default_context="${MDE_FABRIC_DEFAULT_MODEL_CONTEXT_LENGTH:-}"

  if set_env_line "$env_file" "DEFAULT_VENDOR" "$default_vendor" "$overwrite"; then
    wrote=1
  fi
  if set_env_line "$env_file" "DEFAULT_MODEL" "$default_model" "$overwrite"; then
    wrote=1
  fi
  if set_env_line "$env_file" "DEFAULT_MODEL_CONTEXT_LENGTH" "$default_context" "$overwrite"; then
    wrote=1
  fi

  if [[ "$wrote" == "1" ]]; then
    echo "[fabric] updated config at $env_file"
  fi
}

install_fabric() {
  if ! command -v curl >/dev/null 2>&1; then
    echo "missing curl for fabric install" >&2
    return 1
  fi
  local bin_dir="${MDE_FABRIC_BIN_DIR:-$HOME/.local/share/mde/bin}"
  local legacy_bin="$HOME/.local/bin/fabric"

  mkdir -p "$bin_dir" 2>/dev/null || true

  if [[ -f "$legacy_bin" && ! -L "$legacy_bin" ]]; then
    if ! grep -q "Managed by macos-development-environment" "$legacy_bin" 2>/dev/null; then
      if [[ ! -f "$bin_dir/fabric" ]]; then
        mv "$legacy_bin" "$bin_dir/fabric" 2>/dev/null || true
      fi
    fi
  fi

  curl -fsSL https://raw.githubusercontent.com/danielmiessler/fabric/main/scripts/installer/install.sh |     INSTALL_DIR="$bin_dir" bash
}

ensure_mise
ensure_runtimes
ensure_uv
ensure_pixi

PYTHON_TOOLS=(
  "langchain-cli"
  "langgraph-cli"
  "langsmith-fetch"
  "skypilot[aws]"
  "aider-chat"
  "open-interpreter"
  "crewai"
)

NODE_TOOLS=(
  "@anthropic-ai/claude-code"
  "@openai/codex"
  "@google/gemini-cli"
  "openwork"
  "create-agent-chat-app"
  "@modelcontextprotocol/inspector"
)

GO_TOOLS=(
  "github.com/opencode-ai/opencode@latest"
)

python_failures=()
node_failures=()
go_failures=()

for pkg in "${PYTHON_TOOLS[@]}"; do
  echo "[python] installing ${pkg}"
  if ! install_python_tool "$pkg"; then
    python_failures+=("$pkg")
  fi
done

for pkg in "${NODE_TOOLS[@]}"; do
  echo "[node] installing ${pkg}"
  if ! install_node_tool "$pkg"; then
    node_failures+=("$pkg")
  fi
done

cleanup_claude_cli
cleanup_gemini_cli

for pkg in "${GO_TOOLS[@]}"; do
  echo "[go] installing ${pkg}"
  if command -v go >/dev/null 2>&1; then
    if ! go install "${pkg}"; then
      go_failures+=("$pkg")
    fi
  else
    go_failures+=("$pkg")
  fi
done

if [[ "$INCLUDE_OPTIONAL" == "1" ]]; then
  if command -v gh >/dev/null 2>&1; then
    gh extension install github/gh-copilot >/dev/null 2>&1 || \
      gh extension upgrade github/gh-copilot >/dev/null 2>&1 || true
  fi
  if install_fabric; then
    configure_fabric_env || true
  fi
fi

if command -v pixi >/dev/null 2>&1; then
  pixi global update -e "$PIXI_ENV" >/dev/null 2>&1 || true
fi

mise reshim

if (( ${#python_failures[@]} > 0 || ${#node_failures[@]} > 0 || ${#go_failures[@]} > 0 )); then
  echo "Install completed with failures:" >&2
  if (( ${#python_failures[@]} > 0 )); then
    echo "  Python: ${python_failures[*]}" >&2
  fi
  if (( ${#node_failures[@]} > 0 )); then
    echo "  Node: ${node_failures[*]}" >&2
  fi
  if (( ${#go_failures[@]} > 0 )); then
    echo "  Go: ${go_failures[*]}" >&2
  fi
  exit 1
fi

printf "\nAgent stack installed/updated.\n"
