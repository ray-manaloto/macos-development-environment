#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install

mde_emit_telemetry_event "policy.verify.started" started "Agent runtime verification started" "repo=$MDE_REPO_ROOT"
"$SCRIPT_DIR/mde-agent-preflight.sh" --quiet >/dev/null

# Contract surfaces that must stay wired into verification:
# configs/mde-domain-catalog.json
# configs/mde-reference-sources.json
# configs/mde-preset-catalog.json
# configs/mde-learning-registry.json

failures=0
mkdir -p "$MDE_REPO_ROOT/.artifacts/tmp"
skillport_cache="$MDE_REPO_ROOT/.artifacts/tmp/mde-agent-verify.$BASHPID.$RANDOM.cache"
: > "$skillport_cache"
trap 'rm -f "$skillport_cache"' EXIT
if command -v skillport >/dev/null 2>&1; then
  SKILLPORT_NO_PAGER=1 skillport list > "$skillport_cache" 2>/dev/null || true
fi

pass() { printf 'PASS %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1" >&2; failures=$((failures + 1)); }

require_text() {
  local file="$1"
  local pattern="$2"
  local desc="$3"
  if rg -q "$pattern" "$file"; then
    pass "$desc"
  else
    fail "$desc ($file)"
  fi
}

skill_exists() {
  local skill_id="$1"
  local raw_skill_id="${skill_id#skills/}"
  if mde_skill_registry_has_id "$skill_id"; then
    return 0
  fi
  if mde_skill_registry_has_id "$raw_skill_id"; then
    return 0
  fi
  if [[ -s "$skillport_cache" ]] && rg -q "(^|[[:space:]])(${skill_id}|${raw_skill_id})([[:space:]]|$)" "$skillport_cache"; then
    return 0
  fi
  return 1
}

scan_skill_ids() {
  local file="$1"
  rg -o 'skills/[a-zA-Z0-9._/-]+' "$file" 2>/dev/null | sort -u || true
}

has_transition_exception_marker() {
  rg -q 'MDE_POLICY_TRANSITION_EXCEPTION=1' "$1"
}

check_required_surfaces() {
  require_text "$MDE_REPO_ROOT/AGENTS.md" 'skills/mde-agent-runtime-contract' 'top-level AGENTS references runtime contract skill'
  require_text "$MDE_REPO_ROOT/AGENTS.md" 'mde-package-cache-policy' 'top-level AGENTS references cache policy skill'
  require_text "$MDE_REPO_ROOT/AGENTS.md" 'mde-domain-catalog\.json' 'top-level AGENTS references the domain catalog'
  require_text "$MDE_REPO_ROOT/AGENTS.md" 'mde-reference-sources\.json' 'top-level AGENTS references the reference source catalog'
  require_text "$MDE_REPO_ROOT/AGENTS.md" 'mde-preset-catalog\.json' 'top-level AGENTS references the preset catalog'
  require_text "$MDE_REPO_ROOT/AGENTS.md" 'mde-learning-registry\.json' 'top-level AGENTS references the learning registry'
  require_text "$MDE_REPO_ROOT/.agents/AGENTS.md" 'skills/mde-agent-runtime-contract' 'local AGENTS references runtime contract skill'
  require_text "$MDE_REPO_ROOT/.agents/AGENTS.md" 'reuse package manager caches by default' 'local AGENTS references cache-first policy'
  require_text "$MDE_REPO_ROOT/scripts/agent-runner.sh" 'configs/mde-domain-catalog\.json' 'agent runner injects the domain catalog'
  require_text "$MDE_REPO_ROOT/scripts/agent-runner.sh" 'configs/mde-reference-sources\.json' 'agent runner injects the reference source catalog'
  require_text "$MDE_REPO_ROOT/scripts/agent-runner.sh" 'configs/mde-preset-catalog\.json' 'agent runner injects the preset catalog'
  require_text "$MDE_REPO_ROOT/scripts/agent-runner.sh" 'configs/mde-learning-registry\.json' 'agent runner injects the learning registry'
  require_text "$MDE_REPO_ROOT/scripts/agent-runner.sh" 'domain classification' 'agent runner mentions domain classification'
  require_text "$MDE_REPO_ROOT/scripts/agent-runner.sh" 'delegat' 'agent runner mentions delegation'
  require_text "$MDE_REPO_ROOT/scripts/teams/run-mde-autoresearch-team.sh" 'domain classification' 'autoresearch runner requires domain classification'
  require_text "$MDE_REPO_ROOT/scripts/teams/run-mde-autoresearch-team.sh" 'delegat' 'autoresearch runner requires delegation'
  require_text "$MDE_REPO_ROOT/scripts/teams/validate-mde-autoresearch-output.sh" 'preset' 'autoresearch validator checks preset coverage markers'
  require_text "$MDE_REPO_ROOT/scripts/teams/validate-mde-autoresearch-output.sh" 'learning registry' 'autoresearch validator checks learning registry markers'
  require_text "$MDE_REPO_ROOT/scripts/teams/run-mde-domain-team.sh" 'domain classification' 'domain runner requires domain classification'
  require_text "$MDE_REPO_ROOT/scripts/teams/run-mde-domain-team.sh" 'delegat' 'domain runner requires delegation'
  require_text "$MDE_REPO_ROOT/scripts/teams/validate-mde-domain-output.sh" 'preset' 'domain validator checks preset coverage markers'
  require_text "$MDE_REPO_ROOT/scripts/teams/validate-mde-domain-output.sh" 'learning registry' 'domain validator checks learning registry markers'
}

check_team_yaml() {
  local file
  while IFS= read -r file; do
    require_text "$file" 'mde-agent-runtime-contract' "team requires runtime contract skill: $(basename "$file")"
    while IFS= read -r skill_id; do
      [[ -n "$skill_id" ]] || continue
      if skill_exists "$skill_id"; then
        pass "skill id resolves in $(basename "$file"): $skill_id"
      else
        fail "skill id missing in $(basename "$file"): $skill_id"
        mde_emit_telemetry_event "policy.skill.missing" failed "Missing skill id" "file=$file" "skill=$skill_id"
      fi
    done < <(scan_skill_ids "$file")
  done < <(find "$MDE_REPO_ROOT/configs/agent-teams" -maxdepth 1 -type f -name '*.yaml' | sort)
}

check_registry_files() {
  local file
  for file in \
    "$MDE_TOOL_OWNERSHIP_FILE" \
    "$MDE_MODERNIZATION_MATRIX_FILE" \
    "$MDE_MISE_EXCEPTION_ALLOWLIST" \
    "$MDE_SKILL_REGISTRY_FILE" \
    "$MDE_DOMAIN_CATALOG_FILE" \
    "$MDE_REFERENCE_SOURCES_FILE" \
    "$MDE_PRESET_CATALOG_FILE" \
    "$MDE_LEARNING_REGISTRY_FILE"; do
    if [[ -r "$file" ]] && mde_validate_json_file "$file"; then
      pass "registry parses: $(basename "$file")"
    else
      fail "registry invalid: $file"
    fi
  done
}

check_cache_contract_schema() {
  if python3 - "$MDE_MODERNIZATION_MATRIX_FILE" <<'PY' >/dev/null
import json
import sys

required = {
    "package_manager_backend",
    "cache_mechanism",
    "cache_directory_or_source",
    "cache_scope",
    "cache_warming_supported",
    "cache_pruning_allowed",
    "cache_policy_mandatory_for_automation",
}

with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)

assert data["policy"]["cache_policy_defaults"]["reuse_caches_by_default"] is True
for item in data["global_tools"]:
    assert required.issubset(item["cache_policy"].keys()), item["id"]
PY
  then
    pass 'matrix encodes cache policy defaults and per-tool cache fields'
  else
    fail 'matrix is missing required cache policy fields'
  fi
}

