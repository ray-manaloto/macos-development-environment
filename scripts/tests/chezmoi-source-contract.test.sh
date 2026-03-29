#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_DIR="$ROOT_DIR/home"

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

CHEZMOI_TOML="$SOURCE_DIR/.chezmoi.toml.tmpl"
MISE_EXTERNAL="$SOURCE_DIR/.chezmoiexternals/mise.toml.tmpl"
MISE_HOOK="$SOURCE_DIR/.chezmoiscripts/run_onchange_after_install_mise.sh.tmpl"

[[ -f "$CHEZMOI_TOML" ]] || fail "missing chezmoi source config"
[[ -f "$MISE_EXTERNAL" ]] || fail "missing mise external bootstrap"
[[ -f "$MISE_HOOK" ]] || fail "missing mise install lifecycle hook"
pass "chezmoi source bootstrap files exist"

grep -q '^sourceDir =' "$CHEZMOI_TOML" || fail "chezmoi source config missing sourceDir"
grep -q '\[data\]' "$CHEZMOI_TOML" || fail "chezmoi source config missing data section"
pass "chezmoi source config exports sourceDir and data"

grep -q 'mise-latest-' "$MISE_EXTERNAL" || fail "mise external does not bootstrap mise binary"
grep -q '"\.local/bin/mise"' "$MISE_EXTERNAL" || fail "mise external bootstrap path changed unexpectedly"
pass "mise external bootstraps managed mise binary"

grep -q '"\$MISE_BIN_PATH" install' "$MISE_HOOK" || fail "mise lifecycle hook missing install step"
grep -q '"\$MISE_BIN_PATH" trust' "$MISE_HOOK" || fail "mise lifecycle hook missing trust step"
grep -q 'joinPath .chezmoi.sourceDir ".."' "$MISE_HOOK" || fail "mise lifecycle hook does not anchor to repo root"
pass "mise lifecycle hook installs from repo root"
