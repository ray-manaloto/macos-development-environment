#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"
# shellcheck source=scripts/lib/mde-json.sh
source "$SCRIPT_DIR/lib/mde-json.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install
mde_prepare_cache_dirs

JSON_OUTPUT=0
QUIET=0
for arg in "$@"; do
  case "$arg" in
    --json) JSON_OUTPUT=1 ;;
    --quiet) QUIET=1 ;;
    *) printf 'Unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

say() {
  if [[ "$QUIET" != "1" ]]; then
    printf '%s\n' "$1"
  fi
}

say_failure() {
  printf '%s\n' "$1" >&2
}

record_check() {
  local name="$1"
  local ok="$2"
  local details="$3"
  if [[ "$ok" == "1" ]]; then
    mde_add_check "$name" pass hard "$details"
    say "PASS $name: $details"
  else
    mde_add_check "$name" fail hard "$details"
    say_failure "FAIL $name: $details"
  fi
}

record_warn() {
  local name="$1"
  local details="$2"
  mde_add_check "$name" warn soft "$details" true
  say "WARN $name: $details"
}

check_mise() {
  if ! command -v mise >/dev/null 2>&1; then
    record_check "mise_on_path" 0 "mise is not available on PATH"
    return 1
  fi
  record_check "mise_on_path" 1 "$(command -v mise)"
}

check_path() {
  local first_entry
  first_entry="${PATH%%:*}"
  if [[ "$first_entry" == "$HOME/.local/share/mise/shims" ]]; then
    record_check "mise_shims_first" 1 "$first_entry"
  else
    record_check "mise_shims_first" 0 "first PATH entry is $first_entry"
  fi
}

check_global_config() {
  if [[ -r "$MDE_GLOBAL_MISE_CONFIG_FILE" ]]; then
    record_check "global_mise_config" 1 "$MDE_GLOBAL_MISE_CONFIG_FILE"
  else
    record_check "global_mise_config" 0 "$MDE_GLOBAL_MISE_CONFIG_FILE is not readable"
  fi
}

check_repo_trust() {
  if mde_assert_repo_trusted "$MDE_REPO_ROOT"; then
    record_check "repo_trusted" 1 "$MDE_REPO_ROOT"
  else
    record_check "repo_trusted" 0 "mise trust failed for $MDE_REPO_ROOT"
  fi
}

check_registries() {
  local file
  for file in "$MDE_TOOL_OWNERSHIP_FILE" "$MDE_MODERNIZATION_MATRIX_FILE" "$MDE_MISE_EXCEPTION_ALLOWLIST" "$MDE_SKILL_REGISTRY_FILE"; do
    if [[ ! -r "$file" ]]; then
      record_check "registry:$(basename "$file")" 0 "$file is not readable"
      continue
    fi
    if mde_validate_json_file "$file"; then
      record_check "registry:$(basename "$file")" 1 "$file parses"
    else
      record_check "registry:$(basename "$file")" 0 "$file does not parse"
    fi
  done
}

check_skills() {
  local required_skill_ids=(
    "skills/mde-agent-runtime-contract"
    "skills/mise-enforcement"
    "skills/mde-global-tool-migration"
    "skills/mde-autoresearch"
    "skills/mde-python-backend-selection"
    "skills/mde-node-cli-declaration"
    "skills/mde-native-tool-validation"
    "skills/mde-package-cache-policy"
  )
  local skill_id
  for skill_id in "${required_skill_ids[@]}"; do
    if ! mde_skill_registry_has_id "$skill_id"; then
      record_check "skill:$skill_id" 0 "required skill id is missing from $MDE_SKILL_REGISTRY_FILE"
    fi
  done

  while IFS= read -r skill_id; do
    [[ -n "$skill_id" ]] || continue
    local skill_path
    skill_path="$(mde_resolve_skill_path "$skill_id" 2>/dev/null || true)"
    if [[ -n "$skill_path" && -r "$skill_path" ]]; then
      record_check "skill:$skill_id" 1 "$skill_path"
    else
      record_check "skill:$skill_id" 0 "skill path missing for $skill_id"
    fi
  done < <(python3 - "$MDE_SKILL_REGISTRY_FILE" <<'PY'
import json
import sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    data = json.load(fh)
for item in data.get('skills', []):
    print(item.get('id', ''))
PY
)
}

