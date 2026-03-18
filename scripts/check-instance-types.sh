#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

COLLECTOR_CLUSTER="rm-rmanaloto-mde-otel-gw-prod-use1"
GRAFANA_CLUSTER="rm-rmanaloto-mde-graf-prod-use1"
RDS_CLUSTER="rds-postgres"

declare -A CLUSTER_CONFIGS=(
  ["$COLLECTOR_CLUSTER"]="configs/skypilot/otel-gateway.yaml"
  ["$GRAFANA_CLUSTER"]="configs/skypilot/grafana-stack.yaml"
  ["$RDS_CLUSTER"]="configs/skypilot/rds-postgres.yaml"
)

fail() { echo "[FAIL] $1" >&2; exit 1; }
info() { echo "[INFO] $1"; }

read_expected_instance_type() {
  local config="$1"
  [[ -f "$config" ]] || fail "Expected config not found: $config"
  awk -F: '
    /^[[:space:]]*instance_type:/ {
      gsub(/#.*/, "", $2);
      gsub(/[[:space:]]/, "", $2);
      print $2;
      exit;
    }
  ' "$config"
}

read_actual_instance_type() {
  local cluster="$1"
  local status_output=""
  if [[ -n "${SKY_STATUS_OUTPUT:-}" ]]; then
    status_output="$SKY_STATUS_OUTPUT"
  else
    status_output="$(sky status -v "$cluster")"
  fi

  local line=""
  line=$(printf '%s\n' "$status_output" | awk -v c="$cluster" '$1 == c {print; exit}')
  [[ -n "$line" ]] || fail "Cluster $cluster not found in sky status output"

  local instance=""
  instance=$(printf '%s\n' "$line" | awk '
    {
      start = index($0, "1x(");
      if (start == 0) {
        next;
      }
      rest = substr($0, start + 3);
      end = index(rest, ")");
      if (end == 0) {
        next;
      }
      resources = substr(rest, 1, end - 1);
      n = split(resources, parts, ",");
      if (n >= 3) {
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", parts[3]);
        print parts[3];
        exit;
      }
    }
  ')
  [[ -n "$instance" ]] || fail "Unable to parse instance type for $cluster"
  printf '%s\n' "$instance"
}

for cluster in "${!CLUSTER_CONFIGS[@]}"; do
  config="${CLUSTER_CONFIGS[$cluster]}"
  expected="$(read_expected_instance_type "$config")"
  [[ -n "$expected" ]] || fail "Missing instance_type in $config"
  actual="$(read_actual_instance_type "$cluster")"
  if [[ "$expected" != "$actual" ]]; then
    fail "Instance type mismatch for $cluster: expected $expected, got $actual"
  fi
  info "$cluster instance type OK ($actual)"
done

echo "[OK] Instance type validation passed"
