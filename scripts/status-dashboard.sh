#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="$HOME/Library/Logs/com.ray-manaloto.macos-dev-maintenance"
MAINT_LOG="$LOG_DIR/macos-dev-maintenance.out"
VALID_LOG="$LOG_DIR/macos-dev-validation.out"
SUMMARY_LOG="$LOG_DIR/post-setup-summary.log"

usage() {
  cat <<'USAGE'
Usage: status-dashboard.sh [--json|--tmux|--one-line]

  --json     Output JSON summary
  --tmux     Output a one-line status for tmux
  --one-line Alias for --tmux
USAGE
}

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.bun/bin:$home/.pixi/bin:$home/.local/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

json_escape() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

last_match() {
  local file="$1"
  local pattern="$2"

  if [[ ! -f "$file" ]]; then
    printf 'missing'
    return 0
  fi

  awk -v pat="$pattern" '$0 ~ pat {line=$0} END{if(line!="") print line}' "$file" 2>/dev/null || true
}

extract_time() {
  local line="$1"
  local ts=""

  if [[ -z "$line" || "$line" == "missing" ]]; then
    printf 'n/a'
    return 0
  fi

  ts="$(printf '%s' "$line" | awk -F'[][]' '{print $2}')"
  if [[ -z "$ts" ]]; then
    printf 'n/a'
    return 0
  fi

  printf '%s' "${ts##* }"
}

summary_status() {
  local line="$1"

  if [[ -z "$line" || "$line" == "missing" ]]; then
    printf 'unknown'
    return 0
  fi

  printf '%s' "$line" | awk '{print $NF}'
}


tmux_verification_status() {
  local line="$1"

  if [[ -z "$line" || "$line" == "missing" ]]; then
    printf 'unknown'
    return 0
  fi

  if [[ "$line" == *"PASSED"* ]]; then
    printf 'PASS'
    return 0
  fi
  if [[ "$line" == *"FAILED"* ]]; then
    printf 'FAIL'
    return 0
  fi

  printf 'unknown'
}

launchd_status_code() {
  local label="$1"
  launchctl list 2>/dev/null | awk -v label="$label" '$3==label {print $2}' || true
}

launchd_state() {
  local label="$1"
  local status

  status="$(launchd_status_code "$label")"
  if [[ -z "$status" ]]; then
    printf 'off'
    return 0
  fi
  if [[ "$status" == "0" ]]; then
    printf 'ok'
    return 0
  fi
  printf 'err:%s' "$status"
}

log_size() {
  local file="$1"
  if [[ -f "$file" ]]; then
    stat -f '%z bytes' "$file" 2>/dev/null || echo "unknown"
  else
    echo "missing"
  fi
}

cmd_path() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    command -v "$name"
  else
    printf 'missing'
  fi
}

gcloud_path() {
  if [[ -x /opt/google-cloud-sdk/bin/gcloud ]]; then
    printf '/opt/google-cloud-sdk/bin/gcloud'
    return 0
  fi
  if command -v gcloud >/dev/null 2>&1; then
    command -v gcloud
    return 0
  fi
  printf 'missing'
}

output_tmux() {
  local maint_state="$1"
  local valid_state="$2"
  local last_time="$3"
  local summary="$4"

  printf 'm:%s v:%s last:%s upd:%s' "$maint_state" "$valid_state" "$last_time" "$summary"
}

output_json() {
  local maint_state="$1"
  local maint_exit="$2"
  local valid_state="$3"
  local valid_exit="$4"
  local last_maint_line="$5"
  local last_valid_line="$6"
  local summary="$7"
  local last_maint_time="$8"
  local maint_size="$9"
  local valid_size="${10}"
  local summary_size="${11}"
  local gcloud_bin="${12}"
  local mise_bin="${13}"
  local uv_bin="${14}"
  local pixi_bin="${15}"
  local bun_bin="${16}"
  local tmux_status="${17}"
  local tmux_line="${18}"

  printf '{\n'
  printf '  "maintenance_job": {"state": "%s", "last_exit": "%s"},\n' "$(json_escape "$maint_state")" "$(json_escape "$maint_exit")"
  printf '  "validation_job": {"state": "%s", "last_exit": "%s"},\n' "$(json_escape "$valid_state")" "$(json_escape "$valid_exit")"
  printf '  "logs": {\n'
  printf '    "maintenance": {"path": "%s", "size": "%s", "last_line": "%s", "last_time": "%s"},\n' \
    "$(json_escape "$MAINT_LOG")" "$(json_escape "$maint_size")" "$(json_escape "$last_maint_line")" "$(json_escape "$last_maint_time")"
  printf '    "validation": {"path": "%s", "size": "%s", "last_line": "%s"},\n' \
    "$(json_escape "$VALID_LOG")" "$(json_escape "$valid_size")" "$(json_escape "$last_valid_line")"
  printf '    "summary": {"path": "%s", "size": "%s", "status": "%s"}\n' \
    "$(json_escape "$SUMMARY_LOG")" "$(json_escape "$summary_size")" "$(json_escape "$summary")"
  printf '  },\n'
  printf '  "tmux_verification": {"status": "%s", "last_line": "%s"},\n' \
    "$(json_escape "$tmux_status")" "$(json_escape "$tmux_line")"
  printf '  "tools": {"gcloud": "%s", "mise": "%s", "uv": "%s", "pixi": "%s", "bun": "%s"}\n' \
    "$(json_escape "$gcloud_bin")" "$(json_escape "$mise_bin")" "$(json_escape "$uv_bin")" "$(json_escape "$pixi_bin")" "$(json_escape "$bun_bin")"
  printf '}\n'
}

