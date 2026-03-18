#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_ARTIFACT_BASE="$ROOT_DIR/.artifacts/shell-profile"
DEFAULT_ZSH_BENCH_DIR="${MDE_ZSH_BENCH_INSTALL_DIR:-$HOME/.local/share/mde/tools/zsh-bench}"
TIMESTAMP="${MDE_SHELL_PROFILE_TIMESTAMP:-$(date +%Y%m%d-%H%M%S)}"
ARTIFACT_BASE="$DEFAULT_ARTIFACT_BASE"
ALLOW_SUDO=0
SUBCOMMAND=""
PROFILE_CWD="${MDE_SHELL_PROFILE_CWD:-$HOME}"

usage() {
  cat <<'EOF'
Usage: scripts/profile-zsh-startup.sh <subcommand> [options]

Subcommands:
  baseline   Run a coarse startup timing using hyperfine or /usr/bin/time.
  bench      Run optional zsh-bench latency measurements when available.
  zprof      Profile shell functions with zsh/zprof.
  xtrace     Capture timestamped xtrace and report the biggest gaps.
  syscalls   Attempt syscall/file tracing with dtruss or fs_usage.
  all        Run baseline, bench, zprof, and xtrace, then write a summary.
  help       Show this help text.

Options:
  --artifacts-dir <dir>  Base directory for timestamped output directories.
  --allow-sudo           Allow sudo-based tracing for the syscalls subcommand.
  -h, --help             Show this help text.

Notes:
  - Output is written to <artifacts-dir>/<timestamp>/.
  - HISTFILE is redirected to /dev/null for all probes.
  - The baseline command is a coarse regression metric; it is not a proxy for
    user-visible first prompt or first command latency.
  - zsh-bench remains optional. The profiler auto-detects a managed checkout at
    $HOME/.local/share/mde/tools/zsh-bench/zsh-bench or MDE_ZSH_BENCH_BIN.
EOF
}

log() {
  printf '%s\n' "$*"
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

ensure_dir() {
  mkdir -p "$1"
}

default_zsh_bench_bin() {
  printf '%s/zsh-bench\n' "$DEFAULT_ZSH_BENCH_DIR"
}

resolve_zsh_bench_bin() {
  local bench_bin="${MDE_ZSH_BENCH_BIN:-}"
  local managed_bin
  managed_bin="$(default_zsh_bench_bin)"
  if [[ -n "$bench_bin" ]]; then
    printf '%s\n' "$bench_bin"
    return 0
  fi
  if [[ -x "$managed_bin" ]]; then
    printf '%s\n' "$managed_bin"
    return 0
  fi
  command -v zsh-bench || true
}

run_dir() {
  printf '%s/%s\n' "$ARTIFACT_BASE" "$TIMESTAMP"
}

write_note() {
  local path="$1"
  shift
  printf '%s\n' "$*" > "$path"
}

append_command_log() {
  local outdir="$1"
  shift
  printf '%s | %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*" >> "$outdir/commands.log"
}

write_metadata() {
  local outdir="$1"
  local subcommand="$2"
  /usr/bin/python3 - "$outdir/run-metadata.json" "$subcommand" "$TIMESTAMP" "$PROFILE_CWD" <<'PY'
import json
import os
import shutil
import socket
import sys
from pathlib import Path

metadata_path = Path(sys.argv[1])
subcommand = sys.argv[2]
timestamp = sys.argv[3]
profile_cwd = sys.argv[4]
tool_candidates = {
    "hyperfine": shutil.which("hyperfine"),
    "zsh": shutil.which("zsh"),
    "python3": shutil.which("python3"),
    "dtruss": shutil.which("dtruss"),
    "fs_usage": shutil.which("fs_usage"),
    "zsh_bench": (
        os.environ.get("MDE_ZSH_BENCH_BIN")
        or (
            str(Path.home() / ".local/share/mde/tools/zsh-bench/zsh-bench")
            if (Path.home() / ".local/share/mde/tools/zsh-bench/zsh-bench").exists()
            else shutil.which("zsh-bench")
        )
    ),
    "managed_zsh_bench_checkout": str(Path.home() / ".local/share/mde/tools/zsh-bench"),
}
metadata = {
    "timestamp": timestamp,
    "subcommand": subcommand,
    "artifact_dir": str(metadata_path.parent),
    "profile_cwd": profile_cwd,
    "home": os.environ.get("HOME"),
    "shell": os.environ.get("SHELL"),
    "hostname": socket.gethostname(),
    "available_tools": tool_candidates,
}
metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

prepare_wrapper_dir() {
  local tmpdir="$1"
  local mode="$2"

  cat > "$tmpdir/.zshenv" <<'EOF'
export HISTFILE=/dev/null
EOF

  cat > "$tmpdir/.zprofile" <<'EOF'
if [[ -f "$HOME/.zprofile" ]]; then
  source "$HOME/.zprofile"
fi
EOF

  case "$mode" in
    zprof)
      cat > "$tmpdir/.zshrc" <<'EOF'
zmodload zsh/zprof
if [[ -f "$HOME/.zshrc" ]]; then
  source "$HOME/.zshrc"
else
  print -u2 -- "missing $HOME/.zshrc"
  return 1
fi
zprof
EOF
      ;;
    xtrace)
      cat > "$tmpdir/.zprofile" <<'EOF'
PS4=$'+%D{%s.%9.} %N:%i> '
setopt xtrace promptsubst
if [[ -f "$HOME/.zprofile" ]]; then
  source "$HOME/.zprofile"
fi
EOF
      cat > "$tmpdir/.zshrc" <<'EOF'
if [[ -f "$HOME/.zshrc" ]]; then
  source "$HOME/.zshrc"
else
  print -u2 -- "missing $HOME/.zshrc"
  return 1
fi
EOF
      ;;
    *)
      die "unknown wrapper mode: $mode"
      ;;
  esac
}

