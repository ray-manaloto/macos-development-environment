#!/usr/bin/env bash
set -euo pipefail

DATE_STAMP="${1:-$(date +%F)}"
OUT_DIR="${2:-reports/mde-domain-sdlc}"
DOMAIN="${3:-${MDE_ACTIVE_DOMAIN:-}}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ -z "$DOMAIN" ]]; then
  echo "Domain is required." >&2
  exit 2
fi

fail=0
required_files=(
  "$OUT_DIR/${DATE_STAMP}-01-mirror-refresh.md"
  "$OUT_DIR/${DATE_STAMP}-02-docs-tutorial.md"
  "$OUT_DIR/${DATE_STAMP}-03-repo-mining.md"
  "$OUT_DIR/${DATE_STAMP}-04-social-signal.md"
  "$OUT_DIR/${DATE_STAMP}-05-authority.md"
  "$OUT_DIR/${DATE_STAMP}-06-implementation.md"
  "$OUT_DIR/${DATE_STAMP}-07-validation.md"
  "$OUT_DIR/${DATE_STAMP}-08-learning.md"
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

require_pattern "$OUT_DIR/${DATE_STAMP}-01-mirror-refresh.md" 'mirror|reference source|domain classification' 'mirror-refresh output covers mirrored sources and domain classification'
require_pattern "$OUT_DIR/${DATE_STAMP}-05-authority.md" 'domain classification|delegate|delegation|reference source|preset|learning registry' 'authority output covers domain delegation markers and catalog inputs'
require_pattern "$OUT_DIR/${DATE_STAMP}-06-implementation.md" 'preset|bundle|starter|delegate|delegation' 'implementation output covers preset scaffolding and delegation'
require_pattern "$OUT_DIR/${DATE_STAMP}-07-validation.md" 'proof|verify|acceptance|mde:refs:verify|mde:preset:verify|mde:domain:verify|mde:learn:verify|delegat' 'validation output covers proof commands and domain delegation markers'
require_pattern "$OUT_DIR/${DATE_STAMP}-08-learning.md" 'learning registry|affected prompts|affected skills|affected docs|affected tasks|adopted|deferred|rejected|delegat' 'learning output covers learning registry writeback surfaces'

MDE_REQUIRE_REFERENCE_MIRROR=1 "$ROOT_DIR/scripts/mde-refs-verify.sh" "$DOMAIN"
"$ROOT_DIR/scripts/mde-preset-verify.sh" "$DOMAIN"
"$ROOT_DIR/scripts/mde-domain-verify.sh" "$DOMAIN"
"$ROOT_DIR/scripts/mde-learn-verify.sh" "$DOMAIN"

if (( fail != 0 )); then
  echo 'VALIDATION: FAILED'
  exit 1
fi

echo 'VALIDATION: PASSED'
