#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$REPO_ROOT/scripts/lib/mde-agent-policy.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install
"$REPO_ROOT/scripts/mde-agent-preflight.sh" --quiet >/dev/null
export MDE_AGENT_PREFLIGHT_PASSED=1
export MDE_AGENT_CONTEXT=1
mde_prepare_guard_dir >/dev/null

DOMAIN=""
TRIGGER_CONTEXT="${MDE_DOMAIN_TRIGGER_CONTEXT:-manual}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --domain)
      DOMAIN="$2"
      shift 2
      ;;
    --trigger)
      TRIGGER_CONTEXT="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 [--domain <domain-id>] [--trigger <context>]" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$DOMAIN" ]]; then
  DOMAIN="${MDE_ACTIVE_DOMAIN:-${MDE_DOMAIN:-}}"
fi
if [[ -z "$DOMAIN" ]]; then
  DOMAIN="$($REPO_ROOT/scripts/mde-domain-classify.sh "$TRIGGER_CONTEXT")"
fi
if [[ -z "$DOMAIN" ]]; then
  echo "Domain is required." >&2
  exit 2
fi

DOMAIN_JSON="$(python3 - "$REPO_ROOT" "$DOMAIN" <<'PY'
import json
import os
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
domain_id = sys.argv[2]
raw_path = os.environ.get('MDE_DOMAIN_CATALOG_FILE', str(repo_root / 'configs' / 'mde-domain-catalog.json'))
path = Path(raw_path)
if not path.is_absolute():
    path = repo_root / path
with path.open('r', encoding='utf-8') as fh:
    data = json.load(fh)
for domain in data.get('domains', []):
    if domain.get('id') == domain_id:
        print(json.dumps(domain))
        raise SystemExit(0)
raise SystemExit(f'Unknown domain: {domain_id}')
PY
)"

DOMAIN_NAME="$(python3 - <<'PY' "$DOMAIN_JSON"
import json
import sys
obj = json.loads(sys.argv[1])
print(obj.get('name', obj['id']))
PY
)"
TEAM_ID="$(python3 - <<'PY' "$DOMAIN_JSON"
import json
import sys
obj = json.loads(sys.argv[1])
print(obj.get('team_id') or obj.get('owner_team') or '')
PY
)"
TEAM_CONFIG_PATH="$(python3 - <<'PY' "$DOMAIN_JSON"
import json
import sys
obj = json.loads(sys.argv[1])
print(obj.get('team_config_path') or '')
PY
)"
BUNDLE_PATH="$(python3 - <<'PY' "$DOMAIN_JSON"
import json
import sys
obj = json.loads(sys.argv[1])
print(obj.get('bundle_path') or '')
PY
)"
REFERENCE_SOURCE_GROUP="$(python3 - <<'PY' "$DOMAIN_JSON"
import json
import sys
obj = json.loads(sys.argv[1])
print(obj.get('reference_source_group') or obj.get('reference_group') or obj.get('reference_bundle_id') or obj.get('id'))
PY
)"
PRESET_IDS="$(python3 - <<'PY' "$DOMAIN_JSON"
import json
import sys
obj = json.loads(sys.argv[1])
values = obj.get('preset_ids') or obj.get('domains') or []
print(', '.join(values))
PY
)"
LEARNING_RECORD_ID="$(python3 - <<'PY' "$DOMAIN_JSON"
import json
import sys
obj = json.loads(sys.argv[1])
print(obj.get('learning_record_id') or obj.get('id') or '')
PY
)"
DATE_STAMP="${MDE_DOMAIN_DATE:-$(date +%F)}"
OUT_DIR="${MDE_DOMAIN_OUT_DIR:-reports/mde-domain-sdlc/$DOMAIN}"
VALIDATOR="${MDE_DOMAIN_VALIDATOR:-$REPO_ROOT/scripts/teams/validate-mde-domain-output.sh}"
RUNNER="${MULTI_AGENT_RUNNER:-$REPO_ROOT/scripts/agent-runner.sh}"

if [[ ! -x "$RUNNER" ]]; then
  echo "Runner is not executable: $RUNNER" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
