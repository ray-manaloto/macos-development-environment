#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASKS_FILE="$ROOT_DIR/.mise.toml"
AGENT_VERIFY="$ROOT_DIR/scripts/mde-agent-verify.sh"
REFS_REFRESH="$ROOT_DIR/scripts/mde-refs-refresh.sh"
REFS_VERIFY="$ROOT_DIR/scripts/mde-refs-verify.sh"
PRESET_VERIFY="$ROOT_DIR/scripts/mde-preset-verify.sh"
DOMAIN_VERIFY="$ROOT_DIR/scripts/mde-domain-verify.sh"
LEARN_VERIFY="$ROOT_DIR/scripts/mde-learn-verify.sh"
DOMAIN_RUNNER="$ROOT_DIR/scripts/teams/run-mde-domain-team.sh"
DOMAIN_VALIDATOR="$ROOT_DIR/scripts/teams/validate-mde-domain-output.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

for task in \
  'mde:refs:refresh' \
  'mde:refs:verify' \
  'mde:preset:verify' \
  'mde:domain:verify' \
  'mde:learn:verify' \
  'mde:team:domain'
do
  if rg -q "^\[tasks\.\"${task}\"\]" "$TASKS_FILE"; then
    pass "mise task exists: $task"
  else
    fail "missing mise task: $task"
  fi
done

for file in \
  "$REFS_REFRESH" \
  "$REFS_VERIFY" \
  "$PRESET_VERIFY" \
  "$DOMAIN_VERIFY" \
  "$LEARN_VERIFY" \
  "$DOMAIN_RUNNER" \
  "$DOMAIN_VALIDATOR"
do
  if [[ -f "$file" ]]; then
    pass "file exists: $(basename "$file")"
  else
    fail "missing file: $file"
  fi
done

if rg -q 'configs/mde-domain-catalog\.json' "$AGENT_VERIFY" && \
   rg -q 'configs/mde-reference-sources\.json' "$AGENT_VERIFY" && \
   rg -q 'configs/mde-preset-catalog\.json' "$AGENT_VERIFY" && \
   rg -q 'configs/mde-learning-registry\.json' "$AGENT_VERIFY"; then
  pass 'agent verify references all new catalog and registry files'
else
  fail 'agent verify is missing one or more new catalog and registry references'
fi

if rg -q 'mde-domain-verify\.sh' "$AGENT_VERIFY" && \
   rg -q 'mde-refs-verify\.sh' "$AGENT_VERIFY" && \
   rg -q 'mde-preset-verify\.sh' "$AGENT_VERIFY" && \
   rg -q 'mde-learn-verify\.sh' "$AGENT_VERIFY"; then
  pass 'agent verify delegates to the new verification entrypoints'
else
  fail 'agent verify is missing one or more verification entrypoints'
fi

if rg -q 'domain classification' "$DOMAIN_RUNNER" && rg -q 'delegat' "$DOMAIN_RUNNER"; then
  pass 'domain runner requires classification and delegation markers'
else
  fail 'domain runner missing classification or delegation marker'
fi

if ! grep -Fq 'MDE_AGENT_RUNNER_MODE="${MDE_AGENT_RUNNER_MODE:-local-synth}"' "$DOMAIN_RUNNER"; then
  pass 'domain runner preserves the real runner path by default'
else
  fail 'domain runner still forces local-synth mode by default'
fi

if rg -q 'preset' "$DOMAIN_VALIDATOR" && rg -q 'learning registry' "$DOMAIN_VALIDATOR"; then
  pass 'domain validator checks preset and learning registry markers'
else
  fail 'domain validator missing preset or learning registry marker checks'
fi

mkdir -p "$ROOT_DIR/.artifacts/test-tmp"
tmp_dir="$ROOT_DIR/.artifacts/test-tmp/mde-domain-system.$BASHPID.$RANDOM"
rm -rf "$tmp_dir"
mkdir -p "$tmp_dir"
trap 'rm -rf "$tmp_dir"' EXIT

