#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

REGISTRY="configs/mde-guidance-quarantine.json"
TOOL_AUDIT_README="docs/tool-audit/README.md"
MISE_PARALLEL_README="reports/mise-parallel-2026-03-09/README.md"

echo "=== Guidance Quarantine Contract Tests ==="

if [[ -s "$REGISTRY" ]]; then
  pass "guidance quarantine registry exists"
else
  fail "guidance quarantine registry missing"
fi

if python3 -c '
import json, pathlib, sys
root = pathlib.Path(".")
data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
items = data.get("quarantined_paths", [])
assert items
for item in items:
    rel = item["path"]
    assert rel.startswith("docs/") or rel.startswith("reports/")
    assert (root / rel).is_file(), rel
    assert item["disposition"] in {"quarantined", "historical-only", "exclude-from-active-guidance"}
    assert item["replacement_guidance"]
' "$REGISTRY" >/dev/null; then
  pass "registry entries are well-formed and point at real docs/report files"
else
  fail "registry entries are missing required quarantine metadata"
fi

if [[ -s "$TOOL_AUDIT_README" ]] && rg -q 'historical|not active guidance|toolchain-precedence' "$TOOL_AUDIT_README"; then
  pass "tool-audit directory is explicitly marked historical"
else
  fail "tool-audit directory is missing a historical guidance marker"
fi

if [[ -s "$MISE_PARALLEL_README" ]] && rg -q 'historical|not active guidance|toolchain-precedence' "$MISE_PARALLEL_README"; then
  pass "mise-parallel report directory is explicitly marked historical"
else
  fail "mise-parallel report directory is missing a historical guidance marker"
fi

if python3 -c '
import json, pathlib, sys
root = pathlib.Path(".")
patterns = (
    "brew install mise",
    "curl https://mise.run | sh",
    "curl https://mise.run/zsh | sh",
    "auto_install = true",
    "uv tool install",
    "bun add -g",
)
data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
items = data.get("quarantined_paths", [])
assert items
for item in items:
    text = (root / item["path"]).read_text(encoding="utf-8")
    assert any(pattern in text for pattern in patterns), item["path"]
' "$REGISTRY" >/dev/null; then
  pass "quarantined artifacts are backed by explicit legacy-guidance evidence"
else
  fail "one or more quarantined artifacts do not contain the expected stale-guidance evidence"
fi

echo
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