check_cache_contract() {
  local status
  status="$(python3 - "$MDE_MODERNIZATION_MATRIX_FILE" <<'PY'
import json
import sys

required = [
    "package_manager_backend",
    "cache_mechanism",
    "cache_directory_or_source",
    "cache_scope",
    "cache_warming_supported",
    "cache_pruning_allowed",
    "cache_policy_mandatory_for_automation",
]

with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)

missing = []
for item in data.get("global_tools", []):
    policy = item.get("cache_policy") or {}
    if any(key not in policy for key in required):
        missing.append(item.get("id"))

if missing:
    print(",".join(missing))
    sys.exit(1)
PY
)" || true
  if [[ -z "$status" ]]; then
    record_check "cache_contract_matrix" 1 "$MDE_MODERNIZATION_MATRIX_FILE encodes cache policy for managed tools"
  else
    record_check "cache_contract_matrix" 0 "missing cache policy fields for: $status"
  fi
}

check_cache_dirs() {
  local name value
  while IFS='=' read -r name value; do
    [[ -n "$name" && -n "$value" ]] || continue
    mkdir -p "$value" 2>/dev/null || true
    if [[ -d "$value" && -w "$value" ]]; then
      record_check "cache_dir:$name" 1 "$value"
    else
      record_check "cache_dir:$name" 0 "$value is not writable"
    fi
  done < <(mde_cache_policy_env_report)
}

check_cache_flags() {
  if [[ "${MISE_NOT_FOUND_AUTO_INSTALL:-}" == "false" && "${MISE_AUTO_INSTALL:-}" == "false" ]]; then
    record_check "cache_no_implicit_cold_installs" 1 "mise auto-install is disabled in agent context"
  else
    record_check "cache_no_implicit_cold_installs" 0 "mise auto-install flags are not disabled"
  fi
}

check_owned_commands() {
  python3 - "$MDE_TOOL_OWNERSHIP_FILE" <<'PY' | while IFS='|' read -r command preflight_required; do
import json
import sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    data = json.load(fh)
for item in data.get('tools', []):
    print(f"{item.get('command','')}|{1 if item.get('preflight_required') else 0}")
PY
    [[ -n "$command" ]] || continue
    local resolved
    resolved="$(command -v "$command" 2>/dev/null || true)"
    if [[ "$preflight_required" == "1" ]]; then
      if [[ -n "$resolved" && ( "$resolved" == "$HOME/.local/share/mise/shims/"* || "$resolved" == "$HOME/.local/share/mise/installs/"* || "$resolved" == "$HOME/.local/share/mise/bin/"* ) ]]; then
        record_check "command:$command" 1 "$resolved"
      else
        record_check "command:$command" 0 "expected mise-managed path, got ${resolved:-missing}"
      fi
    elif [[ -n "$resolved" ]]; then
      record_warn "command:$command" "$resolved"
    fi
  done
}

mde_emit_telemetry_event "policy.preflight.started" started "Agent runtime preflight started" "repo=$MDE_REPO_ROOT"

check_mise || true
check_path
check_global_config
check_repo_trust
check_registries
check_skills
check_cache_contract
check_cache_dirs
check_cache_flags
check_owned_commands

overall_json="$(mde_emit_json)"
overall_status="$(python3 - <<'PY' "$overall_json"
import json
import sys
print(json.loads(sys.argv[1]).get('overall', 'fail'))
PY
)"
mkdir -p "$MDE_REPO_ROOT/reports/agent-policy"
printf '%s\n' "$overall_json" > "$MDE_REPO_ROOT/reports/agent-policy/latest-preflight.json"

if [[ "$JSON_OUTPUT" == "1" ]]; then
  printf '%s\n' "$overall_json"
else
  say "overall: $overall_status"
fi

if [[ "$overall_status" == "pass" ]]; then
  mde_emit_telemetry_event "policy.preflight.passed" passed "Agent runtime preflight passed" "repo=$MDE_REPO_ROOT"
  exit 0
fi

mde_emit_telemetry_event "policy.preflight.failed" failed "Agent runtime preflight failed" "repo=$MDE_REPO_ROOT" "overall=$overall_status"
exit 1
