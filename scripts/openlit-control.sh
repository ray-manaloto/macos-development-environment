#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: openlit-control.sh <action> [options]

Actions (SkyPilot):
  deploy        Provision OpenLIT via SkyPilot (AWS)
  update        Pull OpenLIT + restart Docker on the SkyPilot cluster
  status        Show SkyPilot cluster status
  endpoints     Show SkyPilot endpoints + IP
  env           Print or write OTEL/OpenLIT env vars for local tools
  start         Start the SkyPilot cluster
  stop          Stop the SkyPilot cluster
  down          Tear down the SkyPilot cluster

Actions (Kubernetes):
  k8s-deploy    Apply OpenLIT manifest with kubectl
  k8s-update    Re-apply OpenLIT manifest
  k8s-status    Show OpenLIT pods/services
  k8s-down      Delete OpenLIT manifest
  k8s-env       Write env vars (requires --endpoint)

Options:
  --cluster NAME        SkyPilot cluster name (default: openlit-cluster)
  --config PATH         SkyPilot config path (default: configs/openlit-skypilot.yaml)
  --env-file PATH       Env file to update (default: ~/.config/macos-development-environment/secrets.env)
  --endpoint URL        Override endpoint for env output
  --write-env           Write env vars to the env file
  --k8s-manifest PATH   Kubernetes manifest for OpenLIT
  --namespace NAME      Kubernetes namespace (default: openlit)
USAGE
}

action="${1:-}"
if [[ -z "$action" ]]; then
  usage >&2
  exit 2
fi
shift

cluster="${OPENLIT_CLUSTER:-openlit-cluster}"
config_path=""
write_env=0
endpoint_override=""
env_file="${MDE_ENV_FILE:-$HOME/.config/macos-development-environment/secrets.env}"

k8s_manifest="${OPENLIT_K8S_MANIFEST:-}"
namespace="${OPENLIT_K8S_NAMESPACE:-openlit}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cluster)
      cluster="$2"
      shift
      ;;
    --config)
      config_path="$2"
      shift
      ;;
    --env-file)
      env_file="$2"
      shift
      ;;
    --endpoint)
      endpoint_override="$2"
      shift
      ;;
    --write-env)
      write_env=1
      ;;
    --k8s-manifest)
      k8s_manifest="$2"
      shift
      ;;
    --namespace)
      namespace="$2"
      shift
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

set_env_line() {
  local file="$1"
  local key="$2"
  local value="$3"
  local tmp

  [[ -z "$value" ]] && return 1

  tmp="$(mktemp)"
  if [[ -f "$file" ]]; then
    grep -v "^${key}=" "$file" > "$tmp" || true
  fi
  printf '%s=%s\n' "$key" "$value" >> "$tmp"
  mv "$tmp" "$file"
  chmod 600 "$file" 2>/dev/null || true
}

get_env_value() {
  local file="$1"
  local key="$2"
  if [[ -f "$file" ]]; then
    grep -E "^${key}=" "$file" 2>/dev/null | tail -n1 | sed -e "s/^${key}=//" || true
  fi
}

ensure_config() {
  local repo_root="$1"
  local default_cfg="$repo_root/configs/openlit-skypilot.yaml"

  if [[ -n "$config_path" ]]; then
    return 0
  fi
  config_path="$default_cfg"
}

sky_status_flag() {
  local flag="$1"
  local help=""

  if help="$(sky status -h 2>/dev/null)"; then
    if command -v rg >/dev/null 2>&1; then
      if printf '%s' "$help" | rg -q -- "${flag}"; then
        printf '%s' "$flag"
        return 0
      fi
    else
      if printf '%s' "$help" | grep -q -- "${flag}"; then
        printf '%s' "$flag"
        return 0
      fi
    fi
  fi
  return 1
}

sky_cluster_ip() {
  local output=""
  local flag=""
  local ip=""
  local re="[0-9]{1,3}(\.[0-9]{1,3}){3}"

  if flag="$(sky_status_flag '--ip')"; then
    output="$(sky status $flag "$cluster" 2>/dev/null || true)"
  else
    output="$(sky status "$cluster" 2>/dev/null || true)"
  fi

  if command -v rg >/dev/null 2>&1; then
    ip="$(printf '%s' "$output" | rg -o "$re" | head -n1)"
  else
    ip="$(printf '%s' "$output" | grep -Eo "$re" | head -n1 || true)"
  fi

  if [[ -n "$ip" ]]; then
    printf '%s' "$ip"
    return 0
  fi

  if flag="$(sky_status_flag '--endpoints')"; then
    output="$(sky status $flag "$cluster" 2>/dev/null || true)"
    if command -v rg >/dev/null 2>&1; then
      printf '%s' "$output" | rg -o "$re" | head -n1
      return 0
    fi
    printf '%s' "$output" | grep -Eo "$re" | head -n1 || true
  fi
}

openlit_endpoint() {
  local ip=""

  if [[ -n "$endpoint_override" ]]; then
    printf '%s' "$endpoint_override"
    return 0
  fi

  ip="$(sky_cluster_ip)"
  if [[ -z "$ip" ]]; then
    return 1
  fi

  printf 'http://%s:4318' "$ip"
}

sky_deploy() {
  local repo_root=""
  local help=""
  local detach_flag=""

  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  ensure_config "$repo_root"

  if [[ ! -f "$config_path" ]]; then
    log "Missing SkyPilot config: $config_path"
    exit 1
  fi

  cd "$repo_root" || exit 1

  if help="$(sky launch -h 2>/dev/null)"; then
    if printf '%s' "$help" | rg -q -- '--detach-run'; then
      detach_flag="--detach-run"
    elif printf '%s' "$help" | rg -q -- '--detach'; then
      detach_flag="--detach"
    fi
  fi

  if [[ -n "$detach_flag" ]]; then
    sky launch -y -c "$cluster" "$config_path" "$detach_flag"
  else
    sky launch -y -c "$cluster" "$config_path"
  fi
  log "OpenLIT deployed on SkyPilot cluster: $cluster"
}

