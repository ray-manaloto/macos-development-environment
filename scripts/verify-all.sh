#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERIFY_CONFIG="${MDE_VERIFY_CONFIG:-$SCRIPT_DIR/config/mde-verify.conf}"
# shellcheck source=scripts/lib/mde-platform.sh
source "$SCRIPT_DIR/lib/mde-platform.sh"
# shellcheck source=scripts/lib/mde-secrets.sh
source "$SCRIPT_DIR/lib/mde-secrets.sh"
MDE_PLATFORM="${MDE_PLATFORM:-$(mde_detect_platform)}"

log() {
  if [[ "${JSON_MODE:-0}" == "1" ]]; then
    return 0
  fi
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

MDE_VERIFY_SKYPILOT="${MDE_VERIFY_SKYPILOT:-1}"
MDE_VERIFY_OPENLIT="${MDE_VERIFY_OPENLIT:-1}"
MDE_VERIFY_LANGCHAIN="${MDE_VERIFY_LANGCHAIN:-1}"
MDE_VERIFY_AWS_K8S="${MDE_VERIFY_AWS_K8S:-1}"

JSON_MODE=0
for arg in "$@"; do
  [[ "$arg" == "--json" ]] && JSON_MODE=1
done

run_status=0

setup_path
mde_load_secrets

if [[ "$JSON_MODE" == "1" ]]; then
  # shellcheck source=scripts/lib/mde-json.sh
  source "$SCRIPT_DIR/lib/mde-json.sh"
fi

platform_matches() {
  local allow="$1"
  local item
  [[ -z "${allow// }" ]] && return 0
  IFS=',' read -r -a _allow_items <<< "$allow"
  for item in "${_allow_items[@]}"; do
    item="${item//[[:space:]]/}"
    [[ -z "$item" ]] && continue
    if [[ "${item,,}" == "${MDE_PLATFORM,,}" ]]; then
      return 0
    fi
  done
  return 1
}

skip_allowed_for_platform() {
  local allow="$1"
  local item
  [[ -z "${allow// }" ]] && return 1
  IFS=',' read -r -a _allow_items <<< "$allow"
  for item in "${_allow_items[@]}"; do
    item="${item//[[:space:]]/}"
    [[ -z "$item" ]] && continue
    case "${item,,}" in
      all|'*')
        return 0
        ;;
      *)
        if [[ "${item,,}" == "${MDE_PLATFORM,,}" ]]; then
          return 0
        fi
        ;;
    esac
  done
  return 1
}

record_skip() {
  local name="$1"
  local severity="$2"
  local details="$3"
  local allow_skip="${4:-}"
  local skip_allowed="false"

  if [[ "$severity" == "hard" ]] && skip_allowed_for_platform "$allow_skip"; then
    skip_allowed="true"
  fi

  if [[ "$JSON_MODE" == "1" ]]; then
    mde_add_check "$name" "skip" "$severity" "$details" "$skip_allowed"
  fi

  if [[ "$severity" == "hard" && "$skip_allowed" != "true" ]]; then
    run_status=1
  fi
}

run_script() {
  local name="$1"
  local script="$2"
  local severity="${3:-hard}"
  local allow_skip="${4:-}"
  shift 4 || shift $#
  # Remaining args are passed to the script

  if [[ ! -x "$script" ]]; then
    log "$name script missing."
    record_skip "$name" "$severity" "script not found" "$allow_skip"
    return
  fi

  log "Running $name."
  if [[ "$JSON_MODE" == "1" ]]; then
    local tmp_log
    tmp_log="$(mktemp)"
    if "$script" "$@" >"$tmp_log" 2>&1; then
      mde_add_check "$name" "pass" "$severity" "check passed"
    else
      local detail
      detail="$(tail -n 1 "$tmp_log" | tr -d '\r')"
      [[ -z "$detail" ]] && detail="check failed"
      mde_add_check "$name" "fail" "$severity" "$detail"
      if [[ "$severity" == "hard" ]]; then
        run_status=1
      fi
    fi
    rm -f "$tmp_log"
  else
    if "$script" "$@"; then
      :
    else
      log "$name: FAILED."
      if [[ "$severity" == "hard" ]]; then
        run_status=1
      fi
    fi
  fi
}

log "Verify all starting (platform=$MDE_PLATFORM)."
if [[ ! -f "$VERIFY_CONFIG" ]]; then
  log "Verify config not found: $VERIFY_CONFIG"
  exit 1
fi

while IFS='|' read -r name rel_script severity extra_args platforms allow_skip; do
  [[ -z "${name// }" ]] && continue
  [[ "${name:0:1}" == "#" ]] && continue

  local_script="$rel_script"
  if [[ "${local_script:0:1}" != "/" ]]; then
    local_script="$REPO_ROOT/$local_script"
  fi

  run_severity="${severity:-hard}"
  if ! platform_matches "${platforms:-}"; then
    log "Skipping $name (platform filter: ${platforms:-none})."
    record_skip "$name" "$run_severity" "skipped for platform=$MDE_PLATFORM" "${allow_skip:-}"
    continue
  fi

  if [[ -n "${extra_args:-}" ]]; then
    read -r -a args_arr <<< "$extra_args"
    run_script "$name" "$local_script" "$run_severity" "${allow_skip:-}" "${args_arr[@]}"
  else
    run_script "$name" "$local_script" "$run_severity" "${allow_skip:-}"
  fi
done < "$VERIFY_CONFIG" || true

if [[ "$run_status" -eq 0 ]]; then
  if [[ "$JSON_MODE" == "1" ]]; then
    mde_emit_json
    exit 0
  fi
  log "Verify all: PASS."
  exit 0
fi

if [[ "$JSON_MODE" == "1" ]]; then
  mde_emit_json
  exit 1
fi

log "Verify all: FAIL."
exit 1