cat > "$tmp_dir/domain.json" <<'JSON'
{
  "routing_policy": {
    "default_domain": "python-tooling",
    "required_stage_ids": [
      "mirror-refresh-agent",
      "docs-tutorial-agent",
      "repo-mining-agent",
      "social-signal-agent",
      "authority-agent",
      "implementation-agent",
      "validation-agent",
      "learning-consolidator-agent"
    ]
  },
  "domains": [{
    "id": "python-tooling",
    "name": "Python Tooling",
    "description": "Python tooling domain",
    "team_id": "python-sdlc-team",
    "team_config_path": "configs/agent-teams/python-sdlc-team.yaml",
    "bundle_path": "configs/tool-bundles/python-tooling",
    "reference_source_group": "python-tooling",
    "learning_record_id": "learn-python-tooling-001",
    "preset_ids": ["preset-python-tooling"],
    "reference_bundle_id": "python-tooling",
    "preset_bundle_id": "preset-python-tooling",
    "tool_bundle_dir": "configs/tool-bundles/python-tooling",
    "project_authority": "pixi.toml plus pixi.lock",
    "global_cli_authority_mode": "mise declarative entry",
    "cache_contract": ["PIXI_HOME", "UV_CACHE_DIR"],
    "derived_from_authority": "configs/tool-bundles/python-tooling/pixi.toml",
    "cookbook_pages": ["https://mise.jdx.dev/mise-cookbook/python.html"]
  }]
}
JSON

cat > "$tmp_dir/refs.json" <<'JSON'
{
  "mirror_root": ".artifacts/reference-mirror",
  "source_groups": [{
    "id": "python-tooling",
    "domain_id": "python-tooling",
    "source_ids": ["python-docs", "python-cookbook", "python-community"]
  }],
  "sources": [
    {
      "id": "python-docs",
      "title": "python docs",
      "url": "https://docs.python.org/3/",
      "domain_ids": ["python-tooling"],
      "kind": "official-docs",
      "authority": "official",
      "mirror_path_hint": "official/python/index.html"
    },
    {
      "id": "python-cookbook",
      "title": "mise cookbook python",
      "url": "https://mise.jdx.dev/mise-cookbook/python.html",
      "domain_ids": ["python-tooling"],
      "kind": "official-cookbook",
      "authority": "official",
      "mirror_path_hint": "official/mise/python.html"
    },
    {
      "id": "python-community",
      "title": "python community notes",
      "url": "https://pydevtools.com/handbook/explanation/what-is-an-environment-manager/",
      "domain_ids": ["python-tooling"],
      "kind": "external-reference",
      "authority": "community",
      "mirror_path_hint": "community/python/environment-manager.html"
    }
  ]
}
JSON

cat > "$tmp_dir/presets.json" <<'JSON'
{
  "presets": [{
    "id": "preset-python-tooling",
    "description": "Refresh Python runtime references",
    "domain_ids": ["python-tooling"],
    "bundle_paths": ["configs/tool-bundles/python-tooling"],
    "primary_bundle_path": "configs/tool-bundles/python-tooling",
    "reference_source_groups": ["python-tooling"],
    "learning_record_ids": ["learn-python-tooling-001"],
    "starter_files": ["pixi.toml", "pixi.lock"],
    "cookbook_pages": ["https://mise.jdx.dev/mise-cookbook/python.html"]
  }]
}
JSON

cat > "$tmp_dir/learn.json" <<'JSON'
{
  "records": [{
    "id": "learn-python-tooling-001",
    "domain": "python-tooling",
    "domain_id": "python-tooling",
    "status": "seeded",
    "owning_team_id": "python-sdlc-team",
    "bundle_path": "configs/tool-bundles/python-tooling",
    "authoritative_source_ids": ["python-docs", "python-cookbook"],
    "accepted_learnings": ["Prefer mise managed runtimes."],
    "next_refresh_due": "2026-06-15",
    "title": "Python tooling record",
    "disposition": "adopted",
    "source_snapshots": [{"bundle_id": "python-tooling", "source_ids": ["python-docs"]}],
    "affected_prompts": ["prompts/agent-team/mde-domain-sdlc/*.md"],
    "affected_skills": ["skills/mise-enforcement"],
    "affected_docs": ["docs/toolchain-precedence.md"],
    "affected_tasks": ["mde:team:domain"],
    "required_verification": ["mise run mde:learn:verify"],
    "last_reviewed_at": "2026-03-15"
  }]
}
JSON

