#!/usr/bin/env bash
set -euo pipefail

export UV_NO_MANAGED_PYTHON="${UV_NO_MANAGED_PYTHON:-1}"

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

ensure_mise
ensure_runtimes
ensure_uv
ensure_pixi

PYTHON_TOOLS=(
  "langchain-cli"
  "langgraph-cli"
  "langsmith-fetch"
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
  if command -v go >/dev/null 2>&1; then
    go install github.com/danielmiessler/fabric@latest || true
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
