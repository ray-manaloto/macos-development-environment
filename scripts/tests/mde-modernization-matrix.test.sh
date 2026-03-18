#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

MATRIX="configs/mde-modernization-matrix.json"
GENERATOR="scripts/generate-modernization-matrix.sh"
PYTHON_GENERATOR="scripts/generate_modernization_matrix.py"
mkdir -p .artifacts/test-tmp
TMP_MATRIX=".artifacts/test-tmp/mde-modernization-matrix.$BASHPID.$RANDOM.json"
rm -f "$TMP_MATRIX"
trap 'rm -f "$TMP_MATRIX"' EXIT

echo "=== MDE Modernization Matrix Tests ==="

if [[ -s "$MATRIX" ]]; then
  pass "matrix file exists"
else
  fail "matrix file missing"
fi

if python3 - <<'PY' "$MATRIX" >/dev/null
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    data = json.load(fh)
assert data["policy"]["top_level_authority"] == "mise"
assert data["policy"]["cache_policy_defaults"]["reuse_caches_by_default"] is True
assert data["coverage"]["tasks_total"] >= 16
assert data["coverage"]["scripts_total"] >= 100
for item in data["global_tools"]:
    policy = item["cache_policy"]
    assert "package_manager_backend" in policy
    assert "cache_directory_or_source" in policy
PY
then
  pass "matrix parses and exposes expected top-level contract fields"
else
  fail "matrix does not parse or is missing expected fields"
fi

if [[ -x "$PYTHON_GENERATOR" ]]; then
  pass "python generator exists"
else
  fail "python generator missing"
fi

if ! rg -q "<<'PY'" "$GENERATOR"; then
  pass "shell shim no longer embeds Python"
else
  fail "shell shim still embeds Python"
fi

actual_scripts="$(find scripts -type f ! -path '*/__pycache__/*' | LC_ALL=C sort | wc -l | tr -d ' ')"
matrix_scripts="$(python3 - <<'PY' "$MATRIX"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    data = json.load(fh)
print(len(data["script_surfaces"]))
PY
)"
if [[ "$actual_scripts" == "$matrix_scripts" ]]; then
  pass "matrix covers every file in scripts/"
else
  fail "matrix script coverage mismatch: actual=$actual_scripts matrix=$matrix_scripts"
fi

actual_tasks="$(rg -n '^\[tasks\.' .mise.toml | wc -l | tr -d ' ')"
matrix_tasks="$(python3 - <<'PY' "$MATRIX"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    data = json.load(fh)
print(len(data["public_tasks"]))
PY
)"
if [[ "$actual_tasks" == "$matrix_tasks" ]]; then
  pass "matrix covers every public mise task"
else
  fail "matrix task coverage mismatch: actual=$actual_tasks matrix=$matrix_tasks"
fi

if python3 - <<'PY' "$MATRIX" >/dev/null
import json, sys
required_scripts = {
    "scripts/mde-refs-refresh.sh",
    "scripts/mde-refs-verify.sh",
    "scripts/mde-preset-verify.sh",
    "scripts/mde-domain-verify.sh",
    "scripts/mde-learn-verify.sh",
    "scripts/mde-sops-secrets-refresh.sh",
    "scripts/mde-sops-secrets-import-keychain.sh",
    "scripts/mde-sops-secrets-backup-1password.sh",
    "scripts/install-zsh-bench.sh",
    "scripts/teams/run-modern-best-practices-upgrade-team.sh",
    "scripts/teams/run-mde-domain-team.sh",
    "scripts/teams/validate-mde-domain-output.sh",
    "scripts/tests/chezmoi-source-contract.test.sh",
    "scripts/tests/chezmoi-template-parity.test.sh",
    "scripts/tests/remediation-policy-contract.test.sh",
    "scripts/tests/modern-best-practices-team-contract.test.sh",
}
required_tasks = {
    "mde:refs:refresh",
    "mde:refs:verify",
    "mde:preset:verify",
    "mde:domain:verify",
    "mde:learn:verify",
    "mde:team:domain",
    "mde:mcp:sync",
    "mde:agents:review",
    "mde:secrets:refresh",
    "mde:secrets:restore:keychain",
    "mde:secrets:backup:1password",
    "mde:shell:profile:install-bench",
    "mde:shell:profile:bench",
    "mde:team:modern-best-practices",
}
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)
script_paths = {item["path"] for item in data["script_surfaces"]}
task_ids = {item["id"] for item in data["public_tasks"]}
assert required_scripts.issubset(script_paths)
assert required_tasks.issubset(task_ids)
PY
then
  pass "matrix includes the new domain governance scripts and tasks"
else
  fail "matrix is missing one or more new domain governance scripts or tasks"
fi

removed_tool='notebooklm'"-"'mcp-cli'
if ! rg -q "$removed_tool" "$MATRIX" configs/mde-tool-ownership.json docs/tool-audit/mise-report.md mde-update-results.20260413.log; then
  pass "deprecated notebooklm MCP CLI is removed from tracked matrix and contract surfaces"
else
  fail "deprecated notebooklm MCP CLI still appears in tracked matrix or contract surfaces"
fi

"$GENERATOR" "$TMP_MATRIX"
if cmp -s "$MATRIX" "$TMP_MATRIX"; then
  pass "matrix is reproducible from the generator"
else
  fail "matrix is out of date with the generator output"
fi

echo
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
