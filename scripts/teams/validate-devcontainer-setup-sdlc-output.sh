#!/usr/bin/env bash
set -euo pipefail

DATE_STAMP="${1:-${DEVCONTAINER_SDLC_DATE:-$(date +%F)}}"
OUT_DIR="${2:-${DEVCONTAINER_SDLC_OUT_DIR:-reports/devcontainer-sdlc}}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

fail=0

required_files=(
  "$OUT_DIR/${DATE_STAMP}-01-product-requirements.md"
  "$OUT_DIR/${DATE_STAMP}-02-architecture-design.md"
  "$OUT_DIR/${DATE_STAMP}-03-implementation-plan.md"
  "$OUT_DIR/${DATE_STAMP}-04-functional-qa.md"
  "$OUT_DIR/${DATE_STAMP}-05-nonfunctional-qa.md"
  "$OUT_DIR/${DATE_STAMP}-06-security-review.md"
  "$OUT_DIR/${DATE_STAMP}-07-devops-release.md"
  "$OUT_DIR/${DATE_STAMP}-08-docs-handoff.md"
)

for f in "${required_files[@]}"; do
  if [[ ! -s "$f" ]]; then
    echo "FAIL: missing or empty file: $f"
    fail=1
  else
    echo "OK: $f"
  fi
done

bad_patterns='^\s*TODO\b|\bTBD\b|lorem ipsum|Task captured|Agent Runner Output|Docs task captured|Review task captured|No specialized handler configured yet'
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

if [[ -s "$OUT_DIR/${DATE_STAMP}-03-implementation-plan.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-03-implementation-plan.md" 'verification|verify|command' 'implementation has verification commands'
  require_pattern "$OUT_DIR/${DATE_STAMP}-03-implementation-plan.md" 'devcontainer-image-build\.sh|devcontainer-image-smoke\.sh|devcontainer-lifecycle-smoke\.sh|devcontainer up|devcontainer exec' 'implementation references real devcontainer smoke commands'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-04-functional-qa.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-04-functional-qa.md" 'pass|fail' 'functional QA includes pass/fail outcomes'
  require_pattern "$OUT_DIR/${DATE_STAMP}-04-functional-qa.md" 'postCreateCommand|post-create|mde:verify|mde:drift|mde:status' 'functional QA includes lifecycle verification evidence'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-06-security-review.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-06-security-review.md" 'severity|risk|mitigation' 'security review includes ranked risk/mitigation'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-01-product-requirements.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-01-product-requirements.md" 'acceptance criteria|acceptance outcomes' 'product requirements include acceptance criteria'
  require_pattern "$OUT_DIR/${DATE_STAMP}-01-product-requirements.md" 'lifecycle smoke|image smoke|devcontainer up' 'product requirements include smoke validation scope'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-02-architecture-design.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-02-architecture-design.md" 'rio/dotfiles|samhvw8/dotfiles' 'architecture references both comparison repos'
  require_pattern "$OUT_DIR/${DATE_STAMP}-02-architecture-design.md" 'adopt|reject' 'architecture distinguishes adopted and rejected patterns'
  require_pattern "$OUT_DIR/${DATE_STAMP}-02-architecture-design.md" 'sign-off|approved|accept' 'architecture includes sign-off language'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-05-nonfunctional-qa.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-05-nonfunctional-qa.md" 'idempotence|idempotent|rerun' 'non-functional QA covers idempotence'
  require_pattern "$OUT_DIR/${DATE_STAMP}-05-nonfunctional-qa.md" 'amd64|arm64|platform' 'non-functional QA covers platform coverage'
  require_pattern "$OUT_DIR/${DATE_STAMP}-05-nonfunctional-qa.md" 'sign-off|approved|accept' 'non-functional QA includes sign-off language'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-06-security-review.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-06-security-review.md" 'sign-off|approved|accept' 'security review includes sign-off language'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-07-devops-release.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-07-devops-release.md" 'image smoke|lifecycle smoke|devcontainer-image-smoke|devcontainer-lifecycle-smoke' 'devops release covers both smoke lanes'
  require_pattern "$OUT_DIR/${DATE_STAMP}-07-devops-release.md" 'sign-off|approved|accept' 'devops release includes sign-off language'
fi
if [[ -s "$OUT_DIR/${DATE_STAMP}-08-docs-handoff.md" ]]; then
  require_pattern "$OUT_DIR/${DATE_STAMP}-08-docs-handoff.md" 'rio/dotfiles|samhvw8/dotfiles|adopt|reject' 'docs handoff captures reference decisions'
  require_pattern "$OUT_DIR/${DATE_STAMP}-08-docs-handoff.md" 'architecture sign-off|qa sign-off|security sign-off|devops sign-off|sign-off summary' 'docs handoff summarizes role sign-offs'
fi

if (( fail != 0 )); then
  echo "VALIDATION: FAILED"
  exit 1
fi

echo "VALIDATION: PASSED"
