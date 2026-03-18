#!/usr/bin/env bash
set -euo pipefail

TASK="${1:-}"
if [[ -z "$TASK" ]]; then
  echo "Usage: $0 '<task-string>'" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install
if [[ "${MDE_AGENT_PREFLIGHT_PASSED:-0}" != "1" ]]; then
  "$REPO_ROOT/scripts/mde-agent-preflight.sh" --quiet >/dev/null
  export MDE_AGENT_PREFLIGHT_PASSED=1
fi
export MDE_AGENT_CONTEXT=1
if [[ -n "${MDE_GUARD_DIR:-}" && -d "${MDE_GUARD_DIR:-}" ]]; then
  export PATH="$MDE_GUARD_DIR:$PATH"
else
  mde_prepare_guard_dir >/dev/null
fi

OUT_DIR="${MULTI_AGENT_OUTPUT_DIR:-$REPO_ROOT/reports/multi-agent}"
mkdir -p "$OUT_DIR"

# Test/dev-only escape hatch for deterministic contract tests.
local_synth_output() {
  local task_text="$1"
  python3 - "$REPO_ROOT" <<'PY' "$task_text"
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
task = sys.argv[2]

def field(name: str) -> str:
    match = re.search(rf"^{re.escape(name)}: (.*)$", task, re.MULTILINE)
    return match.group(1).strip() if match else ""

def load_json(rel: str) -> dict:
    with (repo_root / rel).open("r", encoding="utf-8") as fh:
        return json.load(fh)

domain_id = field("Domain")
subagent_id = field("Subagent")
output_path = field("Output file")
date_stamp = field("Date")
domain_name = field("Domain name")
team_id = field("Domain team id")
reference_group_id = field("Reference source group") or field("Reference bundle id")
preset_ids_raw = field("Preset ids")
learning_record_id = field("Learning record id")
bundle_path = field("Bundle path") or field("Tool bundle dir")
project_authority = field("Project authority")
global_mode = field("Global CLI authority mode")
objective = field("Objective")

if not output_path:
    raise SystemExit("missing Output file in task payload")

domain_catalog = load_json("configs/mde-domain-catalog.json")
refs = load_json("configs/mde-reference-sources.json")
presets = load_json("configs/mde-preset-catalog.json")
learning_registry = load_json("configs/mde-learning-registry.json")

domain = next((item for item in domain_catalog["domains"] if item["id"] == domain_id), {})
source_group = next((item for item in refs["source_groups"] if item["id"] == reference_group_id or item["domain_id"] == domain_id), {})
source_ids = source_group.get("source_ids", [])
sources = {item["id"]: item for item in refs["sources"]}
source_lines = [
    f"- `{sid}`: {sources[sid].get('title', sid)} ({sources[sid].get('kind', 'unknown')})"
    for sid in source_ids if sid in sources
]
preset_ids = [item.strip() for item in preset_ids_raw.split(",") if item.strip()]
preset_rows = [item for item in presets["presets"] if item["id"] in preset_ids]
cookbook_pages = sorted({page for item in preset_rows for page in item.get("cookbook_pages", [])} | set(domain.get("cookbook_pages", [])))
cache_contract = ", ".join(domain.get("cache_contract", []))

header = [f"# {subagent_id}", "", f"- Date: `{date_stamp}`"]
if domain_id:
    header.append(f"- Domain: `{domain_id}`")
if domain_name or domain.get("name"):
    header.append(f"- Domain Name: {domain_name or domain.get('name', domain_id)}")
if team_id or domain.get("team_id"):
    header.append(f"- Domain Team: `{team_id or domain.get('team_id', '')}`")
header.extend([f"- Objective: {objective}", ""])

body: list[str]
if subagent_id == "mirror-refresh-agent":
    body = [
        "## Mirror Summary",
        f"- Reference source group: `{reference_group_id}`",
        f"- Bundle path: `{bundle_path or domain.get('bundle_path', '')}`",
        f"- Learning record: `{learning_record_id or domain.get('learning_record_id', '')}`",
        "- Mirror-first validation completed against the committed reference source catalog.",
        "- Curated external references are present alongside official and upstream sources.",
        "",
        "## Mirrored Sources",
        *source_lines,
        "",
        "## Freshness Disposition",
        "- No freshness gaps were identified in the committed mirror metadata during this run.",
    ]
elif subagent_id == "docs-tutorial-agent":
    cookbook_lines = [f"- Cookbook/doc page: {page}" for page in cookbook_pages] or ["- No cookbook pages declared."]
    body = [
        "## Official Coverage",
        *cookbook_lines,
        "",
        "## Guidance",
        f"- Project authority remains `{project_authority or domain.get('project_authority', '')}`.",
        f"- Global CLI authority mode remains `{global_mode or domain.get('global_cli_authority_mode', '')}`.",
    ]
elif subagent_id == "repo-mining-agent":
    body = [
        "## Upstream Patterns",
        *source_lines,
        "",
        "## Portability Notes",
        "- Repo-mining confirms the domain should continue to anchor on native project manifests plus mise-owned runtime entry points.",
    ]
elif subagent_id == "social-signal-agent":
    body = [
        "## Social Signal Disposition",
        "- Community references are treated as supporting evidence only.",
        "- No social signal overrides the official authority surfaces captured for this domain.",
    ]
elif subagent_id == "authority-agent":
    body = [
        "## Authority Contract",
        f"- Project authority: {project_authority or domain.get('project_authority', '')}",
        f"- Global CLI authority mode: {global_mode or domain.get('global_cli_authority_mode', '')}",
        f"- Cache contract: {cache_contract}",
        f"- Reference bundle: `{domain.get('reference_bundle_id', reference_group_id)}`",
        f"- Preset bundle: `{domain.get('preset_bundle_id', '')}`",
        "",
        "## Authority Surfaces",
        "- `pixi.toml`",
        "- `pyproject.toml`",
        "- `pixi-global.toml`",
        "- `mise`",
        "- `uv`",
    ]
elif subagent_id == "implementation-agent":
    starter_files = sorted({item for row in preset_rows for item in row.get("starter_files", [])})
    preset_lines = [f"- Preset: `{row['id']}` -> `{row.get('primary_bundle_path', '')}`" for row in preset_rows] or ["- No preset rows matched."]
    body = [
        "## Preset Scaffolding",
        *preset_lines,
        "",
        "## Starter Bundle",
        f"- Bundle path: `{bundle_path or domain.get('tool_bundle_dir', '')}`",
        *[f"- Starter file: `{item}`" for item in starter_files],
        "",
        "## Task Wiring",
        "- `mde:team:domain` remains the orchestration entry point for this domain.",
    ]
elif subagent_id == "validation-agent":
    body = [
        "## Proof Commands",
        f"- `mise run mde:team:domain -- --domain {domain_id}`",
        "- `mise run mde:refs:verify`",
        "- `mise run mde:preset:verify`",
        "- `mise run mde:domain:verify`",
        "- `mise run mde:learn:verify`",
        "",
        "## Acceptance",
        "- Acceptance requires mirror validation, preset coverage, domain contract validation, and learning writeback coverage.",
    ]
elif subagent_id == "sdlc-product-manager":
    body = [
        "## Product Requirements",
        "- Scope: modernize devcontainer setup so it aligns with the mise-first runtime contract and the repo-managed bootstrap policy.",
        "- Acceptance outcome: the devcontainer path remains reproducible, cache-aware, and validated by repo-owned commands.",
        "- Constraint: do not introduce unmanaged installers or bypass the exception registry.",
    ]
elif subagent_id == "sdlc-architect":
    body = [
        "## Architecture Design",
        "- Keep devcontainer bootstrap aligned with the same authority surfaces used on the host: `mise`, native manifests, and repo-owned validation tasks.",
        "- Prefer declarative config and image-layer changes over ad hoc shell bootstrap drift.",
        "- Route release and policy checks through the existing SDLC validators before adoption.",
    ]
elif subagent_id == "sdlc-implementation":
    body = [
        "## Implementation Plan",
        "- Update devcontainer build and bootstrap surfaces to match the current runtime contract and cache policy.",
        "- Verification command: `mise run mde:devcontainer:image:build`",
        "- Verify command: `mise run mde:devcontainer:image:smoke`",
        "- Verification command: `bash scripts/tests/devcontainer-bootstrap-contract.test.sh`",
    ]
elif subagent_id == "sdlc-functional-qa":
    body = [
        "## Functional QA",
        "- pass: bootstrap installs managed runtimes and repo-owned config without manual repair steps.",
        "- pass: container startup exposes the expected toolchain entrypoints through mise-managed paths.",
        "- fail condition: bootstrap depends on unmanaged installers or untracked shell drift.",
    ]
elif subagent_id == "sdlc-nonfunctional-qa":
    body = [
        "## Non-Functional QA",
        "- Reliability: preserve cache reuse and avoid cold-install defaults during repeated container starts.",
        "- Operability: keep smoke validation and image build commands as the canonical proof path.",
        "- Performance risk: repeated bootstrap work should stay inside cached image or package-manager layers.",
    ]
elif subagent_id == "sdlc-security":
    body = [
        "## Security Review",
        "- severity: medium",
        "- risk: unmanaged installer drift in the devcontainer can bypass the host runtime contract and create unreconciled tool state.",
        "- mitigation: keep bootstrap declarative, validate through repo-owned checks, and preserve exception-registry boundaries.",
    ]
elif subagent_id == "sdlc-devops":
    body = [
        "## DevOps Release",
        "- Release gate: run `mise run mde:devcontainer:image:build` before publishing image updates.",
        "- Release gate: run `mise run mde:devcontainer:image:smoke` plus the shell contract tests before merge.",
        "- Rollback: revert the devcontainer image/config change set and rebuild from the last passing baseline.",
    ]
elif subagent_id == "sdlc-docs":
    body = [
        "## Docs Handoff",
        "- Update `docs/devcontainer.md` when bootstrap, image build, or validation steps change.",
        "- Keep the handoff centered on execution order: build, smoke, shell/bootstrap checks, then adoption.",
        "- Feed accepted operational lessons back into the repo learning surfaces after verification.",
    ]
else:
    body = [
        "## Learning Registry Writeback",
        f"- Learning registry: `{learning_record_id or domain.get('learning_record_id', '')}`",
        "- Disposition: adopted",
        "- affected prompts: `prompts/agent-team/mde-domain-sdlc/*.md`",
        "- affected skills: `skills/mise-enforcement`, `skills/research-source-discovery`, `skills/github-repo-mining`, `skills/social-signal-mining`, `skills/evidence-synthesis`",
        "- affected docs: `docs/mise-config.md`, `docs/toolchain-precedence.md`, `docs/decision-log.md`",
        "- affected tasks: `mde:team:domain`, `mde:refs:refresh`, `mde:refs:verify`, `mde:preset:verify`, `mde:domain:verify`, `mde:learn:verify`",
        "- learning registry update is required before the run is considered complete.",
    ]

output = repo_root / output_path if not Path(output_path).is_absolute() else Path(output_path)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text("\n".join(header + body) + "\n", encoding="utf-8")
print(output)
PY
}

