#!/usr/bin/env bash

# shellcheck source=scripts/lib/mde-platform.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/mde-platform.sh"
# shellcheck source=scripts/lib/mde-cache-policy.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/mde-cache-policy.sh"
# shellcheck source=scripts/lib/mde-telemetry.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/mde-telemetry.sh"

mde_repo_root() {
  if [[ -n "${MDE_REPO_ROOT:-}" && -d "$MDE_REPO_ROOT" ]]; then
    printf '%s\n' "$MDE_REPO_ROOT"
    return 0
  fi

  local root
  root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  printf '%s\n' "$root"
}

mde_policy_init() {
  export MDE_REPO_ROOT="$(mde_repo_root)"
  export MDE_TOOL_OWNERSHIP_FILE="${MDE_TOOL_OWNERSHIP_FILE:-$MDE_REPO_ROOT/configs/mde-tool-ownership.json}"
  export MDE_MODERNIZATION_MATRIX_FILE="${MDE_MODERNIZATION_MATRIX_FILE:-$MDE_REPO_ROOT/configs/mde-modernization-matrix.json}"
  export MDE_MISE_EXCEPTION_ALLOWLIST="${MDE_MISE_EXCEPTION_ALLOWLIST:-$MDE_REPO_ROOT/configs/mde-install-exceptions.json}"
  export MDE_SKILL_REGISTRY_FILE="${MDE_SKILL_REGISTRY_FILE:-$MDE_REPO_ROOT/configs/mde-skill-registry.json}"
  export MDE_DOMAIN_CATALOG_FILE="${MDE_DOMAIN_CATALOG_FILE:-$MDE_REPO_ROOT/configs/mde-domain-catalog.json}"
  export MDE_REFERENCE_SOURCES_FILE="${MDE_REFERENCE_SOURCES_FILE:-$MDE_REPO_ROOT/configs/mde-reference-sources.json}"
  export MDE_PRESET_CATALOG_FILE="${MDE_PRESET_CATALOG_FILE:-$MDE_REPO_ROOT/configs/mde-preset-catalog.json}"
  export MDE_LEARNING_REGISTRY_FILE="${MDE_LEARNING_REGISTRY_FILE:-$MDE_REPO_ROOT/configs/mde-learning-registry.json}"
  export MDE_GLOBAL_MISE_CONFIG_FILE="${MDE_GLOBAL_MISE_CONFIG_FILE:-$HOME/.config/mise/config.toml}"
  export MDE_RUN_ID="${MDE_RUN_ID:-mde-run-$(date +%Y%m%d%H%M%S)}"
  export MDE_CORRELATION_ID="${MDE_CORRELATION_ID:-$MDE_RUN_ID}"
  mde_export_cache_policy_env
}

mde_setup_managed_path() {
  local home="${HOME:-/Users/rmanaloto}"
  local path_rest="${PATH:-/usr/bin:/bin}"
  path_rest="${path_rest//:$home\/.local\/share\/mise\/shims:/:}"
  path_rest="${path_rest//:$home\/.local\/share\/mise\/bin:/:}"
  path_rest="${path_rest//:$home\/.local\/bin:/:}"
  path_rest="${path_rest//:$home\/.bun\/bin:/:}"
  path_rest="${path_rest//:$home\/.pixi\/bin:/:}"
  path_rest="${path_rest//:\/Applications\/Codex.app\/Contents\/Resources:/:}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:${path_rest}"
}

mde_disable_mise_auto_install() {
  export MISE_NOT_FOUND_AUTO_INSTALL="false"
  export MISE_AUTO_INSTALL="false"
  export MISE_TASK_AUTO_INSTALL="false"
  export MISE_EXEC_AUTO_INSTALL="false"
}

mde_python_cmd() {
  if command -v python3 >/dev/null 2>&1; then
    printf 'python3\n'
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    printf 'python\n'
    return 0
  fi
  printf 'python3 or python is required for policy checks\n' >&2
  return 1
}

mde_real_command() {
  local cmd="$1"
  local guard_dir="${MDE_GUARD_DIR:-}"
  local candidate

  while IFS= read -r candidate; do
    [[ -z "$candidate" ]] && continue
    if [[ -n "$guard_dir" && "$candidate" == "$guard_dir/"* ]]; then
      continue
    fi
    printf '%s\n' "$candidate"
    return 0
  done < <(which -a "$cmd" 2>/dev/null || true)

  return 1
}