mkdir -p "$tmp_dir/configs/agent-teams" "$tmp_dir/configs/tool-bundles/python-tooling"
cat > "$tmp_dir/configs/agent-teams/python-sdlc-team.yaml" <<'YAML'
subagents:
  - id: mirror-refresh-agent
  - id: docs-tutorial-agent
  - id: repo-mining-agent
  - id: social-signal-agent
  - id: authority-agent
  - id: implementation-agent
  - id: validation-agent
  - id: learning-consolidator-agent
YAML
touch "$tmp_dir/configs/tool-bundles/python-tooling/pixi.toml" "$tmp_dir/configs/tool-bundles/python-tooling/pixi.lock"
python3 - "$tmp_dir" <<'PY'
import json
import sys
from pathlib import Path

tmp_dir = Path(sys.argv[1])
bundle_dir = tmp_dir / "configs" / "tool-bundles" / "python-tooling"
team_config = tmp_dir / "configs" / "agent-teams" / "python-sdlc-team.yaml"

domain_path = tmp_dir / "domain.json"
with domain_path.open("r", encoding="utf-8") as fh:
    domain = json.load(fh)
domain["domains"][0]["team_config_path"] = str(team_config)
domain["domains"][0]["bundle_path"] = str(bundle_dir)
domain["domains"][0]["tool_bundle_dir"] = str(bundle_dir)
domain["domains"][0]["derived_from_authority"] = str(bundle_dir / "pixi.toml")
with domain_path.open("w", encoding="utf-8") as fh:
    json.dump(domain, fh)

preset_path = tmp_dir / "presets.json"
with preset_path.open("r", encoding="utf-8") as fh:
    presets = json.load(fh)
presets["presets"][0]["bundle_paths"] = [str(bundle_dir)]
presets["presets"][0]["primary_bundle_path"] = str(bundle_dir)
with preset_path.open("w", encoding="utf-8") as fh:
    json.dump(presets, fh)

learn_path = tmp_dir / "learn.json"
with learn_path.open("r", encoding="utf-8") as fh:
    learn = json.load(fh)
learn["records"][0]["bundle_path"] = str(bundle_dir)
with learn_path.open("w", encoding="utf-8") as fh:
    json.dump(learn, fh)
PY

mkdir -p "$tmp_dir/scripts/teams"
cat > "$tmp_dir/scripts/agent-runner.sh" <<'SH'
# configs/mde-domain-catalog.json
# configs/mde-reference-sources.json
# configs/mde-preset-catalog.json
# configs/mde-learning-registry.json
# domain classification
# delegate
SH
cat > "$tmp_dir/scripts/teams/run-mde-autoresearch-team.sh" <<'SH'
# configs/mde-domain-catalog.json
# configs/mde-reference-sources.json
# configs/mde-preset-catalog.json
# configs/mde-learning-registry.json
# domain classification
# delegate
# run-mde-domain-team.sh
SH
cat > "$tmp_dir/scripts/teams/validate-mde-autoresearch-output.sh" <<'SH'
# domain classification
# delegate
# preset
# learning registry
SH
cat > "$tmp_dir/scripts/teams/run-mde-domain-team.sh" <<'SH'
# configs/mde-domain-catalog.json
# configs/mde-reference-sources.json
# configs/mde-preset-catalog.json
# configs/mde-learning-registry.json
# domain classification
# delegate
SH
cat > "$tmp_dir/scripts/teams/validate-mde-domain-output.sh" <<'SH'
# domain classification
# delegate
# preset
# learning registry
SH
cat > "$tmp_dir/scripts/mde-agent-verify.sh" <<'SH'
# mde-refs-verify.sh
# mde-preset-verify.sh
# mde-domain-verify.sh
# mde-learn-verify.sh
SH

common_env=(
  MDE_REPO_ROOT="$tmp_dir"
  MDE_DOMAIN_CATALOG_FILE="$tmp_dir/domain.json"
  MDE_REFERENCE_SOURCES_FILE="$tmp_dir/refs.json"
  MDE_PRESET_CATALOG_FILE="$tmp_dir/presets.json"
  MDE_LEARNING_REGISTRY_FILE="$tmp_dir/learn.json"
)

