#!/usr/bin/env bash
set -euo pipefail

export UV_NO_MANAGED_PYTHON="${UV_NO_MANAGED_PYTHON:-1}"

PIXI_ENV="${PIXI_ENV:-langchain-cli-tools}"
INCLUDE_INTERNAL="${INCLUDE_INTERNAL:-1}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required command: $1" >&2
    return 1
  fi
}

ensure_bun() {
  if command -v bun >/dev/null 2>&1; then
    bun upgrade || true
    return 0
  fi

  if command -v mise >/dev/null 2>&1; then
    mise install -q bun@latest
    mise use -g bun@latest
    return 0
  fi

  echo "bun not found and mise is unavailable; install bun first." >&2
  return 1
}

install_with_pixi() {
  local pkg="$1"
  if ! command -v pixi >/dev/null 2>&1; then
    return 1
  fi

  PIXI_NO_PROGRESS=1 pixi global install -e "$PIXI_ENV" "$pkg" >/dev/null 2>&1
}

install_with_uv() {
  local pkg="$1"
  uv tool install --upgrade "$pkg"
}

install_with_uv_git() {
  local repo="$1"
  local subdir="$2"
  local url="git+https://github.com/${repo}.git"
  if [[ -n "$subdir" ]]; then
    url+="#subdirectory=${subdir}"
  fi
  uv tool install --upgrade "$url"
}

install_python_tool() {
  local name="$1"
  local repo="$2"
  local subdir="$3"

  if install_with_pixi "$name"; then
    return 0
  fi

  if install_with_uv "$name"; then
    return 0
  fi

  if [[ -n "$repo" ]]; then
    install_with_uv_git "$repo" "$subdir"
    return 0
  fi

  return 1
}

install_node_tool() {
  local pkg="$1"
  bun add -g "${pkg}@latest"
}

require_cmd uv

ensure_bun

PYTHON_TOOLS=(
  "langchain-cli|langchain-ai/langchain|libs/cli"
  "langchain-model-profiles|langchain-ai/langchain|libs/model-profiles"
  "langgraph-cli|langchain-ai/langgraph|libs/cli"
  "langgraph-gen|langchain-ai/langgraph-gen-py|"
  "langgraph-engineer|langchain-ai/langgraph-engineer|"
  "langsmith-fetch|langchain-ai/langsmith-fetch|"
  "langsmith-data-migration-tool|langchain-ai/langsmith-data-migration-tool|"
  "langsmith-mcp-server|langchain-ai/langsmith-mcp-server|"
  "mcpdoc|langchain-ai/mcpdoc|"
  "deepagents-cli|langchain-ai/deepagents|libs/deepagents-cli"
  "deepagents-acp|langchain-ai/deepagents|libs/acp"
  "pylon-data-extractor|langchain-ai/pylon_data_extractor|"
)

PYTHON_INTERNAL_TOOLS=(
  "langc|langchain-ai/cli|"
  "docs-monorepo|langchain-ai/docs|"
  "langchain-plugin|langchain-ai/langchain-aiplugin|"
  "learning-langchain|langchain-ai/learning-langchain|"
  "mcp-simple-streamablehttp-stateless|langchain-ai/langchain-mcp-adapters|examples/servers/streamable-http-stateless"
)

NODE_TOOLS=(
  "create-agent-chat-app"
  "create-langchain-integration"
  "create-langgraph"
  "@langchain/langgraph-checkpoint-validation"
  "@langchain/langgraph-cli"
  "@langchain/langgraph-ui"
  "deepagents-cli"
  "openwork"
)

if [[ "$INCLUDE_INTERNAL" == "1" ]]; then
  PYTHON_TOOLS+=("${PYTHON_INTERNAL_TOOLS[@]}")
fi

python_failures=()
node_failures=()

for entry in "${PYTHON_TOOLS[@]}"; do
  IFS='|' read -r name repo subdir <<<"$entry"
  echo "[python] installing ${name}"
  if ! install_python_tool "$name" "$repo" "$subdir"; then
    python_failures+=("$name")
  fi
done

for pkg in "${NODE_TOOLS[@]}"; do
  echo "[node] installing ${pkg}"
  if ! install_node_tool "$pkg"; then
    node_failures+=("$pkg")
  fi
done

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

printf "\nAll LangChain CLI tools installed/updated.\n"