run_baseline() {
  local outdir="$1"
  local outfile="$outdir/baseline.txt"
  local hyperfine_failed=0

  append_command_log "$outdir" "baseline: zsh -il -c exit"

  {
    echo "warning: 'zsh -il -c exit' is a coarse regression metric."
    echo "warning: Prefer zprof, xtrace, or optional zsh-bench for user-visible latency."
    echo
    if command -v hyperfine >/dev/null 2>&1; then
      echo "tool: hyperfine"
      if ! (
        cd "$PROFILE_CWD"
        HYPERFINE_SHELL=bash \
          hyperfine --shell=bash --warmup 1 --runs 5 \
          "cd \"$PROFILE_CWD\" && HISTFILE=/dev/null exec zsh -il -c exit"
      ); then
        hyperfine_failed=1
        echo
        echo "note: hyperfine failed; falling back to /usr/bin/time."
        echo
      fi
    fi

    if [[ "$hyperfine_failed" == "1" ]] || ! command -v hyperfine >/dev/null 2>&1; then
      echo "tool: /usr/bin/time"
      (
        cd "$PROFILE_CWD"
        HISTFILE=/dev/null /usr/bin/time -lp zsh -il -c exit
      )
    fi
  } >"$outfile" 2>&1

  log "baseline -> $outfile"
}