export MDE_ACTIVE_DOMAIN="$DOMAIN"
export MDE_DOMAIN_OUT_DIR="$OUT_DIR"

"$REPO_ROOT/scripts/mde-refs-refresh.sh" "$DOMAIN" >/dev/null

run_subagent() {
  local id="$1"
  local objective="$2"
  local prompt_file="$3"
  local output_file="$4"

  "$RUNNER" "Team: mde-domain-team
Subagent: $id
Date: $DATE_STAMP
Domain: $DOMAIN
Domain name: $DOMAIN_NAME
Domain team id: $TEAM_ID
Domain team config: $TEAM_CONFIG_PATH
Trigger context: $TRIGGER_CONTEXT
Reference source group: $REFERENCE_SOURCE_GROUP
Preset ids: $PRESET_IDS
Learning record id: $LEARNING_RECORD_ID
Bundle path: $BUNDLE_PATH
Objective: $objective
Prompt template: $prompt_file
Output file: $output_file
Requirements:
- Use domain classification against configs/mde-domain-catalog.json for the trigger context before proposing domain changes.
- delegate all authority, preset, and learning decisions through this domain team workflow before finalizing outcomes.
- Delegate cross-domain adoption or remediation decisions back through the owning domain SDLC team instead of accepting repo-wide guidance without review.
- Read configs/mde-reference-sources.json, configs/mde-preset-catalog.json, and configs/mde-learning-registry.json.
- Use mirrored reference metadata in .artifacts/reference-mirror and the reports/mde-domain-sdlc/$DOMAIN baseline before synthesizing new decisions.
- Cover preset coverage, learning registry writeback requirements, and verification hooks in the output.
- Do not edit configs, prompts, generator code, or docs from this runner.
- Write the required output file before finishing.
"
}

run_subagent "mirror-refresh-agent" "Refresh or validate mirrored sources for $DOMAIN" "prompts/agent-team/mde-domain-sdlc/mirror-refresh-agent.md" "$OUT_DIR/${DATE_STAMP}-01-mirror-refresh.md"
run_subagent "docs-tutorial-agent" "Extract declarative guidance for $DOMAIN" "prompts/agent-team/mde-domain-sdlc/docs-tutorial-agent.md" "$OUT_DIR/${DATE_STAMP}-02-docs-tutorial.md" &
pid_a=$!
run_subagent "repo-mining-agent" "Mine upstream repos for $DOMAIN" "prompts/agent-team/mde-domain-sdlc/repo-mining-agent.md" "$OUT_DIR/${DATE_STAMP}-03-repo-mining.md" &
pid_b=$!
run_subagent "social-signal-agent" "Review grounded social signals for $DOMAIN" "prompts/agent-team/mde-domain-sdlc/social-signal-agent.md" "$OUT_DIR/${DATE_STAMP}-04-social-signal.md" &
pid_c=$!
wait "$pid_a"
wait "$pid_b"
wait "$pid_c"
run_subagent "authority-agent" "Define authority and cache contract for $DOMAIN" "prompts/agent-team/mde-domain-sdlc/authority-agent.md" "$OUT_DIR/${DATE_STAMP}-05-authority.md"
run_subagent "implementation-agent" "Map accepted authority to preset scaffolding for $DOMAIN" "prompts/agent-team/mde-domain-sdlc/implementation-agent.md" "$OUT_DIR/${DATE_STAMP}-06-implementation.md"
run_subagent "validation-agent" "Define proof commands and acceptance checks for $DOMAIN" "prompts/agent-team/mde-domain-sdlc/validation-agent.md" "$OUT_DIR/${DATE_STAMP}-07-validation.md"
run_subagent "learning-consolidator-agent" "Capture learning registry writeback requirements for $DOMAIN" "prompts/agent-team/mde-domain-sdlc/learning-consolidator-agent.md" "$OUT_DIR/${DATE_STAMP}-08-learning.md"

"$VALIDATOR" "$DATE_STAMP" "$OUT_DIR" "$DOMAIN"