sky_update() {
  sky exec "$cluster" -- "cd openlit && git pull && sudo docker compose up -d"
  log "OpenLIT updated on SkyPilot cluster: $cluster"
}

sky_status() {
  sky status "$cluster"
}

sky_endpoints() {
  local flag=""
  if flag="$(sky_status_flag '--endpoints')"; then
    sky status $flag "$cluster"
    return 0
  fi
  sky status "$cluster"
}

sky_env() {
  local endpoint=""
  local otlp_protocol="http/protobuf"
  local ui_user=""
  local ui_pass=""
  endpoint="$(openlit_endpoint || true)"

  if [[ -z "$endpoint" ]]; then
    log "Unable to determine OpenLIT endpoint. Use --endpoint or ensure cluster is running."
    return 1
  fi

  ui_user="${OPENLIT_UI_USER:-$(get_env_value "$env_file" "OPENLIT_UI_USER")}"
  ui_pass="${OPENLIT_UI_PASSWORD:-$(get_env_value "$env_file" "OPENLIT_UI_PASSWORD")}"
  if [[ -z "$ui_user" ]]; then
    ui_user="admin@example.com"
  fi
  if [[ -z "$ui_pass" ]]; then
    if command -v openssl >/dev/null 2>&1; then
      ui_pass="$(openssl rand -base64 18 | tr -d '=/[:space:]')"
    else
      ui_pass="changeme-openlit"
    fi
    log "Generated OpenLIT UI password; stored in $env_file."
  fi

  if [[ "$write_env" -eq 1 ]]; then
    mkdir -p "$(dirname "$env_file")" 2>/dev/null || true
    set_env_line "$env_file" "OPENLIT_ENDPOINT" "$endpoint"
    set_env_line "$env_file" "OTEL_EXPORTER_OTLP_ENDPOINT" "$endpoint"
    set_env_line "$env_file" "OTEL_EXPORTER_OTLP_PROTOCOL" "$otlp_protocol"
    set_env_line "$env_file" "GEMINI_TELEMETRY_ENABLED" "1"
    set_env_line "$env_file" "GEMINI_TELEMETRY_TARGET" "local"
    set_env_line "$env_file" "GEMINI_TELEMETRY_OTLP_ENDPOINT" "$endpoint"
    set_env_line "$env_file" "GEMINI_TELEMETRY_OTLP_PROTOCOL" "http"
    set_env_line "$env_file" "GEMINI_TELEMETRY_LOG_PROMPTS" "1"
    set_env_line "$env_file" "OPENLIT_UI_USER" "$ui_user"
    set_env_line "$env_file" "OPENLIT_UI_PASSWORD" "$ui_pass"
    log "Updated $env_file with OpenLIT OTLP settings."
    return 0
  fi

  cat <<EOF_ENV
export OPENLIT_ENDPOINT="$endpoint"
export OTEL_EXPORTER_OTLP_ENDPOINT="$endpoint"
export OTEL_EXPORTER_OTLP_PROTOCOL="$otlp_protocol"
export GEMINI_TELEMETRY_ENABLED="1"
export GEMINI_TELEMETRY_TARGET="local"
export GEMINI_TELEMETRY_OTLP_ENDPOINT="$endpoint"
export GEMINI_TELEMETRY_OTLP_PROTOCOL="http"
export GEMINI_TELEMETRY_LOG_PROMPTS="1"
export OPENLIT_UI_USER="$ui_user"
export OPENLIT_UI_PASSWORD="$ui_pass"
EOF_ENV
}

k8s_requirements() {
  if ! command -v kubectl >/dev/null 2>&1; then
    log "kubectl not found. Install with scripts/install-aws-k8s-tools.sh"
    exit 1
  fi

  if [[ -z "$k8s_manifest" ]]; then
    log "Missing --k8s-manifest (OPENLIT_K8S_MANIFEST)."
    exit 1
  fi
}

k8s_deploy() {
  k8s_requirements
  if ! kubectl get namespace "$namespace" >/dev/null 2>&1; then
    kubectl create namespace "$namespace"
  fi
  kubectl apply -n "$namespace" -f "$k8s_manifest"
  kubectl -n "$namespace" rollout status deployment --timeout=120s || true
}

k8s_update() {
  k8s_requirements
  kubectl apply -n "$namespace" -f "$k8s_manifest"
}

k8s_status() {
  k8s_requirements
  kubectl -n "$namespace" get pods,svc
}

k8s_down() {
  k8s_requirements
  kubectl delete -n "$namespace" -f "$k8s_manifest"
}

k8s_env() {
  if [[ -z "$endpoint_override" ]]; then
    log "Provide --endpoint to write env vars for Kubernetes." >&2
    exit 1
  fi
  write_env=1
  sky_env
}

main() {
  setup_path

  case "$action" in
    deploy)
      sky_deploy
      ;;
    update)
      sky_update
      ;;
    status)
      sky_status
      ;;
    endpoints)
      sky_endpoints
      ;;
    env)
      sky_env
      ;;
    start)
      sky start "$cluster"
      ;;
    stop)
      sky stop "$cluster"
      ;;
    down)
      sky down "$cluster"
      ;;
    k8s-deploy)
      k8s_deploy
      ;;
    k8s-update)
      k8s_update
      ;;
    k8s-status)
      k8s_status
      ;;
    k8s-down)
      k8s_down
      ;;
    k8s-env)
      k8s_env
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
}

main "$@"
