#!/usr/bin/env bash
set -euo pipefail

export UV_NO_MANAGED_PYTHON="${UV_NO_MANAGED_PYTHON:-1}"

export PYO3_USE_ABI3_FORWARD_COMPATIBILITY="${PYO3_USE_ABI3_FORWARD_COMPATIBILITY:-1}"

PIXI_ENV="${PIXI_ENV:-langchain-cli-tools}"
INCLUDE_INTERNAL="${INCLUDE_INTERNAL:-1}"

TOOL_PYTHON_VERSION="${TOOL_PYTHON_VERSION:-3.12}"
UV_TOOL_FORCE="${UV_TOOL_FORCE:-1}"
UV_TOOL_TIMEOUT_SECONDS="${UV_TOOL_TIMEOUT_SECONDS:-600}"
DOCS_MONOREPO_SUBMODULES="${DOCS_MONOREPO_SUBMODULES:-1}"
DOCS_MONOREPO_DEPTH="${DOCS_MONOREPO_DEPTH:-1}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required command: $1" >&2
    return 1
  fi
}

tool_python_path() {
  local version="${1:-$TOOL_PYTHON_VERSION}"
  if command -v mise >/dev/null 2>&1; then
    local base=""
    base="$(mise where python@${version} 2>/dev/null || true)"
    if [[ -z "$base" ]]; then
      mise install -q python@${version} >/dev/null 2>&1 || true
      base="$(mise where python@${version} 2>/dev/null || true)"
    fi
    if [[ -n "$base" && -x "$base/bin/python3" ]]; then
      printf '%s' "$base/bin/python3"
      return 0
    fi
  fi
  return 1
}

