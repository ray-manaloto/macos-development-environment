#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASKS_FILE="$ROOT_DIR/.mise.toml"
RUNNER_FILE="$ROOT_DIR/scripts/teams/run-modern-best-practices-upgrade-team.sh"

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

rg -q '^\[tasks\."mde:team:modern-best-practices"\]' "$TASKS_FILE" || fail "missing mise modernization team task"
pass "mise modernization team task exists"

[[ -f "$RUNNER_FILE" ]] || fail "missing modernization team runner"
pass "modernization team runner exists"

rg -q 'run-mde-domain-team\.sh' "$RUNNER_FILE" || fail "runner does not invoke domain team orchestration"
rg -q 'run-devcontainer-setup-sdlc-team\.sh' "$RUNNER_FILE" || fail "runner does not invoke devcontainer SDLC orchestration"
pass "runner invokes domain and devcontainer SDLC teams"

rg -q 'mise-core,shell-editor' "$RUNNER_FILE" || fail "runner default modernization domains changed unexpectedly"
rg -q 'summary\.md' "$RUNNER_FILE" || fail "runner does not publish consolidated summary output"
pass "runner publishes expected default scope and summary output"

rg -q 'mde-agent-preflight\.sh' "$RUNNER_FILE" || fail "runner missing agent preflight guard"
pass "runner enforces agent preflight before orchestration"