if env "${common_env[@]}" bash "$REFS_REFRESH" python-tooling >/dev/null 2>&1; then
  pass 'refs refresh writes mirrored metadata for a valid fixture'
else
  fail 'refs refresh rejected valid fixture catalogs'
fi

if env MDE_REQUIRE_REFERENCE_MIRROR=1 "${common_env[@]}" bash "$REFS_VERIFY" python-tooling >/dev/null 2>&1; then
  pass 'refs verify accepts valid fixture catalogs'
else
  fail 'refs verify rejected valid fixture catalogs'
fi

if env "${common_env[@]}" bash "$PRESET_VERIFY" python-tooling >/dev/null 2>&1; then
  pass 'preset verify accepts valid fixture catalogs'
else
  fail 'preset verify rejected valid fixture catalogs'
fi

if env "${common_env[@]}" bash "$DOMAIN_VERIFY" python-tooling >/dev/null 2>&1; then
  pass 'domain verify accepts valid fixture catalogs'
else
  fail 'domain verify rejected valid fixture catalogs'
fi

if env "${common_env[@]}" bash "$LEARN_VERIFY" python-tooling >/dev/null 2>&1; then
  pass 'learn verify accepts valid fixture catalogs'
else
  fail 'learn verify rejected valid fixture catalogs'
fi

runner_fixture_dir="$tmp_dir/domain-runner-fixture"
mkdir -p "$runner_fixture_dir"
stub_runner="$runner_fixture_dir/stub-runner.sh"
cat > "$stub_runner" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

task="${1:?task payload required}"
subagent="$(printf '%s\n' "$task" | sed -n 's/^Subagent: //p' | head -n1)"
output_file="$(printf '%s\n' "$task" | sed -n 's/^Output file: //p' | head -n1)"

printf '%s\n' "${MDE_AGENT_RUNNER_MODE:-unset}" >> "${TEST_CAPTURE_DIR:?}/runner-mode.log"
printf '%s\n' "$subagent" >> "${TEST_CAPTURE_DIR:?}/subagents.log"

mkdir -p "$(dirname "$output_file")"
case "$subagent" in
  mirror-refresh-agent)
    cat > "$output_file" <<EOF
## Mirror Summary
- reference source group captured for domain classification
- mirror validation completed without delegation gaps
EOF
    ;;
  docs-tutorial-agent)
    cat > "$output_file" <<EOF
## Official Coverage
- cookbook guidance retained for the selected domain
EOF
    ;;
  repo-mining-agent)
    cat > "$output_file" <<EOF
## Upstream Patterns
- repository evidence supports the selected bundle
EOF
    ;;
  social-signal-agent)
    cat > "$output_file" <<EOF
## Social Signal Disposition
- external references remain supporting evidence only
EOF
    ;;
  authority-agent)
    cat > "$output_file" <<EOF
## Authority Contract
- domain classification confirmed
- delegation remains scoped to the owning team
- reference source catalog linked to preset and learning registry inputs
EOF
    ;;
  implementation-agent)
    cat > "$output_file" <<EOF
## Preset Scaffolding
- preset bundle starter files remain delegated through the domain workflow
EOF
    ;;
  validation-agent)
    cat > "$output_file" <<EOF
## Proof Commands
- verify acceptance with mde:refs:verify, mde:preset:verify, mde:domain:verify, and mde:learn:verify
- delegation markers retained for validation review
EOF
    ;;
  learning-consolidator-agent)
    cat > "$output_file" <<EOF
## Learning Registry Writeback
- learning registry adopted update
- affected prompts recorded
- affected skills recorded
- affected docs recorded
- affected tasks recorded
- delegation remains owned by the domain workflow
EOF
    ;;
  *)
    echo "unexpected subagent: $subagent" >&2
    exit 1
    ;;
esac
SH
chmod +x "$stub_runner"

