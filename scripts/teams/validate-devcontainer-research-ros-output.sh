#!/usr/bin/env bash
set -euo pipefail

DATE_STAMP="${1:-${ROS_TEAM_DATE:-$(date +%F)}}"
OUT_DIR="${2:-${ROS_TEAM_OUT_DIR:-reports/research-ros}}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

fail=0

required_files=(
  "${OUT_DIR}/${DATE_STAMP}-phase-a-candidates.md"
  "${OUT_DIR}/${DATE_STAMP}-phase-b-repo-mining.md"
  "${OUT_DIR}/${DATE_STAMP}-phase-c-social-signals.md"
  "${OUT_DIR}/${DATE_STAMP}-phase-d-validation-mapping.md"
  "${OUT_DIR}/${DATE_STAMP}-discovery-records.jsonl"
  "${OUT_DIR}/${DATE_STAMP}-pattern-records.jsonl"
  "${OUT_DIR}/${DATE_STAMP}-social-pattern-records.jsonl"
  "${OUT_DIR}/${DATE_STAMP}-decision-records.jsonl"
  "${OUT_DIR}/${DATE_STAMP}-acceptance-records.jsonl"
  "${OUT_DIR}/${DATE_STAMP}-research-bundle.json"
  "docs/plans/${DATE_STAMP}-devcontainer-research-ros-spec.md"
)

for f in "${required_files[@]}"; do
  if [[ ! -s "$f" ]]; then
    echo "FAIL: missing or empty file: $f"
    fail=1
  else
    echo "OK: $f"
  fi
done

if (( fail == 0 )); then
  bad_patterns='Agent Runner Output|Captured Task|Task captured|TODO|TBD|lorem ipsum|mock|stub|placeholder'
  for f in "${required_files[@]}"; do
    if rg -qi "$bad_patterns" "$f"; then
      echo "FAIL: placeholder/mock-like content detected in $f"
      fail=1
    fi
  done
fi

jsonl_has_required_keys() {
  local file="$1"
  local jq_expr="$2"
  if jq -e -R 'fromjson?' "$file" >/dev/null 2>&1; then
    if jq -e -s "$jq_expr" "$file" >/dev/null; then
      return 0
    fi
  fi
  return 1
}

if (( fail == 0 )); then
  jsonl_has_required_keys "${OUT_DIR}/${DATE_STAMP}-discovery-records.jsonl" 'all(.[]; has("source") and has("source_class") and has("query") and has("url") and has("hit_count") and has("shortlist_reason"))' \
    && echo "OK: discovery schema minimum" \
    || { echo "FAIL: discovery schema minimum"; fail=1; }

  jsonl_has_required_keys "${OUT_DIR}/${DATE_STAMP}-pattern-records.jsonl" 'all(.[]; has("repo_or_url") and has("pattern_category") and has("proof") and has("confidence") and has("portability_risk") and has("recommendation"))' \
    && echo "OK: repo pattern schema minimum" \
    || { echo "FAIL: repo pattern schema minimum"; fail=1; }

  jsonl_has_required_keys "${OUT_DIR}/${DATE_STAMP}-social-pattern-records.jsonl" 'all(.[]; has("repo_or_url") and has("pattern_category") and has("proof") and has("confidence") and has("portability_risk") and has("recommendation"))' \
    && echo "OK: social pattern schema minimum" \
    || { echo "FAIL: social pattern schema minimum"; fail=1; }

  jsonl_has_required_keys "${OUT_DIR}/${DATE_STAMP}-decision-records.jsonl" 'all(.[]; has("decision") and has("rationale") and has("migration_cost") and has("enforcement_impact") and has("evidence"))' \
    && echo "OK: decision schema minimum" \
    || { echo "FAIL: decision schema minimum"; fail=1; }

  jsonl_has_required_keys "${OUT_DIR}/${DATE_STAMP}-acceptance-records.jsonl" 'all(.[]; has("criterion") and has("proof_command") and has("expected_signal") and has("status"))' \
    && echo "OK: acceptance schema minimum" \
    || { echo "FAIL: acceptance schema minimum"; fail=1; }
fi

if (( fail == 0 )); then
  jq -e -R 'fromjson?' "${OUT_DIR}/${DATE_STAMP}-discovery-records.jsonl" >/dev/null 2>&1 || { echo "FAIL: discovery jsonl parse"; fail=1; }
  jq -e -s 'all(.[]; (.query | type == "string") and (.query | length > 12))' "${OUT_DIR}/${DATE_STAMP}-discovery-records.jsonl" >/dev/null \
    && echo "OK: discovery query logging quality" \
    || { echo "FAIL: discovery query logging quality"; fail=1; }
  jq -e -s 'all(.[]; (.url | type == "string") and (.url | startswith("http")))' "${OUT_DIR}/${DATE_STAMP}-discovery-records.jsonl" >/dev/null \
    && echo "OK: discovery proof links present" \
    || { echo "FAIL: discovery proof links present"; fail=1; }

  jq -e -s 'all(.[]; (.proof | type == "string") and (.proof | length > 10))' "${OUT_DIR}/${DATE_STAMP}-pattern-records.jsonl" >/dev/null \
    && echo "OK: repo pattern proof quality" \
    || { echo "FAIL: repo pattern proof quality"; fail=1; }

  jq -e -s 'all(.[]; (.proof | type == "string") and (.proof | length > 10))' "${OUT_DIR}/${DATE_STAMP}-social-pattern-records.jsonl" >/dev/null \
    && echo "OK: social pattern proof quality" \
    || { echo "FAIL: social pattern proof quality"; fail=1; }

  jq -e -s 'all(.[]; (.evidence | type == "array") and ((.evidence | length) > 0))' "${OUT_DIR}/${DATE_STAMP}-decision-records.jsonl" >/dev/null \
    && echo "OK: decision evidence arrays present" \
    || { echo "FAIL: decision evidence arrays present"; fail=1; }
fi

if (( fail == 0 )); then
  bundle="${OUT_DIR}/${DATE_STAMP}-research-bundle.json"
  jq -e '.summary.source_classes | length >= 3' "$bundle" >/dev/null \
    && echo "OK: source class threshold" \
    || { echo "FAIL: source class threshold"; fail=1; }

  jq -e '.summary.repository_count >= 10' "$bundle" >/dev/null \
    && echo "OK: repository threshold" \
    || { echo "FAIL: repository threshold"; fail=1; }

  jq -e '.summary.non_repo_artifact_count >= 20' "$bundle" >/dev/null \
    && echo "OK: non-repo artifact threshold" \
    || { echo "FAIL: non-repo artifact threshold"; fail=1; }

  jq -e '(.decision_records | length > 0) and (.acceptance_records | length > 0)' "$bundle" >/dev/null \
    && echo "OK: bundle decision/acceptance records" \
    || { echo "FAIL: bundle decision/acceptance records"; fail=1; }
fi

if (( fail != 0 )); then
  echo "VALIDATION: FAILED"
  exit 1
fi

echo "VALIDATION: PASSED"
