#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: sky-status.sh [--no-aws] [--refresh] [--ttl SECONDS] [--strict]

Runs `sky status` and augments output with AWS account + EC2 details.

Options:
  --no-aws    Skip AWS queries.
  --refresh   Force refresh of AWS cached output.
  --ttl       Cache TTL for AWS queries (default: 60 seconds).
  --strict    Exit non-zero when sky/aws commands fail.
USAGE
}

no_aws=0
force_refresh=0
strict=0
cache_ttl="${MDE_SKY_AWS_TTL:-60}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-aws)
      no_aws=1
      ;;
    --refresh)
      force_refresh=1
      ;;
    --ttl)
      shift
      cache_ttl="$1"
      ;;
    --strict)
      strict=1
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

load_env_file_secrets() {
  local env_file="${MDE_ENV_FILE:-$HOME/.config/macos-development-environment/secrets.env}"
  local override="${MDE_ENV_OVERRIDE:-1}"
  local line key value

  if [[ "${MDE_ENV_AUTOLOAD:-1}" != "1" ]]; then
    return 0
  fi

  if [[ ! -f "$env_file" ]]; then
    return 0
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
    if [[ "$override" != "1" && -n "${!key:-}" ]]; then
      continue
    fi
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

file_mtime() {
  local path="$1"
  if stat -f %m "$path" >/dev/null 2>&1; then
    stat -f %m "$path"
    return 0
  fi
  stat -c %Y "$path"
}

sky_status() {
  local output=""
  local help=""
  local args=()

  if help="$(sky status -h 2>/dev/null)"; then
    if printf '%s' "$help" | grep -q -- '--all-users'; then
      args+=(--all-users)
    elif printf '%s' "$help" | grep -q -- '--all'; then
      args+=(--all)
    fi
  fi

  if output="$(sky status "${args[@]}" 2>/dev/null)"; then
    printf '%s\n' "$output"
    return 0
  fi

  sky status
}

aws_summary() {
  local cache_dir="$HOME/Library/Caches/com.ray-manaloto.macos-dev-maintenance"
  local cache_file="$cache_dir/sky-aws-status.txt"
  local now
  local mtime

  mkdir -p "$cache_dir" 2>/dev/null || true

  now="$(date +%s)"
  if [[ "$force_refresh" -ne 1 && -f "$cache_file" ]]; then
    mtime="$(file_mtime "$cache_file" 2>/dev/null || echo 0)"
    if [[ -n "$mtime" && $((now - mtime)) -lt "$cache_ttl" ]]; then
      log "AWS status (cached, ttl=${cache_ttl}s)."
      cat "$cache_file"
      return 0
    fi
  fi

  if ! command -v aws >/dev/null 2>&1; then
    log "AWS CLI not available. Install with: mise use -g awscli@latest"
    return 1
  fi

  local tmp_file=""
  tmp_file="$(mktemp)"

  local block_status=0
  set +e
  {
    local region="${AWS_DEFAULT_REGION:-${AWS_REGION:-}}"
    if [[ -z "$region" ]]; then
      region="$(aws configure get region 2>/dev/null || true)"
    fi

    if [[ -n "${AWS_PROFILE:-}" ]]; then
      log "AWS profile: $AWS_PROFILE"
    fi
    if [[ -n "$region" ]]; then
      log "AWS region: $region"
    else
      log "WARN: AWS region not set (set AWS_DEFAULT_REGION)."
    fi

    local identity
    identity="$(aws sts get-caller-identity --query 'Account,Arn,UserId' --output text 2>/dev/null || true)"
    if [[ -n "$identity" ]]; then
      local account arn user
      IFS=$'\t' read -r account arn user <<< "$identity"
      log "AWS account: $account"
      log "AWS user: $user"
      log "AWS ARN: $arn"
    else
      log "WARN: Unable to fetch AWS caller identity."
      block_status=1
    fi

    log "EC2 instances (pending/running):"
    if ! aws ec2 describe-instances \
      --filters Name=instance-state-name,Values=pending,running \
      --query 'Reservations[].Instances[].{Id:InstanceId,State:State.Name,Type:InstanceType,AZ:Placement.AvailabilityZone,Name:Tags[?Key==`Name`]|[0].Value,Launch:LaunchTime}' \
      --output table 2>/dev/null; then
      log "WARN: EC2 describe-instances failed."
      block_status=1
    fi
  } > "$tmp_file"
  local cmd_status=$?
  set -e

  cat "$tmp_file"
  mv "$tmp_file" "$cache_file"

  if [[ "$cmd_status" -ne 0 || "$block_status" -ne 0 ]]; then
    return 1
  fi
}

main() {
  setup_path
  load_env_file_secrets

  local status=0

  if ! command -v sky >/dev/null 2>&1; then
    log "SkyPilot CLI not found. Install with: scripts/install-agent-stack.sh"
    return 1
  fi

  log "SkyPilot status:"
  if ! sky_status; then
    log "WARN: sky status failed."
    status=1
  fi

  if [[ "$no_aws" -eq 1 ]]; then
    return 0
  fi

  log "AWS status:"
  if ! aws_summary; then
    status=1
  fi

  if [[ "$strict" -eq 1 && "$status" -ne 0 ]]; then
    return "$status"
  fi

  return 0
}

main "$@"