execution_out_dir="$runner_fixture_dir/out"
capture_dir="$runner_fixture_dir/capture"
mkdir -p "$capture_dir"
execution_log="$runner_fixture_dir/domain-runner.log"
if env \
  TEST_CAPTURE_DIR="$capture_dir" \
  MULTI_AGENT_RUNNER="$stub_runner" \
  MDE_DOMAIN_OUT_DIR="$execution_out_dir" \
  MDE_DOMAIN_DATE="2026-03-15" \
  MDE_DOMAIN_VALIDATOR="$DOMAIN_VALIDATOR" \
  MDE_DOMAIN_CATALOG_FILE="$tmp_dir/domain.json" \
  MDE_REFERENCE_SOURCES_FILE="$tmp_dir/refs.json" \
  MDE_PRESET_CATALOG_FILE="$tmp_dir/presets.json" \
  MDE_LEARNING_REGISTRY_FILE="$tmp_dir/learn.json" \
  bash "$DOMAIN_RUNNER" --domain python-tooling >"$execution_log" 2>&1; then
  pass 'domain runner executes end-to-end with a stubbed runner and actual validator'
else
  cat "$execution_log" >&2
  fail 'domain runner failed end-to-end with a stubbed runner'
fi

if [[ -s "$capture_dir/runner-mode.log" ]] && ! rg -qx 'local-synth' "$capture_dir/runner-mode.log"; then
  pass 'domain runner leaves MDE_AGENT_RUNNER_MODE unset during default execution'
else
  fail 'domain runner unexpectedly forced local-synth mode during default execution'
fi

subagent_count="$(wc -l < "$capture_dir/subagents.log" | tr -d ' ')"
if [[ "$subagent_count" == "8" ]]; then
  pass 'domain runner invokes all eight domain subagents through the configured runner'
else
  fail "expected 8 domain subagent invocations (got $subagent_count)"
fi

parallel_dir="$runner_fixture_dir/parallel"
shared_guard_dir="$parallel_dir/shared-guard"
mkdir -p "$parallel_dir"
if env MDE_GUARD_DIR="$shared_guard_dir" bash -lc "source '$ROOT_DIR/scripts/lib/mde-agent-policy.sh'; mde_policy_init; mde_prepare_guard_dir >/dev/null"; then
  :
else
  fail 'failed to initialize shared guard directory fixture'
fi

parallel_task() {
  local output_path="$1"
  cat <<EOF
Team: mde-domain-team
Subagent: validation-agent
Date: 2026-03-15
Domain: python-pixi-uv
Domain name: Python Pixi UV
Domain team id: mde-python-pixi-uv-domain-team
Reference source group: python-pixi-uv
Preset ids: preset-python-pixi-uv
Learning record id: domain-python-pixi-uv
Bundle path: configs/tool-bundles/python-pixi-uv
Objective: Parallel guard reuse verification
Prompt template: prompts/agent-team/mde-domain-sdlc/validation-agent.md
Output file: $output_path
EOF
}

parallel_fail=0
parallel_pids=()
for idx in 1 2 3; do
  output_file="$parallel_dir/parallel-$idx.md"
  log_file="$parallel_dir/parallel-$idx.log"
  env \
    MDE_AGENT_RUNNER_MODE=local-synth \
    MDE_AGENT_PREFLIGHT_PASSED=1 \
    MDE_GUARD_DIR="$shared_guard_dir" \
    bash "$ROOT_DIR/scripts/agent-runner.sh" "$(parallel_task "$output_file")" >"$log_file" 2>&1 &
  parallel_pids+=("$!")
done

for pid in "${parallel_pids[@]}"; do
  if ! wait "$pid"; then
    parallel_fail=1
  fi
done

if (( parallel_fail == 0 )) && ! rg -q 'File exists' "$parallel_dir"/parallel-*.log; then
  pass 'shared guard directory reuse is safe under parallel agent-runner execution'
else
  fail 'parallel agent-runner execution still hits shared guard directory races'
fi

python3 - "$tmp_dir/presets.json" <<'PY'
import json
import sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as fh:
    data = json.load(fh)
data['presets'][0]['domain_ids'] = []
with open(path, 'w', encoding='utf-8') as fh:
    json.dump(data, fh)
PY

if env "${common_env[@]}" bash "$PRESET_VERIFY" python-tooling >/dev/null 2>&1; then
  fail 'preset verify should fail when preset coverage is removed'
else
  pass 'preset verify fails when preset coverage is removed'
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
