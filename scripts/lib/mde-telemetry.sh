#!/usr/bin/env bash

mde_json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

mde_telemetry_now_utc() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

mde_telemetry_dir() {
  if [[ -n "${MDE_TELEMETRY_DIR:-}" ]]; then
    printf '%s\n' "$MDE_TELEMETRY_DIR"
    return 0
  fi

  if [[ -n "${MDE_REPO_ROOT:-}" ]]; then
    printf '%s/reports/agent-policy\n' "$MDE_REPO_ROOT"
    return 0
  fi

  printf '%s/.local/state/mde-agent-policy\n' "$HOME"
}

mde_emit_telemetry_event() {
  local event="$1"
  local status="$2"
  local message="$3"
  shift 3

  local run_id="${MDE_RUN_ID:-mde-run-$(date +%Y%m%d%H%M%S)}"
  local correlation_id="${MDE_CORRELATION_ID:-$run_id}"
  local dir
  local file
  local extra=''
  local pair
  local key
  local value

  dir="$(mde_telemetry_dir)"
  mkdir -p "$dir"
  file="$dir/$(date +%F)-events.jsonl"

  for pair in "$@"; do
    key="${pair%%=*}"
    value="${pair#*=}"
    if [[ -n "$extra" ]]; then
      extra+=','
    fi
    extra+="\"$(mde_json_escape "$key")\":\"$(mde_json_escape "$value")\""
  done

  printf '{"timestamp":"%s","event":"%s","status":"%s","message":"%s","run_id":"%s","correlation_id":"%s"%s}\n' \
    "$(mde_telemetry_now_utc)" \
    "$(mde_json_escape "$event")" \
    "$(mde_json_escape "$status")" \
    "$(mde_json_escape "$message")" \
    "$(mde_json_escape "$run_id")" \
    "$(mde_json_escape "$correlation_id")" \
    "${extra:+,$extra}" >> "$file"

  if [[ "${MDE_TELEMETRY_STDERR:-0}" == "1" ]]; then
    printf '[telemetry] %s %s %s\n' "$event" "$status" "$message" >&2
  fi
}