check_cache_guidance() {
  require_text "$MDE_REPO_ROOT/.agents/skills/mde-agent-runtime-contract/SKILL.md" 'cache' 'runtime contract skill mentions cache policy'
  require_text "$MDE_REPO_ROOT/.agents/skills/mde-package-cache-policy/SKILL.md" 'cache pruning' 'cache policy skill defines pruning guidance'
}

check_domain_contracts() {
  if "$SCRIPT_DIR/mde-refs-verify.sh" >/dev/null 2>&1; then
    pass 'reference bundle verification passes'
  else
    fail 'reference bundle verification fails'
  fi
  if "$SCRIPT_DIR/mde-preset-verify.sh" >/dev/null 2>&1; then
    pass 'preset bundle verification passes'
  else
    fail 'preset bundle verification fails'
  fi
  if "$SCRIPT_DIR/mde-domain-verify.sh" >/dev/null 2>&1; then
    pass 'domain verification passes'
  else
    fail 'domain verification fails'
  fi
  if "$SCRIPT_DIR/mde-learn-verify.sh" >/dev/null 2>&1; then
    pass 'learning verification passes'
  else
    fail 'learning verification fails'
  fi
}

list_policy_surfaces() {
  printf '%s\n' \
    "$MDE_REPO_ROOT/AGENTS.md" \
    "$MDE_REPO_ROOT/.agents/AGENTS.md" \
    "$MDE_REPO_ROOT/scripts/agent-runner.sh" \
    "$MDE_REPO_ROOT/scripts/teams/run-mde-autoresearch-team.sh" \
    "$MDE_REPO_ROOT/scripts/teams/validate-mde-autoresearch-output.sh" \
    "$MDE_REPO_ROOT/scripts/teams/run-mde-domain-team.sh" \
    "$MDE_REPO_ROOT/scripts/teams/validate-mde-domain-output.sh" \
    "$MDE_REPO_ROOT/scripts/mde-agent-verify.sh" \
    "$MDE_REPO_ROOT/scripts/mde-domain-verify.sh" \
    "$MDE_REPO_ROOT/scripts/mde-refs-verify.sh" \
    "$MDE_REPO_ROOT/scripts/mde-preset-verify.sh" \
    "$MDE_REPO_ROOT/scripts/mde-learn-verify.sh"
}

check_banned_install_guidance() {
  local banned='brew install|npm -g|bun add -g|uv tool install|pixi global install|pip install --user|pipx install|cargo install|go install'
  local file
  while IFS= read -r file; do
    [[ -n "$file" && -f "$file" ]] || continue
    if has_transition_exception_marker "$file"; then
      pass "transition exception honored for $(basename "$file")"
      continue
    fi
    if rg -n "$banned" "$file" >/dev/null 2>&1; then
      fail "unmanaged install guidance found in $file"
    fi
  done < <(list_policy_surfaces | awk '!seen[$0]++')
}

check_required_surfaces
check_registry_files
check_cache_contract_schema
check_cache_guidance
check_team_yaml
check_domain_contracts
check_banned_install_guidance

if (( failures == 0 )); then
  mde_emit_telemetry_event "policy.verify.passed" passed "Agent runtime verification passed" "repo=$MDE_REPO_ROOT"
  exit 0
fi

mde_emit_telemetry_event "policy.verify.failed" failed "Agent runtime verification failed" "repo=$MDE_REPO_ROOT" "failures=$failures"
exit 1