slug() {
  local s="$1"
  s="${s,,}"
  s="$(printf '%s' "$s" | tr -cs 'a-z0-9' '-')"
  s="${s#-}"
  s="${s%-}"
  printf '%s' "${s:0:80}"
}

task_hash() {
  if command -v shasum >/dev/null 2>&1; then
    printf '%s' "$TASK" | shasum -a 256 | awk '{print substr($1,1,12)}'
  else
    printf '%s' "$TASK" | cksum | awk '{print $1}'
  fi
}

TASK_SLUG="$(slug "$TASK")"
[[ -n "$TASK_SLUG" ]] || TASK_SLUG="task"
TASK_HASH="$(task_hash)"

REQUESTED_OUTPUTS=()
while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  REQUESTED_OUTPUTS+=("$path")
done < <(printf '%s\n' "$TASK" | sed -n 's/^Output file: //p')
REQUESTED_OUTPUT_FILE="${REQUESTED_OUTPUTS[0]:-}"

SUBAGENT_ID="$(printf '%s\n' "$TASK" | sed -n 's/^Subagent: //p' | head -n1)"
TASK_DATE="$(printf '%s\n' "$TASK" | sed -n 's/^Date: //p' | head -n1)"
TASK_OBJECTIVE="$(printf '%s\n' "$TASK" | sed -n 's/^Objective: //p' | head -n1)"
PROMPT_TEMPLATE="$(printf '%s\n' "$TASK" | sed -n 's/^Prompt template: //p' | head -n1)"

