#!/usr/bin/env bash
set -euo pipefail

PIXI_ENV="${PIXI_ENV:-agent-stack}"
INCLUDE_OPTIONAL="${INCLUDE_OPTIONAL:-1}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required command: $1" >&2
    return 1
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
  mise install -q python@latest node@latest bun@latest uv@latest pixi@latest
  mise use -g python@latest node@latest bun@latest uv@latest pixi@latest
  mise reshim
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
    uv tool install --upgrade "$pkg"
    return 0
  fi

  if command -v pip >/dev/null 2>&1; then
    pip install --upgrade "$pkg"
    return 0
  fi

  return 1
}

install_node_tool() {
  local pkg="$1"
  bun add -g "${pkg}@latest"
}

ensure_mise
ensure_runtimes

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
  "opencode"
  "openwork"
  "create-agent-chat-app"
  "@modelcontextprotocol/inspector"
)

python_failures=()
node_failures=()

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

if (( ${#python_failures[@]} > 0 || ${#node_failures[@]} > 0 )); then
  echo "Install completed with failures:" >&2
  if (( ${#python_failures[@]} > 0 )); then
    echo "  Python: ${python_failures[*]}" >&2
  fi
  if (( ${#node_failures[@]} > 0 )); then
    echo "  Node: ${node_failures[*]}" >&2
  fi
  exit 1
fi

printf "\nAgent stack installed/updated.\n"
