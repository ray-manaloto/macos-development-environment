#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"

mde_policy_init
mde_setup_managed_path

MDE_PLATFORM="${MDE_PLATFORM:-$(mde_detect_platform)}"
MDE_DRIFT_ENFORCE="${MDE_DRIFT_ENFORCE:-0}"

warnings=0
errors=0

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

warn() {
  log "DRIFT: $*"
  warnings=$((warnings + 1))
}

err() {
  log "ERROR: $*"
  errors=$((errors + 1))
}

resolve_realpath() {
  local path="$1"
  local py
  py="$(mde_python_cmd)" || return 1
  "$py" - "$path" <<'PY'
import os
import sys
print(os.path.realpath(sys.argv[1]))
PY
}

is_managed_wrapper() {
  local path="${1:-}"
  [[ -f "$path" ]] || return 1
  grep -q '^# Managed by macos-development-environment\.' "$path" 2>/dev/null
}

classify_owner() {
  local path="${1:-}"
  local real=""

  if [[ -z "$path" ]]; then
    printf 'missing\n'
    return 0
  fi

  real="$(resolve_realpath "$path" 2>/dev/null || printf '%s' "$path")"

  if [[ "$path" == "$HOME/.local/share/mise/shims/"* || "$path" == "$HOME/.local/share/mise/installs/"* || "$path" == "$HOME/.local/share/mise/bin/"* || "$real" == "$HOME/.local/share/mise/shims/"* || "$real" == "$HOME/.local/share/mise/installs/"* || "$real" == "$HOME/.local/share/mise/bin/"* ]]; then
    printf 'mise\n'
  elif [[ "$real" == /Applications/Codex.app/Contents/Resources/* ]]; then
    printf 'app-bundle\n'
  elif [[ "$real" == /opt/homebrew/* || "$real" == /usr/local/* ]]; then
    printf 'brew\n'
  elif [[ "$real" == "$HOME/.bun/"* ]]; then
    printf 'bun-global\n'
  elif [[ "$real" == "$HOME/.local/bin/"* ]] && is_managed_wrapper "$real"; then
    printf 'managed-wrapper\n'
  elif [[ "$real" == "$HOME/.cargo/bin/"* || "$real" == "$HOME/go/bin/"* || "$real" == "$HOME/.local/bin/"* ]]; then
    printf 'local-bin\n'
  else
    printf 'other\n'
  fi
}

registry_entries() {
  local py
  py="$(mde_python_cmd)" || return 1
  "$py" - "$MDE_TOOL_OWNERSHIP_FILE" <<'PY'
import json
import sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    data = json.load(fh)
for item in data.get('tools', []):
    print(f"{item.get('id','')}|{item.get('command','')}|{item.get('owner','')}|{1 if item.get('preflight_required') else 0}")
PY
}

devcontainer_manifest_entries() {
  local manifest="$MDE_REPO_ROOT/.devcontainer/mise.toml"
  local py
  [[ -f "$manifest" ]] || return 1
  py="$(mde_python_cmd)" || return 1
  "$py" - "$manifest" <<'PY'
import sys
import tomllib

manifest_path = sys.argv[1]
with open(manifest_path, "rb") as fh:
    data = tomllib.load(fh)

command_aliases = {
    "python": "python,python3",
}

tool_table = data.get("tools")
if isinstance(tool_table, dict):
    tool_ids = sorted(tool_table)
else:
    tool_ids = sorted(key for key in data if key != "settings")

for tool_id in tool_ids:
    print(f"{tool_id}|{command_aliases.get(tool_id, tool_id)}|mise|1")
PY
}

required_entries() {
  local entries=""
  if mde_is_devcontainer; then
    entries="$(devcontainer_manifest_entries 2>/dev/null || true)"
    if [[ -n "$entries" ]]; then
      printf '%s\n' "$entries"
      return 0
    fi
  fi
  registry_entries
}

check_path_ordering() {
  local first_path_entry
  first_path_entry="${PATH%%:*}"
  if [[ "$first_path_entry" != "$HOME/.local/share/mise/shims" ]]; then
    warn "mise shims are not first in PATH (first entry: $first_path_entry)"
  fi
}

check_conflicting_managers() {
  local mgr dir
  for mgr in nvm volta asdf pyenv; do
    dir="$HOME/.$mgr"
    if [[ -d "$dir" ]]; then
      warn "conflicting manager directory found: $dir"
    fi
  done
}

check_registry_tools() {
  local id command_spec target_owner preflight_required
  local resolved current_owner matched_command display_command
  local -a command_candidates
  local match match_owner foreign_paths

  while IFS='|' read -r id command_spec target_owner preflight_required; do
    [[ -n "$command_spec" ]] || continue
    [[ "$target_owner" == "mise" ]] || continue

    IFS=',' read -r -a command_candidates <<<"$command_spec"
    display_command="${command_spec//,/|}"
    resolved=""
    matched_command=""
    for candidate in "${command_candidates[@]}"; do
      [[ -n "$candidate" ]] || continue
      resolved="$(command -v "$candidate" 2>/dev/null || true)"
      if [[ -n "$resolved" ]]; then
        matched_command="$candidate"
        break
      fi
    done

    if [[ -z "$resolved" ]]; then
      if [[ "$preflight_required" == "1" ]]; then
        warn "required mise-managed command '$display_command' is missing from PATH"
      fi
      continue
    fi

    current_owner="$(classify_owner "$resolved")"
    if [[ "$current_owner" != "mise" && "$current_owner" != "managed-wrapper" && "$current_owner" != "app-bundle" ]]; then
      warn "'$matched_command' resolves to $resolved (owner=$current_owner, expected mise)"
    fi

    foreign_paths=()
    while IFS= read -r match; do
      [[ -n "$match" ]] || continue
      match_owner="$(classify_owner "$match")"
      if [[ "$match_owner" != "mise" && "$match_owner" != "managed-wrapper" && "$match_owner" != "app-bundle" ]]; then
        foreign_paths+=("$match")
      fi
    done < <(which -a "$matched_command" 2>/dev/null | awk '!seen[$0]++')

    if [[ "${#foreign_paths[@]}" -gt 0 ]]; then
      warn "'$matched_command' also exists outside mise: ${foreign_paths[*]}"
    fi
  done < <(required_entries)
}

check_registry_parses() {
  if ! mde_validate_json_file "$MDE_TOOL_OWNERSHIP_FILE"; then
    err "tool ownership registry is not valid JSON: $MDE_TOOL_OWNERSHIP_FILE"
  fi
}

log "Running drift check (platform=$MDE_PLATFORM)..."
check_registry_parses
check_path_ordering
check_conflicting_managers
check_registry_tools

if [[ "$errors" -gt 0 ]]; then
  log "Drift check: $errors errors, $warnings warnings -- FAILED"
  exit 1
fi

if [[ "$warnings" -gt 0 ]]; then
  log "Drift check: $warnings warnings found"
  if [[ "$MDE_DRIFT_ENFORCE" == "1" ]]; then
    log "Enforcement mode: exiting non-zero on warnings"
    exit 1
  fi
  exit 0
fi

log "Drift check: clean (no policy violations)"
exit 0
