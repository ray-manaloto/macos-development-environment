#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=scripts/lib/mde-platform.sh
source "$ROOT_DIR/scripts/lib/mde-platform.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

assert_eq() {
  local got="$1" expected="$2" msg="$3"
  if [[ "$got" == "$expected" ]]; then
    pass "$msg"
  else
    fail "$msg (got=$got expected=$expected)"
  fi
}

assert_eq "$(MDE_PLATFORM=macos mde_detect_platform)" "macos" "explicit macos override"
assert_eq "$(MDE_PLATFORM=devcontainer mde_detect_platform)" "devcontainer" "explicit devcontainer override"
assert_eq "$(MDE_PLATFORM=linux mde_detect_platform)" "linux" "explicit linux override"

assert_eq "$(DEVCONTAINER=1 MDE_PLATFORM='' mde_detect_platform)" "devcontainer" "DEVCONTAINER marker"
assert_eq "$(CODESPACES=1 MDE_PLATFORM='' mde_detect_platform)" "devcontainer" "CODESPACES marker"

if [[ -f /.dockerenv ]]; then
  assert_eq "$(MDE_PLATFORM='' DEVCONTAINER='' CODESPACES='' mde_detect_platform)" "linux" "plain /.dockerenv is linux, not devcontainer"
else
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT

  cat > "$tmp_dir/uname" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' Darwin
EOF
  chmod +x "$tmp_dir/uname"
  assert_eq "$(PATH="$tmp_dir:$PATH" MDE_PLATFORM='' DEVCONTAINER='' CODESPACES='' mde_detect_platform)" "macos" "uname Darwin fallback"

  cat > "$tmp_dir/uname" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' Linux
EOF
  chmod +x "$tmp_dir/uname"
  assert_eq "$(PATH="$tmp_dir:$PATH" MDE_PLATFORM='' DEVCONTAINER='' CODESPACES='' mde_detect_platform)" "linux" "uname Linux fallback"
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
