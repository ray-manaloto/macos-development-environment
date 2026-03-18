#!/usr/bin/env bash
set -euo pipefail

DATE_STAMP="${1:-${DEVCONTAINER_IMAGE_RELEASE_DATE:-$(date +%F)}}"
OUT_DIR="${2:-${DEVCONTAINER_IMAGE_RELEASE_OUT_DIR:-reports/devcontainer-image-release}}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

fail=0

required_files=(
  "$OUT_DIR/${DATE_STAMP}-01-image-authoring.md"
  "$OUT_DIR/${DATE_STAMP}-02-gha-publish.md"
  "$OUT_DIR/${DATE_STAMP}-03-dependency-bot.md"
  "$OUT_DIR/${DATE_STAMP}-04-validation.md"
  "$OUT_DIR/${DATE_STAMP}-05-docs-handoff.md"
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

if [[ -s "$OUT_DIR/${DATE_STAMP}-01-image-authoring.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-01-image-authoring.md" 'Dockerfile|devcontainer\.json|digest|OCI' 'image authoring output covers Dockerfile and pin policy'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-02-gha-publish.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-02-gha-publish.md" 'GHCR|workflow|attest|multi-arch' 'publish output covers workflow and GHCR release contract'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-03-dependency-bot.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-03-dependency-bot.md" 'Dependabot|docker|github-actions' 'dependency output covers Dependabot policy'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-04-validation.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-04-validation.md" 'mde:devcontainer:image:build|mde:devcontainer:image:smoke|mde:verify' 'validation output covers local and hard-gate verification'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-05-docs-handoff.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-05-docs-handoff.md" 'rollback|main|sha-' 'docs handoff covers mutable and immutable tags'
fi

if (( fail != 0 )); then
  echo "VALIDATION: FAILED"
  exit 1
fi

echo "VALIDATION: PASSED"
