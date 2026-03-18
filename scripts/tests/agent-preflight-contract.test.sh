#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PREFLIGHT="$ROOT_DIR/scripts/mde-agent-preflight.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
home_dir="$tmp_dir/home"
config_dir="$home_dir/.config/mise"
bin_dir="$home_dir/.local/share/mise/bin"
shims_dir="$home_dir/.local/share/mise/shims"
mkdir -p "$config_dir" "$shims_dir" "$bin_dir"

cat > "$config_dir/config.toml" <<'CFG'
[tools]
python = '3.12'
node = '20'
bun = '1'
go = '1.22'
uv = 'latest'
pixi = 'latest'
codex = 'latest'
devcontainer = 'latest'
CFG

cat > "$shims_dir/mise" <<'SCRIPT'
#!/usr/bin/env bash
case "${1:-}" in
  trust) exit 0 ;;
  *) exit 0 ;;
esac
SCRIPT
chmod +x "$shims_dir/mise"
cp "$shims_dir/mise" "$bin_dir/mise"

for cmd in python node bun go uv pixi codex devcontainer rustc; do
  cat > "$shims_dir/$cmd" <<'SCRIPT'
#!/usr/bin/env bash
exit 0
SCRIPT
  chmod +x "$shims_dir/$cmd"
done

actual_python3="$(env -i PATH=/usr/bin:/bin /bin/sh -c 'command -v python3')"
ln -s "$actual_python3" "$shims_dir/python3"

set +e
pass_output="$(env -i HOME="$home_dir" PATH="$shims_dir:$bin_dir:/usr/bin:/bin" "$PREFLIGHT" --quiet 2>&1)"
pass_status=$?
set -e
if (( pass_status == 0 )); then
  pass 'preflight passes when required skills, config, and managed commands are present'
else
  fail "expected preflight success (exit=$pass_status output=$pass_output)"
fi

python3 - "$ROOT_DIR/configs/mde-skill-registry.json" "$tmp_dir/skill-registry-missing-contract.json" <<'PY'
import json
import sys
src, dst = sys.argv[1:3]
with open(src, 'r', encoding='utf-8') as fh:
    data = json.load(fh)
data['skills'] = [item for item in data.get('skills', []) if item.get('id') != 'skills/mde-agent-runtime-contract']
with open(dst, 'w', encoding='utf-8') as fh:
    json.dump(data, fh)
PY

set +e
fail_output="$(env -i HOME="$home_dir" PATH="$shims_dir:$bin_dir:/usr/bin:/bin" MDE_SKILL_REGISTRY_FILE="$tmp_dir/skill-registry-missing-contract.json" "$PREFLIGHT" --quiet 2>&1)"
fail_status=$?
set -e
if (( fail_status != 0 )) && printf '%s' "$fail_output" | grep -q 'mde-agent-runtime-contract'; then
  pass 'preflight fails when the required runtime contract skill is missing from the registry'
else
  fail "expected preflight failure for missing runtime contract skill (exit=$fail_status output=$fail_output)"
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
