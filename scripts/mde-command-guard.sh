#!/usr/bin/env bash
set -euo pipefail

SOURCE_PATH="${BASH_SOURCE[0]}"
while [[ -L "$SOURCE_PATH" ]]; do
  SOURCE_DIR="$(cd "$(dirname "$SOURCE_PATH")" && pwd)"
  SOURCE_PATH="$(readlink "$SOURCE_PATH")"
  [[ "$SOURCE_PATH" == /* ]] || SOURCE_PATH="$SOURCE_DIR/$SOURCE_PATH"
done
SCRIPT_DIR="$(cd "$(dirname "$SOURCE_PATH")" && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install

resolve_path_shell() {
  local path="$1"
  local dir

  while [[ -L "$path" ]]; do
    dir="$(cd "$(dirname "$path")" && pwd)"
    path="$(readlink "$path")"
    [[ "$path" == /* ]] || path="$dir/$path"
  done

  dir="$(cd "$(dirname "$path")" && pwd)"
  printf '%s/%s\n' "$dir" "$(basename "$path")"
}

find_real_command() {
  local name="$1"
  local guard_dir="${MDE_GUARD_DIR:-}"
  local candidate
  local candidate_resolved

  while IFS= read -r candidate; do
    [[ -n "$candidate" ]] || continue
    if [[ -n "$guard_dir" && "$candidate" == "$guard_dir/"* ]]; then
      continue
    fi
    candidate_resolved="$(resolve_path_shell "$candidate")"
    if [[ "$candidate_resolved" == "$SOURCE_PATH" ]]; then
      continue
    fi
    printf '%s\n' "$candidate"
    return 0
  done < <(which -a "$name" 2>/dev/null || true)

  return 1
}

cmd="$(basename "$0")"
real_cmd="$(find_real_command "$cmd" || true)"
if [[ -z "$real_cmd" ]]; then
  printf 'mde command guard could not locate the real %s binary\n' "$cmd" >&2
  exit 127
fi

args=("$@")
manager="$cmd"
action="${1:-}"
shifted=("${args[@]:1}")

list_targets() {
  local out=()
  local skip_next=0
  local item
  for item in "$@"; do
    if (( skip_next == 1 )); then
      skip_next=0
      continue
    fi
    case "$item" in
      --formula|--cask|--repository)
        continue
        ;;
      -*)
        continue
        ;;
      *=*)
        continue
        ;;
      *)
        out+=("$item")
        ;;
    esac
  done
  printf '%s\n' "${out[@]}"
}

collect_targets() {
  local item
  targets=()
  while IFS= read -r item; do
    [[ -n "$item" ]] || continue
    targets+=("$item")
  done < <(list_targets "$@")
}

allow_via_exception() {
  local target
  [[ "${MDE_ALLOW_UNMANAGED_INSTALL:-0}" == "1" ]] || return 1
  for target in "$@"; do
    [[ -n "$target" ]] || continue
    if mde_exception_allows_target "$manager" "$target"; then
      mde_emit_telemetry_event "policy.exception.used" "override" "Allowed unmanaged install via exception" "manager=$manager" "target=$target"
      return 0
    fi
  done
  return 1
}

block_now() {
  local reason="$1"
  shift
  local targets=("$@")
  if allow_via_exception "${targets[@]}"; then
    exec "$real_cmd" "${args[@]}"
  fi
  mde_emit_telemetry_event "policy.command.blocked" "blocked" "$reason" "manager=$manager" "command=$cmd" "argv=${args[*]}"
  printf '%s\n' "$reason" >&2
  printf '%s\n' 'Use the managed path instead: declare global tools in /Users/rmanaloto/.config/mise/config.toml and run `mise install`, `mise run`, or `mise x`.' >&2
  exit 97
}

case "$cmd" in
  brew)
    case "$action" in
      install|reinstall|upgrade)
        collect_targets "${shifted[@]}"
        block_now "brew install-style commands are blocked for agents in this repo." "${targets[@]}"
        ;;
    esac
    ;;
  npm)
    if [[ "$action" =~ ^(install|i|add|update)$ ]] && printf '%s\n' "${args[*]}" | grep -Eq '(^|[[:space:]])(-g|--global)($|[[:space:]])'; then
      collect_targets "${shifted[@]}"
      block_now "npm global installs are blocked for agents in this repo." "${targets[@]}"
    fi
    ;;
  bun)
    if [[ "$action" =~ ^(add|install|update)$ ]] && printf '%s\n' "${args[*]}" | grep -Eq '(^|[[:space:]])(-g|--global)($|[[:space:]])'; then
      collect_targets "${shifted[@]}"
      block_now "bun global installs are blocked for agents in this repo." "${targets[@]}"
    fi
    ;;
  uv)
    if [[ "$action" == "tool" && "${args[1]:-}" =~ ^(install|upgrade)$ ]]; then
      collect_targets "${args[@]:2}"
      block_now "uv tool installs are blocked for agents in this repo." "${targets[@]}"
    fi
    ;;
  pip|pip3)
    if [[ "$action" == "install" ]]; then
      if printf '%s\n' "${args[*]}" | grep -Eq '(^|[[:space:]])--user($|[[:space:]])'; then
        collect_targets "${shifted[@]}"
        block_now "pip --user installs are blocked for agents in this repo." "${targets[@]}"
      fi
      if [[ -z "${VIRTUAL_ENV:-}" && -z "${CONDA_PREFIX:-}" ]]; then
        collect_targets "${shifted[@]}"
        block_now "Direct pip installs outside an activated environment are blocked for agents in this repo." "${targets[@]}"
      fi
    fi
    ;;
  pipx)
    if [[ "$action" =~ ^(install|upgrade|inject)$ ]]; then
      collect_targets "${shifted[@]}"
      block_now "pipx install-style commands are blocked for agents in this repo." "${targets[@]}"
    fi
    ;;
  cargo)
    if [[ "$action" =~ ^(install|binstall)$ ]]; then
      collect_targets "${shifted[@]}"
      block_now "cargo install-style commands are blocked for agents in this repo." "${targets[@]}"
    fi
    ;;
  go)
    if [[ "$action" =~ ^(install|get)$ ]]; then
      collect_targets "${shifted[@]}"
      block_now "go install/get commands are blocked for agents in this repo." "${targets[@]}"
    fi
    ;;
  curl)
    if printf '%s\n' "${args[*]}" | grep -Eiq '(mise\.run|astral\.sh/uv/install\.sh|pixi\.sh/install\.sh|/install\.sh([[:space:]]|$|\?))'; then
      block_now "curl installer flows are blocked for agents in this repo."
    fi
    ;;
esac

exec "$real_cmd" "${args[@]}"