ensure_tool_python() {
  if command -v mise >/dev/null 2>&1; then
    tool_python_path "$TOOL_PYTHON_VERSION" >/dev/null 2>&1 || true
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

uv_tool_present() {
  local name="$1"
  if command -v rg >/dev/null 2>&1; then
    uv tool list 2>/dev/null | rg -q "^${name} "
    return $?
  fi
  uv tool list 2>/dev/null | grep -E "^${name} " >/dev/null 2>&1
}

run_with_timeout() {
  local timeout="$1"
  shift

  if [[ -z "$timeout" || "$timeout" == "0" ]]; then
    "$@"
    return $?
  fi

  if command -v python3 >/dev/null 2>&1; then
    python3 - "$timeout" "$@" <<'PY'
import subprocess
import sys

try:
    timeout = int(sys.argv[1])
except ValueError:
    timeout = 0
cmd = sys.argv[2:]
try:
    subprocess.run(cmd, check=True, timeout=timeout or None)
except subprocess.TimeoutExpired:
    print(f"timed out after {timeout}s", file=sys.stderr)
    sys.exit(124)
except subprocess.CalledProcessError as exc:
    sys.exit(exc.returncode)
PY
  else
    "$@"
  fi
}

install_with_uv() {
  local name="$1"
  local pkg="$2"
  local python_version="$3"
  shift 3
  local extra_args=("$@")
  local uv_python=""
  local timeout="0"

  if [[ "$name" == "docs-monorepo" && "$UV_TOOL_TIMEOUT_SECONDS" != "0" ]]; then
    timeout="$UV_TOOL_TIMEOUT_SECONDS"
  fi

  uv_python="$(tool_python_path "$python_version" || true)"
  if [[ -n "$uv_python" ]]; then
    if run_with_timeout "$timeout" env UV_PYTHON="$uv_python" uv tool install --upgrade "${extra_args[@]}" "$pkg"; then
      return 0
    fi
    return 1
  fi
  run_with_timeout "$timeout" uv tool install --upgrade "${extra_args[@]}" "$pkg"
}

install_with_uv_git() {
  local name="$1"
  local repo="$2"
  local subdir="$3"
  local python_version="$4"
  shift 4
  local extra_args=("$@")
  local url="git+https://github.com/${repo}.git"
  local uv_python=""
  local timeout="0"

  if [[ "$name" == "docs-monorepo" && "$UV_TOOL_TIMEOUT_SECONDS" != "0" ]]; then
    timeout="$UV_TOOL_TIMEOUT_SECONDS"
  fi

  if [[ -n "$subdir" ]]; then
    url+="#subdirectory=${subdir}"
  fi
  uv_python="$(tool_python_path "$python_version" || true)"
  if [[ -n "$uv_python" ]]; then
    if run_with_timeout "$timeout" env UV_PYTHON="$uv_python" uv tool install --upgrade "${extra_args[@]}" "$url"; then
      return 0
    fi
    return 1
  fi
  run_with_timeout "$timeout" uv tool install --upgrade "${extra_args[@]}" "$url"
}

install_learning_langchain() {
  local python_version="$1"
  shift
  local extra_args=("$@")
  local tmp_dir=""
  local uv_python=""

  if ! command -v git >/dev/null 2>&1; then
    return 1
  fi

  tmp_dir="$(mktemp -d 2>/dev/null || mktemp -d -t learning-langchain)"
  if [[ -z "$tmp_dir" ]]; then
    return 1
  fi

  if ! git clone --depth 1 https://github.com/langchain-ai/learning-langchain.git "$tmp_dir" >/dev/null 2>&1; then
    rm -rf "$tmp_dir"
    return 1
  fi

  if [[ -f "$tmp_dir/pyproject.toml" ]]; then
    if command -v python3 >/dev/null 2>&1; then
      python3 - <<'PY' "$tmp_dir/pyproject.toml"
import sys
from pathlib import Path
path = Path(sys.argv[1])
text = path.read_text()
text = text.replace(
    'langgraph.cli:dev_command --config ch9/py/langgraph.json --verbose',
    'langgraph.cli:dev_command',
)
path.write_text(text)
PY
    else
      sed -i '' 's/langgraph.cli:dev_command --config ch9\/py\/langgraph.json --verbose/langgraph.cli:dev_command/' "$tmp_dir/pyproject.toml"
    fi
  fi

  uv_python="$(tool_python_path "$python_version" || true)"
  if [[ -n "$uv_python" ]]; then
    UV_PYTHON="$uv_python" uv tool install --upgrade "${extra_args[@]}" "$tmp_dir"
  else
    uv tool install --upgrade "${extra_args[@]}" "$tmp_dir"
  fi
  local status=$?
  rm -rf "$tmp_dir"
  return "$status"
}

install_docs_monorepo() {
  local python_version="$1"
  shift
  local extra_args=("$@")
  local tmp_dir=""
  local uv_python=""
  local depth="${DOCS_MONOREPO_DEPTH}"
  local clone_args=()

  if ! command -v git >/dev/null 2>&1; then
    return 1
  fi

  tmp_dir="$(mktemp -d 2>/dev/null || mktemp -d -t docs-monorepo)"
  if [[ -z "$tmp_dir" ]]; then
    return 1
  fi

  if [[ -n "$depth" && "$depth" != "0" ]]; then
    clone_args+=(--depth "$depth")
  fi
  if [[ "$DOCS_MONOREPO_SUBMODULES" == "1" ]]; then
    clone_args+=(--recurse-submodules --shallow-submodules)
  fi

  if ! env GIT_LFS_SKIP_SMUDGE=1 git clone "${clone_args[@]}" \
    https://github.com/langchain-ai/docs.git "$tmp_dir" >/dev/null 2>&1; then
    rm -rf "$tmp_dir"
    return 1
  fi

  if [[ -f "$tmp_dir/pyproject.toml" ]] && command -v python3 >/dev/null 2>&1; then
    python3 - <<'PYDOC' "$tmp_dir/pyproject.toml"
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()

replacement = """[tool.setuptools]
packages = [
  "pipeline",
  "pipeline.commands",
  "pipeline.core",
  "pipeline.preprocessors",
  "pipeline.tools",
  "pipeline.tools.notebook",
]

[tool.setuptools.package-data]
pipeline = ["tools/notebook/notebook_convert_templates/**/*"]
"""

pattern = re.compile(r"\[tool\.setuptools\]\npackages = \[\"pipeline\"\]\n", re.M)
if pattern.search(text):
    text = pattern.sub(replacement, text)
elif "[tool.setuptools]" in text and "tool.setuptools.package-data" not in text:
    text += "\n" + replacement

path.write_text(text)
PYDOC
  fi

  uv_python="$(tool_python_path "$python_version" || true)"
  if [[ -n "$uv_python" ]]; then
    run_with_timeout "$UV_TOOL_TIMEOUT_SECONDS" env UV_PYTHON="$uv_python" \
      uv tool install --upgrade "${extra_args[@]}" "$tmp_dir"
  else
    run_with_timeout "$UV_TOOL_TIMEOUT_SECONDS" \
      uv tool install --upgrade "${extra_args[@]}" "$tmp_dir"
  fi
  local status=$?
  rm -rf "$tmp_dir"
  return "$status"
}


install_python_tool() {
  local name="$1"
  local repo="$2"
  local subdir="$3"
  local python_version="$4"
  local uv_args=()

  if [[ "$UV_TOOL_FORCE" == "1" ]]; then
    case "$name" in
      langchain-cli|langc)
        uv_args+=(--force)
        ;;
    esac
  fi

  if install_with_pixi "$name"; then
    return 0
  fi

  if [[ "$name" == "learning-langchain" ]]; then
    if install_learning_langchain "$python_version" "${uv_args[@]}"; then
      if uv_tool_present "$name"; then
        return 0
      fi
    fi
    return 1
  fi

  if [[ "$name" == "docs-monorepo" ]]; then
    if install_docs_monorepo "$python_version" "${uv_args[@]}"; then
      if uv_tool_present "$name"; then
        return 0
      fi
    fi
    if command -v uv >/dev/null 2>&1; then
      uv tool uninstall "$name" >/dev/null 2>&1 || true
    fi
    return 1
  fi

  if install_with_uv "$name" "$name" "$python_version" "${uv_args[@]}"; then
    if uv_tool_present "$name"; then
      return 0
    fi
  fi

  if [[ -n "$repo" ]]; then
    if install_with_uv_git "$name" "$repo" "$subdir" "$python_version" "${uv_args[@]}"; then
      if uv_tool_present "$name"; then
        return 0
      fi
    fi
  fi

  return 1
}

install_node_tool() {
  local pkg="$1"
  bun add -g "${pkg}@latest"
}

require_cmd uv

ensure_tool_python
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
  "deepagents-acp|langchain-ai/deepagents|libs/acp|latest"
  "pylon-data-extractor|langchain-ai/pylon_data_extractor|"
)

PYTHON_INTERNAL_TOOLS=(
  "langc|langchain-ai/cli|"
  "docs-monorepo|langchain-ai/docs||latest"
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
  IFS='|' read -r name repo subdir python_version <<<"$entry"
  echo "[python] installing ${name}"
  if ! install_python_tool "$name" "$repo" "$subdir" "$python_version"; then
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