LOG_FILE="$OUT_DIR/${SUBAGENT_ID:-$TASK_SLUG}-${TASK_HASH}.log"

if [[ "${MDE_AGENT_RUNNER_MODE:-}" == "local-synth" ]]; then
  local_synth_output "$TASK" | tee "$LOG_FILE"
  exit 0
fi

if ! command -v codex >/dev/null 2>&1; then
  echo "codex CLI is required for real multi-agent execution but was not found in PATH." >&2
  exit 1
fi

resolve_rel() {
  local p="$1"
  if [[ -z "$p" ]]; then
    return 0
  fi
  if [[ "$p" == /* ]]; then
    printf '%s\n' "$p"
  else
    printf '%s/%s\n' "$REPO_ROOT" "$p"
  fi
}

output_matches_dir() {
  local output_path="$1"
  local dir_path="$2"
  local abs_output
  local abs_dir

  [[ -n "$output_path" && -n "$dir_path" ]] || return 1
  abs_output="$(resolve_rel "$output_path")"
  abs_dir="$(resolve_rel "$dir_path")"
  [[ "$output_path" == "$dir_path" || "$output_path" == "$dir_path/"* || "$abs_output" == "$abs_dir" || "$abs_output" == "$abs_dir/"* ]]
}

required_outputs_for_subagent() {
  local sid="$1"
  local date_stamp="$2"
  local primary_output="$3"
  local ros_out_dir="${ROS_TEAM_OUT_DIR:-reports/research-ros}"
  local oct_out_dir="${OCTOKIT_TEAM_OUT_DIR:-reports/octokit-sdlc}"
  local sdlc_out_dir="${DEVCONTAINER_SDLC_OUT_DIR:-reports/devcontainer-sdlc}"

  case "$sid" in
    scout-agent)
      if output_matches_dir "$primary_output" "$ros_out_dir"; then
        printf '%s\n' "$ros_out_dir/${date_stamp}-phase-a-candidates.md" "$ros_out_dir/${date_stamp}-discovery-records.jsonl"
      fi
      ;;
    repo-mining-agent)
      if output_matches_dir "$primary_output" "$ros_out_dir"; then
        printf '%s\n' "$ros_out_dir/${date_stamp}-phase-b-repo-mining.md" "$ros_out_dir/${date_stamp}-pattern-records.jsonl"
      fi
      ;;
    social-signal-agent)
      if output_matches_dir "$primary_output" "$ros_out_dir"; then
        printf '%s\n' "$ros_out_dir/${date_stamp}-phase-c-social-signals.md" "$ros_out_dir/${date_stamp}-social-pattern-records.jsonl"
      fi
      ;;
    validation-agent)
      if output_matches_dir "$primary_output" "$ros_out_dir"; then
        printf '%s\n' "$ros_out_dir/${date_stamp}-phase-d-validation-mapping.md" "$ros_out_dir/${date_stamp}-acceptance-records.jsonl"
      fi
      ;;
    synthesis-agent)
      if output_matches_dir "$primary_output" "$ros_out_dir"; then
        printf '%s\n' \
          "$ros_out_dir/${date_stamp}-decision-records.jsonl" \
          "$ros_out_dir/${date_stamp}-research-bundle.json" \
          "docs/plans/${date_stamp}-devcontainer-research-ros-spec.md"
      fi
      ;;
    spec-planner)
      if output_matches_dir "$primary_output" "$oct_out_dir"; then
        printf '%s\n' "docs/plans/${date_stamp}-octokit-sdlc-spec-plan.md"
      fi
      ;;
    spec-reviewer)
      if output_matches_dir "$primary_output" "$oct_out_dir"; then
        printf '%s\n' "docs/plans/${date_stamp}-octokit-sdlc-spec-review.md"
      fi
      ;;
    bdd-test-designer)
      if output_matches_dir "$primary_output" "$oct_out_dir"; then
        printf '%s\n' "docs/plans/${date_stamp}-octokit-sdlc-test-design.md"
      fi
      ;;
    coding-agent)
      if output_matches_dir "$primary_output" "$oct_out_dir"; then
        printf '%s\n' "$oct_out_dir/coding-agent.log"
      fi
      ;;
    qa-functional)
      if output_matches_dir "$primary_output" "$oct_out_dir"; then
        printf '%s\n' "$oct_out_dir/qa-functional.md"
      fi
      ;;
    qa-nonfunctional)
      if output_matches_dir "$primary_output" "$oct_out_dir"; then
        printf '%s\n' "$oct_out_dir/qa-nonfunctional.md"
      fi
      ;;
    docs-agent)
      if output_matches_dir "$primary_output" "$oct_out_dir"; then
        printf '%s\n' "$oct_out_dir/docs-validation.md"
      fi
      ;;
    sdlc-product-manager)
      if output_matches_dir "$primary_output" "$sdlc_out_dir"; then
        printf '%s\n' "$sdlc_out_dir/${date_stamp}-01-product-requirements.md"
      fi
      ;;
    sdlc-architect)
      if output_matches_dir "$primary_output" "$sdlc_out_dir"; then
        printf '%s\n' "$sdlc_out_dir/${date_stamp}-02-architecture-design.md"
      fi
      ;;
    sdlc-implementation)
      if output_matches_dir "$primary_output" "$sdlc_out_dir"; then
        printf '%s\n' "$sdlc_out_dir/${date_stamp}-03-implementation-plan.md"
      fi
      ;;
    sdlc-functional-qa)
      if output_matches_dir "$primary_output" "$sdlc_out_dir"; then
        printf '%s\n' "$sdlc_out_dir/${date_stamp}-04-functional-qa.md"
      fi
      ;;
    sdlc-nonfunctional-qa)
      if output_matches_dir "$primary_output" "$sdlc_out_dir"; then
        printf '%s\n' "$sdlc_out_dir/${date_stamp}-05-nonfunctional-qa.md"
      fi
      ;;
    sdlc-security)
      if output_matches_dir "$primary_output" "$sdlc_out_dir"; then
        printf '%s\n' "$sdlc_out_dir/${date_stamp}-06-security-review.md"
      fi
      ;;
    sdlc-devops)
      if output_matches_dir "$primary_output" "$sdlc_out_dir"; then
        printf '%s\n' "$sdlc_out_dir/${date_stamp}-07-devops-release.md"
      fi
      ;;
    sdlc-docs)
      if output_matches_dir "$primary_output" "$sdlc_out_dir"; then
        printf '%s\n' "$sdlc_out_dir/${date_stamp}-08-docs-handoff.md"
      fi
      ;;
  esac
}

DATE_STAMP="${TASK_DATE:-$(date +%F)}"
OUTPUTS=()
for path in "${REQUESTED_OUTPUTS[@]}"; do
  OUTPUTS+=("$path")
done
while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  OUTPUTS+=("$path")
done < <(required_outputs_for_subagent "$SUBAGENT_ID" "$DATE_STAMP" "$REQUESTED_OUTPUT_FILE")

if [[ "${#OUTPUTS[@]}" -gt 0 ]]; then
  deduped_outputs=()
  while IFS= read -r output_path; do
    [[ -n "$output_path" ]] || continue
    deduped_outputs+=("$output_path")
  done < <(printf '%s\n' "${OUTPUTS[@]}" | awk '!seen[$0]++')
  OUTPUTS=("${deduped_outputs[@]}")
fi

for rel in "${OUTPUTS[@]}"; do
  abs="$(resolve_rel "$rel")"
  mkdir -p "$(dirname "$abs")"
done

PROMPT_TEXT="$TASK"
PROMPT_TEXT+=$'\n\nMandatory runtime contract:\n'
PROMPT_TEXT+=$'- Load `skills/mde-agent-runtime-contract` before setup, installation, migration, automation, or research decisions.\n'
PROMPT_TEXT+=$'- Use `skills/mise-enforcement` for toolchain ownership changes and installation/update flows.\n'
PROMPT_TEXT+=$'- Load `skills/mde-package-cache-policy` for cache-aware setup, migration, and automation work.\n'
PROMPT_TEXT+=$'- Read `configs/mde-tool-ownership.json`, `configs/mde-modernization-matrix.json`, `configs/mde-install-exceptions.json`, `configs/mde-skill-registry.json`, `configs/mde-domain-catalog.json`, `configs/mde-reference-sources.json`, `configs/mde-preset-catalog.json`, and `configs/mde-learning-registry.json` as the source of truth.\n'
PROMPT_TEXT+=$'- Perform domain classification through `configs/mde-domain-catalog.json` and delegate domain-owned adoption or remediation decisions through the owning domain SDLC team before repo-wide guidance changes are accepted.\n'
PROMPT_TEXT+=$'- Global runtimes, global CLIs, and SDK CLIs belong to `mise`.\n'
PROMPT_TEXT+=$'- Repository libraries belong in native manifests, not global installers.\n'
PROMPT_TEXT+=$'- Reuse backend-native caches by default and do not force cold installs unless an explicit exception permits it.\n'
PROMPT_TEXT+=$'- Homebrew is exception-only and requires the explicit exception registry plus break-glass override.\n'
PROMPT_TEXT+=$'- Do not use unmanaged global install commands or curl-pipe installer flows; the runtime contract and command guard are authoritative.\n'
if [[ -n "$PROMPT_TEMPLATE" ]]; then
  PROMPT_PATH="$(resolve_rel "$PROMPT_TEMPLATE")"
  if [[ -f "$PROMPT_PATH" ]]; then
    PROMPT_TEXT+=$'\n\n---\nPrompt Template Content:\n'
    PROMPT_TEXT+="$(cat "$PROMPT_PATH")"
  fi
fi

if [[ "${#OUTPUTS[@]}" -gt 0 ]]; then
  PROMPT_TEXT+=$'\n\nRequired output files (must all be created and non-empty):\n'
  for rel in "${OUTPUTS[@]}"; do
    PROMPT_TEXT+="- $(resolve_rel "$rel")"$'\n'
  done
fi

PROMPT_TEXT+=$'\nExecution requirements:\n'
PROMPT_TEXT+=$'- Perform real implementation and real research; do not use stubs, mock data, placeholders, or canned text.\n'
PROMPT_TEXT+=$'- Use repository files, scripts, and available tools directly.\n'
PROMPT_TEXT+=$'- Include verifiable evidence links and executed proof commands where applicable.\n'
PROMPT_TEXT+=$'- Ensure all required output files are fully written before finishing.\n'
PROMPT_TEXT+=$'- Keep final response concise and include what was done.\n'
PROMPT_TEXT+=$'- If preflight or guardrails fail, stop and report the exact contract violation instead of working around it.\n'
if [[ "${SDLC_TEAM_IN_PROGRESS:-0}" == "1" ]]; then
  PROMPT_TEXT+=$'- SDLC team run is already in progress; do not invoke `scripts/teams/run-devcontainer-setup-sdlc-team.sh` or any nested team orchestrator.\n'
fi

{
  printf '[%s] Subagent=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "${SUBAGENT_ID:-unknown}"
  printf '[%s] Objective=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "${TASK_OBJECTIVE:-N/A}"
  printf '[%s] PromptTemplate=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "${PROMPT_TEMPLATE:-N/A}"
  printf '[%s] Running codex exec\n' "$(date '+%Y-%m-%d %H:%M:%S')"

  printf '%s\n' "$PROMPT_TEXT" | codex exec \
    --dangerously-bypass-approvals-and-sandbox \
    --cd "$REPO_ROOT" -
} >"$LOG_FILE" 2>&1

missing=0
for rel in "${OUTPUTS[@]}"; do
  abs="$(resolve_rel "$rel")"
  if [[ ! -s "$abs" ]]; then
    echo "Missing required output: $abs" >&2
    missing=1
  fi
done

if (( missing != 0 )); then
  echo "Runner completed but one or more required outputs are missing." >&2
  echo "See log: $LOG_FILE" >&2
  exit 1
fi

printf 'Wrote %s\n' "$LOG_FILE"
for rel in "${OUTPUTS[@]}"; do
  printf 'Wrote %s\n' "$(resolve_rel "$rel")"
done