mde_json_query() {
  local file="$1"
  local script="$2"
  local py
  py="$(mde_python_cmd)" || return 1
  "$py" - "$file" "$script" <<'PY'
import json
import os
import sys

path, script = sys.argv[1:3]
with open(path, 'r', encoding='utf-8') as fh:
    data = json.load(fh)
home = os.environ.get('HOME', '')
repo = os.environ.get('MDE_REPO_ROOT', '')
ns = {'data': data, 'home': home, 'repo': repo}
result = eval(script, {"__builtins__": {}}, ns)
if isinstance(result, (dict, list)):
    print(json.dumps(result))
elif result is None:
    pass
else:
    print(result)
PY
}

mde_validate_json_file() {
  local file="$1"
  local py
  py="$(mde_python_cmd)" || return 1
  "$py" - "$file" <<'PY' >/dev/null
import json
import sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    json.load(fh)
PY
}

mde_skill_registry_has_id() {
  local skill_id="$1"
  local py
  py="$(mde_python_cmd)" || return 1
  "$py" - "$MDE_SKILL_REGISTRY_FILE" "$skill_id" <<'PY' >/dev/null
import json
import sys
path, skill_id = sys.argv[1:3]
with open(path, 'r', encoding='utf-8') as fh:
    data = json.load(fh)
for item in data.get('skills', []):
    aliases = item.get('aliases', [])
    if item.get('id') == skill_id or skill_id in aliases:
        sys.exit(0)
sys.exit(1)
PY
}

mde_skill_registry_path_for_id() {
  local skill_id="$1"
  local py
  py="$(mde_python_cmd)" || return 1
  "$py" - "$MDE_SKILL_REGISTRY_FILE" "$skill_id" <<'PY'
import json
import sys
path, skill_id = sys.argv[1:3]
with open(path, 'r', encoding='utf-8') as fh:
    data = json.load(fh)
for item in data.get('skills', []):
    aliases = item.get('aliases', [])
    if item.get('id') == skill_id or skill_id in aliases:
        print(item.get('canonical_path', ''))
        sys.exit(0)
sys.exit(1)
PY
}

mde_resolve_skill_path() {
  local skill_id="$1"
  local rel
  rel="$(mde_skill_registry_path_for_id "$skill_id" 2>/dev/null || true)"
  [[ -n "$rel" ]] || return 1
  printf '%s/%s\n' "$MDE_REPO_ROOT" "$rel"
}

mde_exception_allows_target() {
  local manager="$1"
  local target="$2"
  local py
  py="$(mde_python_cmd)" || return 1
  "$py" - "$MDE_MISE_EXCEPTION_ALLOWLIST" "$manager" "$target" <<'PY' >/dev/null
import json
import sys
path, manager, target = sys.argv[1:4]
with open(path, 'r', encoding='utf-8') as fh:
    data = json.load(fh)
needle = target.strip().lower()
for item in data.get('exceptions', []):
    allowed = [x.lower() for x in item.get('allowed_installers', [])]
    targets = [x.lower() for x in item.get('targets', [])]
    if manager.lower() in allowed and needle in targets:
        sys.exit(0)
sys.exit(1)
PY
}

mde_prepare_guard_dir() {
  local dir="${MDE_GUARD_DIR:-}"
  local wrapper="$MDE_REPO_ROOT/scripts/mde-command-guard.sh"
  local cmd

  if [[ -n "$dir" && -d "$dir" ]]; then
    export MDE_GUARD_DIR="$dir"
    export PATH="$dir:$PATH"
    printf '%s\n' "$dir"
    return 0
  fi

  if [[ -z "$dir" ]]; then
    dir="$(mktemp -d 2>/dev/null || mktemp -d -t mde-agent-guard)"
  fi
  mkdir -p "$dir"

  for cmd in brew npm bun uv pip pip3 pipx cargo go curl; do
    ln -sfn "$wrapper" "$dir/$cmd"
  done

  export MDE_GUARD_DIR="$dir"
  export PATH="$dir:$PATH"
  printf '%s\n' "$dir"
}

mde_assert_repo_trusted() {
  local root="$1"
  if ! command -v mise >/dev/null 2>&1; then
    return 1
  fi
  (cd "$root" && mise trust >/dev/null)
}

mde_block_legacy_installer_in_agent_context() {
  local script_name="$1"
  local remediation="$2"
  if [[ "${MDE_AGENT_CONTEXT:-0}" != "1" ]]; then
    return 0
  fi
  mde_emit_telemetry_event "policy.command.blocked" "blocked" "$script_name is blocked in agent context" "script=$script_name" "remediation=$remediation"
  printf '%s\n' "$script_name is blocked in agent context. Use: $remediation" >&2
  exit 1
}
