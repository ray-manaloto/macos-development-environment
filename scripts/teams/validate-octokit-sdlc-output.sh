#!/usr/bin/env bash
set -euo pipefail

DATE_STAMP="${1:-${OCTOKIT_TEAM_DATE:-$(date +%F)}}"
OUT_DIR="${2:-${OCTOKIT_TEAM_OUT_DIR:-reports/octokit-sdlc}}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

fail=0

required_files=(
  "docs/plans/${DATE_STAMP}-octokit-sdlc-spec-plan.md"
  "docs/plans/${DATE_STAMP}-octokit-sdlc-spec-review.md"
  "docs/plans/${DATE_STAMP}-octokit-sdlc-test-design.md"
  "${OUT_DIR}/coding-agent.log"
  "${OUT_DIR}/qa-functional.md"
  "${OUT_DIR}/qa-nonfunctional.md"
  "${OUT_DIR}/docs-validation.md"
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
  bad_patterns='Agent Runner Output|Captured Task|Task captured'
  for f in "${required_files[@]}"; do
    if rg -q "$bad_patterns" "$f"; then
      echo "FAIL: placeholder content detected in $f"
      fail=1
    fi
  done
fi

check_contains() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if rg -q "$pattern" "$file"; then
    echo "OK: $label"
  else
    echo "FAIL: $label"
    fail=1
  fi
}

if (( fail == 0 )); then
  check_contains "docs/plans/${DATE_STAMP}-octokit-sdlc-spec-plan.md" "Implementation Plan" "spec plan marker"
  check_contains "docs/plans/${DATE_STAMP}-octokit-sdlc-spec-review.md" "Findings" "spec review marker"
  check_contains "docs/plans/${DATE_STAMP}-octokit-sdlc-test-design.md" "Feature:" "bdd marker"
  check_contains "${OUT_DIR}/coding-agent.log" "Implementation Summary" "coding marker"
  check_contains "${OUT_DIR}/qa-functional.md" "Functional Validation" "qa functional marker"
  check_contains "${OUT_DIR}/qa-nonfunctional.md" "Non-Functional Validation" "qa nonfunctional marker"
  check_contains "${OUT_DIR}/docs-validation.md" "Documentation Validation" "docs marker"
fi

subagent_logs=(reports/multi-agent/subagent-*.log)
if [[ ! -e "${subagent_logs[0]}" ]]; then
  echo "FAIL: no subagent logs found in reports/multi-agent"
  fail=1
else
  count="$(ls -1 reports/multi-agent/subagent-*.log | wc -l | tr -d ' ')"
  echo "INFO: subagent logs found: ${count}"
  if [[ "$count" -lt 7 ]]; then
    echo "FAIL: expected at least 7 subagent logs"
    fail=1
  fi
fi

if (( fail != 0 )); then
  echo "VALIDATION: FAILED"
  exit 1
fi

echo "VALIDATION: PASSED"
