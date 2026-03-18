#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install

telemetry_dir="$(mde_telemetry_dir)"
latest_events="$(find "$telemetry_dir" -maxdepth 1 -type f -name '*-events.jsonl' 2>/dev/null | sort | tail -n 1)"
latest_preflight="$MDE_REPO_ROOT/reports/agent-policy/latest-preflight.json"

tool_count="$(python3 - <<'PY' "$MDE_TOOL_OWNERSHIP_FILE"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    print(len(json.load(fh).get('tools', [])))
PY
)"
skill_count="$(python3 - <<'PY' "$MDE_SKILL_REGISTRY_FILE"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    print(len(json.load(fh).get('skills', [])))
PY
)"
exception_count="$(python3 - <<'PY' "$MDE_MISE_EXCEPTION_ALLOWLIST"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    print(len(json.load(fh).get('exceptions', [])))
PY
)"

printf 'MDE Agent Runtime Report\n'
printf 'repo_root: %s\n' "$MDE_REPO_ROOT"
printf 'global_mise_config: %s\n' "$MDE_GLOBAL_MISE_CONFIG_FILE"
printf 'tool_registry_entries: %s\n' "$tool_count"
printf 'skill_registry_entries: %s\n' "$skill_count"
printf 'exception_registry_entries: %s\n' "$exception_count"
printf 'latest_preflight: %s\n' "${latest_preflight:-missing}"
printf 'latest_events: %s\n' "${latest_events:-missing}"

if [[ -f "$latest_preflight" ]]; then
  printf '\nlatest_preflight_overall: '
  python3 - <<'PY' "$latest_preflight"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    print(json.load(fh).get('overall', 'unknown'))
PY
fi

if [[ -n "$latest_events" && -f "$latest_events" ]]; then
  printf '\nrecent_events:\n'
  tail -n 10 "$latest_events"
fi
