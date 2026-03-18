#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT_DIR/scripts/profile-zsh-startup.sh"
INSTALL_SCRIPT="$ROOT_DIR/scripts/install-zsh-bench.sh"
TASKS_FILE="$ROOT_DIR/.mise.toml"
DOC="$ROOT_DIR/docs/terminal-startup-profiling.md"

PASS=0
FAIL=0
REAL_HOME="$HOME"

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

echo "=== Profile zsh startup tests ==="

if [[ -x "$SCRIPT" ]]; then
  pass "script exists"
else
  fail "missing executable script: $SCRIPT"
fi

if [[ -x "$INSTALL_SCRIPT" ]]; then
  pass "install script exists"
else
  fail "missing executable script: $INSTALL_SCRIPT"
fi

for task in \
  'mde:shell:profile' \
  'mde:shell:profile:baseline' \
  'mde:shell:profile:install-bench' \
  'mde:shell:profile:bench' \
  'mde:shell:profile:zprof' \
  'mde:shell:profile:xtrace' \
  'mde:shell:profile:syscalls'
do
  if rg -q "^\[tasks\.\"${task}\"\]" "$TASKS_FILE"; then
    pass "mise task exists: $task"
  else
    fail "missing mise task: $task"
  fi
done

if [[ -f "$DOC" ]]; then
  pass "documentation exists"
else
  fail "missing documentation: $DOC"
fi

if [[ -x "$SCRIPT" ]]; then
  if "$SCRIPT" help >/dev/null 2>&1; then
    pass "help subcommand runs"
  else
    fail "help subcommand failed"
  fi
fi

tmp_home="$ROOT_DIR/.artifacts/test-tmp/profile-zsh-home.$BASHPID.$RANDOM"
rm -rf "$tmp_home"
mkdir -p "$tmp_home/.oh-my-zsh-custom" "$tmp_home/.zprofile.d"
trap 'rm -rf "$tmp_home"' EXIT

cat > "$tmp_home/.zprofile" <<'EOF'
if [[ -f "$HOME/.zprofile.d/10-login-slow.zsh" ]]; then
  source "$HOME/.zprofile.d/10-login-slow.zsh"
fi
EOF

cat > "$tmp_home/.zprofile.d/10-login-slow.zsh" <<'EOF'
login_slow_fn() { sleep 0.01; }
login_slow_fn
EOF

cat > "$tmp_home/.zshrc" <<'EOF'
fpath=("$ZSH_CUSTOM/completions" $fpath)
export ZSH='"$REAL_HOME"'/.oh-my-zsh
export ZSH_CUSTOM="$HOME/.oh-my-zsh-custom"
plugins=()
source "$ZSH/oh-my-zsh.sh"
EOF

/usr/bin/python3 - <<'PY' "$tmp_home/.zshrc" "$REAL_HOME"
from pathlib import Path
path = Path(__import__("sys").argv[1])
real_home = __import__("sys").argv[2]
path.write_text(path.read_text().replace('"$REAL_HOME"', real_home), encoding='utf-8')
PY

cat > "$tmp_home/.oh-my-zsh-custom/10-slow.zsh" <<'EOF'
slow_fn() { sleep 0.02; }
slow_fn
EOF

cat > "$tmp_home/.oh-my-zsh-custom/20-env.zsh" <<'EOF'
export TEST_PROFILE_ZSH=1
EOF

artifacts_dir="$ROOT_DIR/.artifacts/test-tmp/profile-zsh-output.$BASHPID.$RANDOM"
rm -rf "$artifacts_dir"

if HOME="$tmp_home" "$SCRIPT" baseline --artifacts-dir "$artifacts_dir" >/dev/null 2>&1; then
  if find "$artifacts_dir" -name baseline.txt -print -quit | grep -q .; then
    pass "baseline writes baseline.txt"
  else
    fail "baseline missing baseline.txt"
  fi
else
  fail "baseline subcommand failed"
fi

rm -rf "$artifacts_dir"
if HOME="$tmp_home" "$SCRIPT" zprof --artifacts-dir "$artifacts_dir" >/dev/null 2>&1; then
  zprof_file="$(find "$artifacts_dir" -name zprof.txt -print -quit)"
  if [[ -n "${zprof_file:-}" && -s "$zprof_file" ]] && grep -q 'slow_fn' "$zprof_file"; then
    pass "zprof writes output and captures slow_fn"
  else
    fail "zprof output missing or does not mention slow_fn"
  fi
else
  fail "zprof subcommand failed"
fi

rm -rf "$artifacts_dir"
if HOME="$tmp_home" "$SCRIPT" xtrace --artifacts-dir "$artifacts_dir" >/dev/null 2>&1; then
  gap_file="$(find "$artifacts_dir" -name xtrace-top-gaps.txt -print -quit)"
  trace_file="$(find "$artifacts_dir" -name xtrace.log -print -quit)"
  if [[ -n "${trace_file:-}" && -s "$trace_file" ]]; then
    pass "xtrace writes trace log"
  else
    fail "xtrace trace log missing"
  fi
  if [[ -n "${trace_file:-}" && -s "$trace_file" ]] && grep -q '10-login-slow.zsh' "$trace_file"; then
    pass "xtrace captures login-shell .zprofile activity"
  else
    fail "xtrace did not capture login-shell .zprofile activity"
  fi
  if [[ -n "${gap_file:-}" && -s "$gap_file" ]] && grep -q '10-slow.zsh' "$gap_file"; then
    pass "xtrace top gaps identifies slow custom file"
  else
    fail "xtrace top gaps missing slow custom file"
  fi
else
  fail "xtrace subcommand failed"