main() {
  local mode="full"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --json)
        mode="json"
        shift
        ;;
      --tmux|--one-line)
        mode="tmux"
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown option: $1" >&2
        usage
        exit 1
        ;;
    esac
  done

  setup_path

  local maint_state
  local valid_state
  local maint_exit
  local valid_exit
  local last_maint_line
  local last_valid_line
  local last_summary_line
  local last_tmux_line
  local summary
  local tmux_status
  local last_maint_time
  local maint_size
  local valid_size
  local summary_size
  local gcloud_bin
  local mise_bin
  local uv_bin
  local pixi_bin
  local bun_bin

  maint_state="$(launchd_state com.ray-manaloto.macos-dev-maintenance)"
  valid_state="$(launchd_state com.ray-manaloto.macos-dev-validation)"
  maint_exit="$(launchd_status_code com.ray-manaloto.macos-dev-maintenance)"
  valid_exit="$(launchd_status_code com.ray-manaloto.macos-dev-validation)"

  last_maint_line="$(last_match "$MAINT_LOG" "Homebrew update\\.")"
  last_valid_line="$(last_match "$VALID_LOG" ".")"
  last_summary_line="$(last_match "$SUMMARY_LOG" "Post-setup summary")"
  last_tmux_line="$(last_match "$SUMMARY_LOG" "Tmux verification")"
  summary="$(summary_status "$last_summary_line")"
  tmux_status="$(tmux_verification_status "$last_tmux_line")"
  last_maint_time="$(extract_time "$last_maint_line")"

  maint_size="$(log_size "$MAINT_LOG")"
  valid_size="$(log_size "$VALID_LOG")"
  summary_size="$(log_size "$SUMMARY_LOG")"

  gcloud_bin="$(gcloud_path)"
  mise_bin="$(cmd_path mise)"
  uv_bin="$(cmd_path uv)"
  pixi_bin="$(cmd_path pixi)"
  bun_bin="$(cmd_path bun)"

  case "$mode" in
    tmux)
      output_tmux "$maint_state" "$valid_state" "$last_maint_time" "$summary"
      ;;
    json)
      output_json "$maint_state" "$maint_exit" "$valid_state" "$valid_exit" \
        "$last_maint_line" "$last_valid_line" "$summary" "$last_maint_time" \
        "$maint_size" "$valid_size" "$summary_size" \
        "$gcloud_bin" "$mise_bin" "$uv_bin" "$pixi_bin" "$bun_bin" \
        "$tmux_status" "$last_tmux_line"
      ;;
    *)
      log "Status dashboard"
      log "Maintenance job: $(launchd_state com.ray-manaloto.macos-dev-maintenance)"
      log "Validation job:  $(launchd_state com.ray-manaloto.macos-dev-validation)"
      log "Maintenance log: $MAINT_LOG ($maint_size)"
      log "Validation log:  $VALID_LOG ($valid_size)"
      log "Summary log:     $SUMMARY_LOG ($summary_size)"
      log "Last maintenance: $last_maint_line"
      log "Last validation:  $last_valid_line"
      log "Last summary:     $last_summary_line"
      log "Last tmux verify: $last_tmux_line"
      log "gcloud: $gcloud_bin"
      log "mise: $mise_bin"
      log "uv:   $uv_bin"
      log "pixi: $pixi_bin"
      log "bun:  $bun_bin"
      ;;
  esac
}

main "$@"
