#!/usr/bin/env bash
# Source this in any verify-*.sh script for JSON output support.

_json_esc() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\t'/\\t}"
  s="${s//$'\f'/\\f}"
  s="${s//$'\b'/\\b}"
  printf '%s' "$s"
}

declare -a _MDE_CHECKS=()

mde_add_check() {
  local name="$1" status="$2" severity="$3" details="$4" skip_allowed="${5:-false}"
  _MDE_CHECKS+=("$(printf '{"name":"%s","status":"%s","severity":"%s","details":"%s","skip_allowed":%s}' \
    "$(_json_esc "$name")" "$status" "$severity" "$(_json_esc "$details")" "$skip_allowed")")
}

mde_emit_json() {
  local overall="pass"
  local c
  for c in "${_MDE_CHECKS[@]}"; do
    if [[ "$c" == *'"status":"fail"'*'"severity":"hard"'* ]]; then
      overall="fail"
      break
    elif [[ "$c" == *'"status":"skip"'*'"severity":"hard"'*'"skip_allowed":false'* ]]; then
      overall="fail"
      break
    elif [[ "$c" == *'"status":"fail"'* || "$c" == *'"status":"warn"'* ]]; then
      overall="warn"
    fi
  done

  printf '{"timestamp":"%s","overall":"%s","checks":[%s]}\n' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    "$overall" \
    "$(IFS=,; printf '%s' "${_MDE_CHECKS[*]}")"
}
