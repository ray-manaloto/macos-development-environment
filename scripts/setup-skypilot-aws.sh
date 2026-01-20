#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: setup-skypilot-aws.sh [--no-check] [--init-config] [--force]

Loads AWS credentials from the MDE secrets env file and validates SkyPilot
access to AWS.

Options:
  --no-check     Skip `sky check aws`.
  --init-config  Copy templates/agent_cloud.yaml to ./agent_cloud.yaml if missing.
  --force        Overwrite ./agent_cloud.yaml when used with --init-config.
USAGE
}

no_check=0
init_config=0
force=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-check)
      no_check=1
      ;;
    --init-config)
      init_config=1
      ;;
    --force)
      force=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
 done

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

setup_path

load_env_file() {
  local env_file="$1"
  local line key value

  if [[ ! -f "$env_file" ]]; then
    return 1
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" ]] && continue
    [[ "$line" == \#* ]] && continue
    line="${line#export }"
    key="${line%%=*}"
    value="${line#*=}"
    key="${key%"${key##*[![:space:]]}"}"
    key="${key#"${key%%[![:space:]]*}"}"
    [[ -z "$key" ]] && continue
    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
      value="${value#\"}"
      value="${value%\"}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
      value="${value#\'}"
      value="${value%\'}"
    fi
    export "$key"="$value"
  done < "$env_file"
}

require_env() {
  local key="$1"
  if [[ -z "${!key:-}" ]]; then
    log "Missing $key (set it in secrets.env)."
    return 1
  fi
  return 0
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export MDE_ENV_FILE="${MDE_ENV_FILE:-$HOME/.config/macos-development-environment/secrets.env}"

if ! load_env_file "$MDE_ENV_FILE"; then
  log "Missing secrets file: $MDE_ENV_FILE"
  log "Run: $repo_root/scripts/setup-secrets-env.sh --open"
  exit 1
fi

failures=0
require_env AWS_ACCESS_KEY_ID || failures=1
require_env AWS_SECRET_ACCESS_KEY || failures=1

if [[ -z "${AWS_DEFAULT_REGION:-}" && -z "${AWS_REGION:-}" ]]; then
  log "Warning: AWS_DEFAULT_REGION or AWS_REGION not set (recommended)."
fi

if [[ "$failures" -ne 0 ]]; then
  exit 1
fi

if [[ "$init_config" -eq 1 ]]; then
  local_cfg="$repo_root/agent_cloud.yaml"
  template_cfg="$repo_root/templates/agent_cloud.yaml"
  if [[ -f "$local_cfg" && "$force" -ne 1 ]]; then
    log "agent_cloud.yaml already exists. Use --force to overwrite."
  else
    cp "$template_cfg" "$local_cfg"
    log "Copied $template_cfg -> $local_cfg"
  fi
fi

if [[ "$no_check" -ne 1 ]]; then
  if ! command -v sky >/dev/null 2>&1; then
    log "SkyPilot CLI not found. Install first: sky --version"
    exit 1
  fi
  log "Running: sky check aws"
  sky check aws
  log "SkyPilot AWS check complete."
fi
