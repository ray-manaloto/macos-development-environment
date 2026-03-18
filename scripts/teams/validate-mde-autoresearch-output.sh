#!/usr/bin/env bash
set -euo pipefail

DATE_STAMP="${1:-$(date +%F)}"
OUT_DIR="${2:-reports/mde-autoresearch}"
DOMAIN="${3:-${MDE_ACTIVE_DOMAIN:-}}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

fail=0
required_files=(
  "$OUT_DIR/${DATE_STAMP}-01-scout.md"
  "$OUT_DIR/${DATE_STAMP}-discovery-records.jsonl"
  "$OUT_DIR/${DATE_STAMP}-02-repo-mining.md"
  "$OUT_DIR/${DATE_STAMP}-pattern-records.jsonl"
  "$OUT_DIR/${DATE_STAMP}-03-docs-tutorials.md"
  "$OUT_DIR/${DATE_STAMP}-04-social-signals.md"
  "$OUT_DIR/${DATE_STAMP}-social-pattern-records.jsonl"
  "$OUT_DIR/${DATE_STAMP}-05-tooling-eval.md"
  "$OUT_DIR/${DATE_STAMP}-06-tool-ownership.md"
  "$OUT_DIR/${DATE_STAMP}-07-runner-enforcement.md"
  "$OUT_DIR/${DATE_STAMP}-08-migration.md"
  "$OUT_DIR/${DATE_STAMP}-09-validation.md"
  "$OUT_DIR/${DATE_STAMP}-acceptance-records.jsonl"
  "$OUT_DIR/${DATE_STAMP}-10-synthesis.md"
  "$OUT_DIR/${DATE_STAMP}-decision-records.jsonl"
  "$OUT_DIR/${DATE_STAMP}-11-telemetry.md"
  "$OUT_DIR/${DATE_STAMP}-12-guidance.md"
  "$OUT_DIR/${DATE_STAMP}-summary.md"
)

for f in "${required_files[@]}"; do
  if [[ ! -s "$f" ]]; then
    echo "FAIL: missing or empty file: $f"
    fail=1
  else
    echo "OK: $f"
  fi
done

bad_patterns='^\s*TODO\b|\bTBD\b|placeholder|mock|stub|No specialized handler configured yet'
for f in "${required_files[@]}"; do
  if [[ -s "$f" ]] && rg -qi "$bad_patterns" "$f"; then
    echo "FAIL: placeholder-like content detected in $f"
    fail=1
  fi
done

require_pattern() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if rg -qi "$pattern" "$file"; then
    echo "OK: $label"
  else
    echo "FAIL: $label"
    fail=1
  fi
}

require_pattern "$OUT_DIR/${DATE_STAMP}-01-scout.md" 'domain classification|mde-domain-catalog\.json|reference source' 'scout output covers domain classification and source discovery'
require_pattern "$OUT_DIR/${DATE_STAMP}-05-tooling-eval.md" 'preset|mde-preset-catalog\.json|reference source group' 'tooling evaluation output covers preset coverage'
require_pattern "$OUT_DIR/${DATE_STAMP}-07-runner-enforcement.md" 'delegate|delegation|run-mde-domain-team\.sh|reports/mde-domain-sdlc' 'runner enforcement output covers domain delegation markers'
require_pattern "$OUT_DIR/${DATE_STAMP}-09-validation.md" 'delegate|delegation|proof|verify|mde:domain:verify|mde:learn:verify' 'validation output covers domain delegation and proof commands'
require_pattern "$OUT_DIR/${DATE_STAMP}-10-synthesis.md" 'domain classification|delegate|delegation|learning registry|mde-learning-registry\.json' 'synthesis output covers domain delegation and learning registry use'
require_pattern "$OUT_DIR/${DATE_STAMP}-12-guidance.md" 'preset|learning registry|delegate|delegation' 'guidance output covers preset and learning-registry markers'
require_pattern "$OUT_DIR/${DATE_STAMP}-summary.md" 'domain classification|delegate|delegation|learning registry' 'summary output covers domain classification and learning registry markers'

if [[ -n "$DOMAIN" ]]; then
  echo "INFO: validated autoresearch outputs for domain $DOMAIN"
fi

if (( fail != 0 )); then
  echo 'VALIDATION: FAILED'
  exit 1
fi

echo 'VALIDATION: PASSED'