fi

fake_bench_dir="$tmp_home/fake-zsh-bench"
mkdir -p "$fake_bench_dir/dbg"

cat > "$fake_bench_dir/zsh-bench" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
scratch_dir=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scratch-dir)
      scratch_dir="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
if [[ -n "$scratch_dir" ]]; then
  mkdir -p "$scratch_dir"
  printf 'scratch\n' > "$scratch_dir/run.log"
fi
cat <<'OUT'
creates_tty=1
has_compsys=1
first_prompt_lag_ms=12.345
first_command_lag_ms=34.567
command_lag_ms=2.500
input_lag_ms=4.250
exit_time_ms=5.125
OUT
EOF
chmod +x "$fake_bench_dir/zsh-bench"

cat > "$fake_bench_dir/dbg/timeline" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cat <<'OUT'
0.000	start
12.345	first_prompt
34.567	first_command
OUT
EOF
chmod +x "$fake_bench_dir/dbg/timeline"

fake_bench_repo="$ROOT_DIR/.artifacts/test-tmp/zsh-bench-repo.$BASHPID.$RANDOM"
rm -rf "$fake_bench_repo"
mkdir -p "$fake_bench_repo/dbg"
trap 'rm -rf "$tmp_home" "$fake_bench_repo"' EXIT

cat > "$fake_bench_repo/zsh-bench" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "installed_zsh_bench=1"
EOF
chmod +x "$fake_bench_repo/zsh-bench"

cat > "$fake_bench_repo/dbg/timeline" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "0.000	start"
EOF
chmod +x "$fake_bench_repo/dbg/timeline"

(
  cd "$fake_bench_repo"
  git init -q
  git config user.email "tests@example.com"
  git config user.name "Tests"
  git add zsh-bench dbg/timeline
  git commit -qm "init"
)

managed_bench_dir="$tmp_home/.local/share/mde/tools/zsh-bench"
if "$INSTALL_SCRIPT" --repo-url "$fake_bench_repo" --install-dir "$managed_bench_dir" >/dev/null 2>&1; then
  if [[ -x "$managed_bench_dir/zsh-bench" ]]; then
    pass "install script clones zsh-bench into managed path"
  else
    fail "install script did not place zsh-bench executable in managed path"
  fi
else
  fail "install script failed"
fi

rm -rf "$artifacts_dir"
if HOME="$tmp_home" MDE_ZSH_BENCH_BIN="$fake_bench_dir/zsh-bench" "$SCRIPT" bench --artifacts-dir "$artifacts_dir" >/dev/null 2>&1; then
  bench_file="$(find "$artifacts_dir" -name zsh-bench.txt -print -quit)"
  bench_timeline="$(find "$artifacts_dir" -name zsh-bench-timeline.tsv -print -quit)"
  if [[ -n "${bench_file:-}" && -s "$bench_file" ]] && grep -q 'first_prompt_lag_ms=12.345' "$bench_file"; then
    pass "bench writes zsh-bench metrics"
  else
    fail "bench metrics output missing"
  fi
  if [[ -n "${bench_timeline:-}" && -s "$bench_timeline" ]] && grep -q 'first_prompt' "$bench_timeline"; then
    pass "bench writes zsh-bench timeline output"
  else
    fail "bench timeline output missing"
  fi
else
  fail "bench subcommand failed"
fi

rm -rf "$artifacts_dir"
cp "$fake_bench_dir/zsh-bench" "$managed_bench_dir/zsh-bench"
chmod +x "$managed_bench_dir/zsh-bench"
mkdir -p "$managed_bench_dir/dbg"
cp "$fake_bench_dir/dbg/timeline" "$managed_bench_dir/dbg/timeline"
chmod +x "$managed_bench_dir/dbg/timeline"
if HOME="$tmp_home" "$SCRIPT" bench --artifacts-dir "$artifacts_dir" >/dev/null 2>&1; then
  bench_file="$(find "$artifacts_dir" -name zsh-bench.txt -print -quit)"
  if [[ -n "${bench_file:-}" && -s "$bench_file" ]] && grep -q 'first_prompt_lag_ms=12.345' "$bench_file"; then
    pass "bench discovers zsh-bench from managed default path"
  else
    fail "bench did not use managed default zsh-bench path"
  fi
else
  fail "bench subcommand with managed default path failed"
fi

rm -rf "$artifacts_dir"
if HOME="$tmp_home" "$SCRIPT" all --artifacts-dir "$artifacts_dir" >/dev/null 2>&1; then
  session_report="$(find "$artifacts_dir" -name terminal-session-report.md -print -quit)"
  session_steps="$(find "$artifacts_dir" -name terminal-session-steps.tsv -print -quit)"
  session_workflow="$(find "$artifacts_dir" -name terminal-session-workflow.md -print -quit)"
  if [[ -n "${session_report:-}" && -s "$session_report" ]] && grep -q 'first_prompt_lag_ms=12.345' "$session_report"; then
    pass "all writes terminal session report with zsh-bench metrics"
  else
    fail "terminal session report missing or incomplete"
  fi
  if [[ -n "${session_steps:-}" && -s "$session_steps" ]] && grep -q $'\tduration_ms\t' "$session_steps"; then
    pass "all writes per-step timestamp and duration data"
  else
    fail "terminal session steps TSV missing duration data"
  fi
  if [[ -n "${session_workflow:-}" && -s "$session_workflow" ]] && grep -q '```mermaid' "$session_workflow"; then
    pass "all writes workflow diagram markdown"
  else
    fail "workflow diagram markdown missing"
  fi
else
  fail "all subcommand failed"
fi

echo
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
