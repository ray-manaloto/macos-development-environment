#!/usr/bin/env bash
set -euo pipefail

DATE_STAMP="${1:-${MDE_UPDATE_REMEDIATION_DATE:-$(date +%F)}}"
OUT_DIR="${2:-${MDE_UPDATE_REMEDIATION_OUT_DIR:-reports/mde-update-remediation}}"
ITEM_ID_INPUT="${3:-${MDE_UPDATE_REMEDIATION_ITEM_ID:-mde:update}}"
EVIDENCE_INPUT="${4:-${MDE_UPDATE_REMEDIATION_EVIDENCE_PATH:-mde-update-results.20260213.log}}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ "$ITEM_ID_INPUT" = /* || "$ITEM_ID_INPUT" == *.log || -f "$ITEM_ID_INPUT" ]]; then
  ITEM_ID="mde:update"
  EVIDENCE_INPUT="$ITEM_ID_INPUT"
else
  ITEM_ID="$ITEM_ID_INPUT"
fi

if [[ "$EVIDENCE_INPUT" = /* ]]; then
  EVIDENCE_PATH="$EVIDENCE_INPUT"
else
  EVIDENCE_PATH="$ROOT_DIR/$EVIDENCE_INPUT"
fi

EVIDENCE_BASENAME="$(basename "$EVIDENCE_PATH")"
ERROR_REGEX='^error:|mise ERROR|ERROR task failed|Install completed with failures'
fail=0

required_files=(
  "$OUT_DIR/${DATE_STAMP}-01-log-triage.md"
  "$OUT_DIR/${DATE_STAMP}-02-maintenance-remediation.md"
  "$OUT_DIR/${DATE_STAMP}-03-parity-sync.md"
  "$OUT_DIR/${DATE_STAMP}-04-validation.md"
  "docs/plans/${DATE_STAMP}-mde-update-remediation-spec.md"
  "docs/plans/${DATE_STAMP}-mde-update-remediation-plan.md"
)

for f in "${required_files[@]}"; do
  if [[ ! -s "$f" ]]; then
    echo "FAIL: missing or empty file: $f"
    fail=1
  else
    echo "OK: $f"
  fi
done

bad_patterns='^\s*TODO\b|\bTBD\b|lorem ipsum|Task captured|Agent Runner Output|No specialized handler configured yet'
for f in "${required_files[@]}"; do
  if [[ -s "$f" ]] && rg -qi "$bad_patterns" "$f"; then
    echo "FAIL: placeholder/mock-like content detected in $f"
    fail=1
  fi
done

require_pattern() {
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

if [[ -s "$OUT_DIR/${DATE_STAMP}-01-log-triage.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-01-log-triage.md" "$ITEM_ID|$EVIDENCE_BASENAME|matrix|ownership|mise" 'triage output covers the active target and evidence'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-02-maintenance-remediation.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-02-maintenance-remediation.md" 'mde-modernization-matrix\.json|mde-tool-ownership\.json|macos-dev-maintenance\.sh|install-agent-stack\.sh|install-langchain-cli-tools\.sh' 'maintenance remediation output covers owning contract surfaces'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-03-parity-sync.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-03-parity-sync.md" 'devcontainer|macOS|MDE_PLATFORM|health-check|verify-all' 'parity sync output covers native and devcontainer contracts'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-04-validation.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-04-validation.md" "$ITEM_ID|$EVIDENCE_BASENAME|mde:verify|devcontainer-image-smoke|run-all\.sh|proof command|success criterion" 'validation output covers proof commands and acceptance'
fi
if [[ -s "docs/plans/${DATE_STAMP}-mde-update-remediation-spec.md" ]]; then
  require_pattern "docs/plans/${DATE_STAMP}-mde-update-remediation-spec.md" 'Goals|Non-Goals|Acceptance Criteria|devcontainer|proof command|success criterion' 'spec covers scope and acceptance'
fi
if [[ -s "docs/plans/${DATE_STAMP}-mde-update-remediation-plan.md" ]]; then
  require_pattern "docs/plans/${DATE_STAMP}-mde-update-remediation-plan.md" 'Phase|proof|parity|next steps|success criterion' 'plan covers sequencing and parity workstream'
fi

if [[ "$ITEM_ID" == "mde:update" && -f "$EVIDENCE_PATH" ]]; then
  if rg -q -e "$ERROR_REGEX" "$EVIDENCE_PATH"; then
    echo "FAIL: latest log still contains updater error lines: $EVIDENCE_PATH"
    fail=1
  else
    echo "OK: latest log is clean: $EVIDENCE_PATH"
  fi
fi

if (( fail != 0 )); then
  echo "VALIDATION: FAILED"
  exit 1
fi

echo "VALIDATION: PASSED"