run_bench() {
  local outdir="$1"
  local outfile="$outdir/zsh-bench.txt"
  local timeline_file="$outdir/zsh-bench-timeline.tsv"
  local scratch_dir="$outdir/zsh-bench-scratch"
  local bench_bin=""
  local timeline_bin=""
  local timeout_sec="${MDE_ZSH_BENCH_TIMEOUT_SEC:-60}"
  local bench_status=0

  bench_bin="$(resolve_zsh_bench_bin)"

  if [[ -z "$bench_bin" ]]; then
    append_command_log "$outdir" "bench: skipped (zsh-bench unavailable)"
    write_note "$outfile" \
      "Skipped zsh-bench." \
      "zsh-bench is optional and was not found on PATH or in the managed checkout." \
      "Install it with scripts/install-zsh-bench.sh or set MDE_ZSH_BENCH_BIN=/path/to/zsh-bench."
    log "bench -> $outfile (skipped; zsh-bench unavailable)"
    return 0
  fi

  append_command_log "$outdir" "bench: $bench_bin --scratch-dir $scratch_dir"
  mkdir -p "$scratch_dir"

  if ! /usr/bin/python3 - "$bench_bin" "$scratch_dir" "$PROFILE_CWD" "$outfile" "$timeout_sec" <<'PY'
import os
import subprocess
import sys
from pathlib import Path

bench_bin = sys.argv[1]
scratch_dir = sys.argv[2]
cwd = sys.argv[3]
outfile = Path(sys.argv[4])
timeout_sec = float(sys.argv[5])
env = os.environ.copy()
env["HISTFILE"] = "/dev/null"

try:
    result = subprocess.run(
        [bench_bin, "--scratch-dir", scratch_dir],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    content = result.stdout or ""
    if result.returncode != 0:
        content += f"\n[zsh-bench exit_code={result.returncode}]\n"
    outfile.write_text(content, encoding="utf-8")
    raise SystemExit(result.returncode)
except subprocess.TimeoutExpired as exc:
    content = exc.stdout or ""
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")
    content += (
        "\nSkipped zsh-bench.\n"
        f"zsh-bench exceeded the timeout budget ({timeout_sec:.0f}s).\n"
        "Use MDE_ZSH_BENCH_TIMEOUT_SEC to raise the limit if you need a longer run.\n"
    )
    outfile.write_text(content, encoding="utf-8")
    raise SystemExit(124)
PY
  then
    bench_status=$?
  fi

  if [[ "$bench_status" == "124" ]]; then
    append_command_log "$outdir" "bench: timed out after ${timeout_sec}s"
    log "bench -> $outfile (timed out after ${timeout_sec}s)"
  elif [[ "$bench_status" != "0" ]]; then
    append_command_log "$outdir" "bench: exited with status $bench_status"
    log "bench -> $outfile (exit status $bench_status)"
  fi

  if [[ -x "$(dirname "$bench_bin")/dbg/timeline" ]]; then
    timeline_bin="$(dirname "$bench_bin")/dbg/timeline"
  else
    timeline_bin="$(cd "$(dirname "$bench_bin")/.." && pwd)/dbg/timeline"
  fi
  if [[ -x "$timeline_bin" ]]; then
    append_command_log "$outdir" "bench timeline: $timeline_bin $scratch_dir"
    "$timeline_bin" "$scratch_dir" >"$timeline_file" 2>&1 || true
  else
    write_note "$timeline_file" \
      "No zsh-bench timeline helper was found." \
      "Expected optional helper at: $timeline_bin"
  fi

  log "bench -> $outfile"
  log "bench timeline -> $timeline_file"
}

run_zprof() {
  local outdir="$1"
  local outfile="$outdir/zprof.txt"
  local tmpdir
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' RETURN

  append_command_log "$outdir" "zprof: ZDOTDIR wrapper -> zsh -il -c exit"

  prepare_wrapper_dir "$tmpdir" zprof
  (
    cd "$PROFILE_CWD"
    HISTFILE=/dev/null ZDOTDIR="$tmpdir" zsh -il -c exit
  ) >"$outfile" 2>&1
  log "zprof -> $outfile"
}

run_xtrace() {
  local outdir="$1"
  local trace_file="$outdir/xtrace.log"
  local gap_file="$outdir/xtrace-top-gaps.txt"
  local timeline_file="$outdir/xtrace-timeline.md"
  local steps_file="$outdir/terminal-session-steps.tsv"
  local workflow_file="$outdir/terminal-session-workflow.md"
  local tmpdir
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' RETURN

  append_command_log "$outdir" "xtrace: ZDOTDIR wrapper -> zsh -il -c exit"

  prepare_wrapper_dir "$tmpdir" xtrace
  (
    cd "$PROFILE_CWD"
    HISTFILE=/dev/null ZDOTDIR="$tmpdir" zsh -il -c exit
  ) >"$outdir/xtrace.stdout" 2>"$trace_file"

  /usr/bin/python3 - "$trace_file" "$gap_file" "$timeline_file" "$steps_file" "$workflow_file" <<'PY'
import re
import sys
from pathlib import Path

trace_path = Path(sys.argv[1])
gap_path = Path(sys.argv[2])
timeline_path = Path(sys.argv[3])
steps_path = Path(sys.argv[4])
workflow_path = Path(sys.argv[5])
pattern = re.compile(r'^\+(\d+\.\d+)\s+(.+?):(\d+)>\s?(.*)$')
source_hint_pattern = re.compile(r'(\.zsh:\d+>|source .+\.zsh)')
timeline_hint_pattern = re.compile(
    r'^(source .+|\. .+|(?:.+/)?brew shellenv|starship init zsh|security find-generic-password\b.+|compinit -i\b.+|compdump$|zrecompile\b.+|compdef _omz omz$)'
)

entries = []
prev_time = None
prev_line = None
prev_index = None
records = []

for raw_line in trace_path.read_text(errors='ignore').splitlines():
    match = pattern.match(raw_line)
    if not match:
        continue
    current_time = float(match.group(1))
    entry = {
        "raw": raw_line,
        "timestamp": current_time,
        "file": match.group(2),
        "line": match.group(3),
        "command": match.group(4),
    }
    entries.append(entry)
    current_index = len(entries) - 1
    if prev_time is not None:
        delta_ms = (current_time - prev_time) * 1000.0
        records.append((delta_ms, prev_line["raw"], raw_line, prev_index))
    prev_time = current_time
    prev_line = entry
    prev_index = current_index

for idx, entry in enumerate(entries):
    if idx + 1 < len(entries):
        entry["duration_ms"] = max(0.0, (entries[idx + 1]["timestamp"] - entry["timestamp"]) * 1000.0)
    else:
        entry["duration_ms"] = 0.0

def find_context(index):
    if index is None:
        return None
    for cursor in range(index, -1, -1):
        candidate = entries[cursor]["raw"]
        if source_hint_pattern.search(candidate):
            return candidate
    return None

def is_major_step(command):
    if command.startswith(("source ", ". ")):
        return True
    return bool(
        re.match(
            r'^(?:.+/)?brew shellenv$|^starship init zsh$|^security find-generic-password\b.+|^compinit -i\b.+|^compdump$|^zrecompile\b.+|^compdef _omz omz$',
            command,
        )
    )

records.sort(key=lambda item: item[0], reverse=True)
with gap_path.open('w', encoding='utf-8') as fh:
    if not records:
      fh.write("No timestamped xtrace gaps were captured.\n")
    else:
        for delta_ms, prev_line, next_line, prev_index in records[:20]:
            fh.write(f"gap_ms={delta_ms:.2f}\n")
            context_line = find_context(prev_index)
            if context_line is not None:
                fh.write(f"context={context_line}\n")
            fh.write(f"{prev_line}\n")
            fh.write(f"{next_line}\n\n")

timeline_rows = []
major_rows = []
for entry in entries:
    command = entry["command"]
    match = timeline_hint_pattern.match(command)
    if not match:
        if is_major_step(entry["command"]):
            if not major_rows or major_rows[-1]["command"] != entry["command"]:
                major_rows.append(entry)
        continue
    event = match.group(1)
    if not timeline_rows or timeline_rows[-1][1] != event:
        timeline_rows.append((entry["timestamp"], event, entry["duration_ms"]))
    if is_major_step(entry["command"]):
        if not major_rows or major_rows[-1]["command"] != entry["command"]:
            major_rows.append(entry)

with timeline_path.open('w', encoding='utf-8') as fh:
    fh.write("# xtrace timeline\n\n")
    fh.write("| timestamp | duration_ms | event |\n")
    fh.write("| --- | ---: | --- |\n")
    for timestamp, event, duration_ms in timeline_rows:
        event = event.replace("|", "\\|")
        fh.write(f"| `{timestamp:.9f}` | `{duration_ms:.3f}` | `{event}` |\n")

with steps_path.open("w", encoding="utf-8") as fh:
    fh.write("timestamp\tduration_ms\tfile\tline\tcommand\n")
    for entry in entries:
        command = entry["command"].replace("\t", " ").replace("\n", " ")
        fh.write(
            f"{entry['timestamp']:.9f}\t{entry['duration_ms']:.3f}\t{entry['file']}\t{entry['line']}\t{command}\n"
        )

def short_label(command):
    command = command.strip()
    if len(command) > 72:
        return command[:69] + "..."
    return command

with workflow_path.open("w", encoding="utf-8") as fh:
    fh.write("# Terminal session workflow\n\n")
    fh.write("| step | timestamp | duration_ms | command |\n")
    fh.write("| --- | --- | ---: | --- |\n")
    for idx, entry in enumerate(major_rows, start=1):
        command = entry["command"].replace("|", "\\|")
        fh.write(
            f"| {idx:02d} | `{entry['timestamp']:.9f}` | `{entry['duration_ms']:.3f}` | `{command}` |\n"
        )
    fh.write("\n```mermaid\n")
    fh.write("flowchart TD\n")
    if not major_rows:
        fh.write('    A["No major steps captured"]\n')
    else:
        for idx, entry in enumerate(major_rows, start=1):
            node = f"S{idx:02d}"
            label = short_label(entry["command"]).replace('"', '\\"')
            fh.write(
                f'    {node}["{idx:02d} {label}<br/>{entry["timestamp"]:.9f}<br/>{entry["duration_ms"]:.3f} ms"]\n'
            )
            if idx > 1:
                prev = f"S{idx - 1:02d}"
                fh.write(f"    {prev} --> {node}\n")
    fh.write("```\n")
PY

  log "xtrace -> $trace_file"
  log "xtrace gaps -> $gap_file"
  log "xtrace timeline -> $timeline_file"
  log "xtrace steps -> $steps_file"
  log "workflow -> $workflow_file"
}

write_session_report() {
  local outdir="$1"
  local report_file="$outdir/terminal-session-report.md"
  local bench_file="$outdir/zsh-bench.txt"
  local zprof_file="$outdir/zprof.txt"
  local gap_file="$outdir/xtrace-top-gaps.txt"
  local workflow_file="$outdir/terminal-session-workflow.md"
  local timeline_file="$outdir/xtrace-timeline.md"

  /usr/bin/python3 - "$report_file" "$bench_file" "$zprof_file" "$gap_file" "$workflow_file" "$timeline_file" <<'PY'
import re
import sys
from pathlib import Path

report_path = Path(sys.argv[1])
bench_path = Path(sys.argv[2])
zprof_path = Path(sys.argv[3])
gap_path = Path(sys.argv[4])
workflow_path = Path(sys.argv[5])
timeline_path = Path(sys.argv[6])

bench_lines = []
bench_skipped = False
bench_timed_out = False
if bench_path.exists():
    for line in bench_path.read_text(errors="ignore").splitlines():
        if line.startswith("Skipped zsh-bench."):
            bench_skipped = True
        if "exceeded the timeout budget" in line:
            bench_timed_out = True
        if line.startswith(("first_prompt_lag_ms=", "first_command_lag_ms=", "command_lag_ms=", "input_lag_ms=", "exit_time_ms=")):
            bench_lines.append(line.strip())

zprof_lines = []
if zprof_path.exists():
    started = False
    for line in zprof_path.read_text(errors="ignore").splitlines():
        if line.startswith("num  calls"):
            started = True
            continue
        if not started:
            continue
        if not line.strip() or line.startswith("---"):
            if zprof_lines:
                break
            continue
        if re.match(r'^\s*\d+\)', line):
            zprof_lines.append(line.strip())
        if len(zprof_lines) >= 5:
            break

gap_lines = []
if gap_path.exists():
    for chunk in gap_path.read_text(errors="ignore").strip().split("\n\n")[:5]:
        lines = chunk.splitlines()
        if not lines:
            continue
        gap_lines.append((lines[0], lines[1] if len(lines) > 1 else ""))

with report_path.open("w", encoding="utf-8") as fh:
    fh.write("# Terminal session report\n\n")
    fh.write("## Latency summary\n")
    if bench_lines:
        for line in bench_lines:
            fh.write(f"- `{line}`\n")
    elif bench_timed_out:
        fh.write("- `zsh-bench` timed out before it could emit usable latency metrics.\n")
    elif bench_skipped:
        fh.write("- `zsh-bench` was not available for this run.\n")
    else:
        fh.write("- No `zsh-bench` metrics were captured.\n")
    fh.write("\n## Top zprof functions\n")
    if zprof_lines:
        for line in zprof_lines:
            fh.write(f"- `{line}`\n")
    else:
        fh.write("- No zprof data captured.\n")
    fh.write("\n## Largest xtrace gaps\n")
    if gap_lines:
        for headline, context in gap_lines:
            fh.write(f"- `{headline}`")
            if context:
                fh.write(f" via `{context}`")
            fh.write("\n")
    else:
        fh.write("- No xtrace gap data captured.\n")
    if timeline_path.exists():
        fh.write("\n## Timeline artifact\n")
        fh.write(f"- See `{timeline_path.name}` for the condensed event timeline.\n")
    if workflow_path.exists():
        fh.write("\n")
        fh.write(workflow_path.read_text(encoding="utf-8"))
PY

  log "session report -> $report_file"
}

run_syscalls() {
  local outdir="$1"
  local outfile="$outdir/syscalls.txt"

  append_command_log "$outdir" "syscalls: sudo tracing requested=$ALLOW_SUDO"

  if [[ "$ALLOW_SUDO" != "1" ]]; then
    write_note "$outfile" \
      "Skipped syscall tracing." \
      "Re-run with --allow-sudo to permit dtruss/fs_usage probes." \
      "Focus areas: child process launches, ~/.oh-my-zsh reads, cache files, and keychain/security access."
    log "syscalls -> $outfile (skipped; --allow-sudo not set)"
    return 0
  fi

  if ! sudo -n true >/dev/null 2>&1; then
    write_note "$outfile" \
      "Skipped syscall tracing." \
      "sudo is required but not available non-interactively." \
      "Try running with cached sudo credentials, then re-run this command."
    log "syscalls -> $outfile (skipped; sudo unavailable)"
    return 0
  fi

  if command -v dtruss >/dev/null 2>&1; then
    {
      echo "tool: dtruss"
      echo "command: sudo -n dtruss -f zsh -il -c exit"
      cd "$PROFILE_CWD"
      sudo -n dtruss -f zsh -il -c exit
    } >"$outfile" 2>&1 || true
    log "syscalls -> $outfile"
    return 0
  fi

  if command -v fs_usage >/dev/null 2>&1; then
    {
      echo "tool: fs_usage"
      echo "command: sudo -n fs_usage -w -f exec zsh"
      echo "fs_usage support is best-effort; refine manually if you need narrower filters."
    } >"$outfile"
    log "syscalls -> $outfile"
    return 0
  fi

  write_note "$outfile" "Skipped syscall tracing: neither dtruss nor fs_usage is available."
  log "syscalls -> $outfile (skipped; no tracing tool available)"
}

write_summary() {
  local outdir="$1"
  local summary="$outdir/summary.md"
  local baseline_file="$outdir/baseline.txt"
  local bench_file="$outdir/zsh-bench.txt"
  local zprof_file="$outdir/zprof.txt"
  local gap_file="$outdir/xtrace-top-gaps.txt"

  /usr/bin/python3 - "$summary" "$baseline_file" "$bench_file" "$zprof_file" "$gap_file" <<'PY'
import re
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
baseline_path = Path(sys.argv[2])
bench_path = Path(sys.argv[3])
zprof_path = Path(sys.argv[4])
gap_path = Path(sys.argv[5])

baseline_lines = []
if baseline_path.exists():
    for line in baseline_path.read_text(errors='ignore').splitlines():
        if line.startswith(("tool:", "Benchmark", "Time (mean", "time elapsed", "real", "user", "sys")):
            baseline_lines.append(line.strip())
        if len(baseline_lines) >= 6:
            break

bench_lines = []
bench_skipped = False
bench_timed_out = False
if bench_path.exists():
    for line in bench_path.read_text(errors='ignore').splitlines():
        if line.startswith("Skipped zsh-bench."):
            bench_skipped = True
        if "exceeded the timeout budget" in line:
            bench_timed_out = True
        if "=" not in line:
            continue
        if line.startswith(("first_prompt_lag_ms=", "first_command_lag_ms=", "command_lag_ms=", "input_lag_ms=", "exit_time_ms=")):
            bench_lines.append(line.strip())
        if len(bench_lines) >= 5:
            break

zprof_lines = []
if zprof_path.exists():
    started = False
    for line in zprof_path.read_text(errors='ignore').splitlines():
        if line.startswith("num  calls"):
            started = True
            continue
        if not started:
            continue
        if not line.strip() or line.startswith("---"):
            if zprof_lines:
                break
            continue
        if re.match(r'^\s*\d+\)', line):
            zprof_lines.append(line.strip())
        if len(zprof_lines) >= 5:
            break

gap_lines = []
if gap_path.exists():
    chunks = gap_path.read_text(errors='ignore').strip().split("\n\n")
    for chunk in chunks[:5]:
        first = chunk.splitlines()[0] if chunk.splitlines() else ""
        second = chunk.splitlines()[1] if len(chunk.splitlines()) > 1 else ""
        gap_lines.append((first, second))

with summary_path.open('w', encoding='utf-8') as fh:
    fh.write("# zsh startup profiling summary\n\n")
    fh.write("## Baseline\n")
    if baseline_lines:
        for line in baseline_lines:
            fh.write(f"- `{line}`\n")
    else:
        fh.write("- No baseline data captured.\n")
    fh.write("\n## zsh-bench\n")
    if bench_lines:
        for line in bench_lines:
            fh.write(f"- `{line}`\n")
    elif bench_timed_out:
        fh.write("- zsh-bench timed out before emitting usable latency metrics.\n")
    elif bench_skipped:
        fh.write("- zsh-bench was skipped because no local binary was configured.\n")
    elif bench_path.exists():
        fh.write("- zsh-bench ran but did not emit parsed latency metrics.\n")
    else:
        fh.write("- zsh-bench was not captured.\n")
    fh.write("\n## Top zprof functions\n")
    if zprof_lines:
        for line in zprof_lines:
            fh.write(f"- `{line}`\n")
    else:
        fh.write("- No zprof data captured.\n")
    fh.write("\n## Top xtrace gaps\n")
    if gap_lines:
        for gap, detail in gap_lines:
            fh.write(f"- `{gap}` from `{detail}`\n")
    else:
        fh.write("- No xtrace gap data captured.\n")
PY

  log "summary -> $summary"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    baseline|bench|zprof|xtrace|syscalls|all|help)
      SUBCOMMAND="$1"
      shift
      ;;
    --artifacts-dir)
      [[ $# -ge 2 ]] || die "--artifacts-dir requires a value"
      ARTIFACT_BASE="$2"
      shift 2
      ;;
    --allow-sudo)
      ALLOW_SUDO=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ -n "$SUBCOMMAND" ]] || {
  usage
  exit 1
}

[[ "$SUBCOMMAND" != "help" ]] || {
  usage
  exit 0
}

OUTDIR="$(run_dir)"
ensure_dir "$OUTDIR"
write_metadata "$OUTDIR" "$SUBCOMMAND"

case "$SUBCOMMAND" in
  baseline)
    run_baseline "$OUTDIR"
    ;;
  bench)
    run_bench "$OUTDIR"
    ;;
  zprof)
    run_zprof "$OUTDIR"
    ;;
  xtrace)
    run_xtrace "$OUTDIR"
    ;;
  syscalls)
    run_syscalls "$OUTDIR"
    ;;
  all)
    run_baseline "$OUTDIR"
    run_bench "$OUTDIR"
    run_zprof "$OUTDIR"
    run_xtrace "$OUTDIR"
    write_summary "$OUTDIR"
    write_session_report "$OUTDIR"
    ;;
  *)
    die "unsupported subcommand: $SUBCOMMAND"
    ;;
esac
