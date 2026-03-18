#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

SCRIPT_DIR="$(pwd)/scripts"
# shellcheck source=scripts/lib/mde-secrets.sh
source "$SCRIPT_DIR/lib/mde-secrets.sh"

mode="full"
for arg in "$@"; do
  case "$arg" in
    --check-instance-types)
      mode="instance-types"
      ;;
    -h|--help)
      echo "Usage: $0 [--check-instance-types]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

mde_load_secrets

COLLECTOR_CLUSTER="rm-rmanaloto-mde-otel-gw-prod-use1"
GRAFANA_CLUSTER="rm-rmanaloto-mde-graf-prod-use1"
DB_INSTANCE_ID="${DB_INSTANCE_ID:-rm-rmanaloto-mde-rds-prod-use1}"
AWS_REGION="${AWS_REGION:-us-east-1}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-}"

fail() { echo "[FAIL] $1" >&2; exit 1; }
info() { echo "[INFO] $1"; }

auth_opt=()
if [[ -n "$GRAFANA_PASSWORD" ]]; then
  auth_opt=(-u "admin:${GRAFANA_PASSWORD}")
else
  info "GRAFANA_PASSWORD not set; Grafana login check will be skipped"
fi

if [[ "$mode" == "instance-types" ]]; then
  scripts/check-instance-types.sh
  exit 0
fi

# Check clusters exist
for c in "$COLLECTOR_CLUSTER" "$GRAFANA_CLUSTER"; do
  if ! sky status "$c" >/dev/null 2>&1; then
    fail "SkyPilot cluster $c not found"
  fi
done

# Collector health
info "Checking collector service on $COLLECTOR_CLUSTER"
sky exec "$COLLECTOR_CLUSTER" -- bash -lc "set -euo pipefail; sudo systemctl is-active --quiet otelcol && curl -sSf http://localhost:8888/metrics | head -n1" >/dev/null || fail "Collector health check failed"
info "Collector healthy"

# Grafana stack health
info "Checking Grafana stack on $GRAFANA_CLUSTER"
sky exec "$GRAFANA_CLUSTER" -- bash -lc "set -euo pipefail; docker compose -f ~/grafana-stack/docker-compose.yaml ps" >/dev/null || fail "Docker compose not healthy"

auth_cmd=""
if [[ ${#auth_opt[@]} -gt 0 ]]; then
  auth_cmd="-u admin:${GRAFANA_PASSWORD}"
fi

sky exec "$GRAFANA_CLUSTER" -- bash -lc "set -euo pipefail; curl -sSf ${auth_cmd} http://localhost:3000/api/health" >/dev/null || fail "Grafana API health failed"
sky exec "$GRAFANA_CLUSTER" -- bash -lc "set -euo pipefail; curl -sSf http://localhost:3200/status" >/dev/null || fail "Tempo status failed"
sky exec "$GRAFANA_CLUSTER" -- bash -lc "set -euo pipefail; curl -sSf 'http://localhost:3100/loki/api/v1/status/buildinfo'" >/dev/null || fail "Loki status failed"
sky exec "$GRAFANA_CLUSTER" -- bash -lc "set -euo pipefail; curl -sSf http://localhost:8080/ready" >/dev/null || fail "Mimir status failed"
info "Grafana/Tempo/Loki/Mimir healthy"

# RDS status
info "Checking RDS instance $DB_INSTANCE_ID"
aws rds describe-db-instances --db-instance-identifier "$DB_INSTANCE_ID" --region "$AWS_REGION" --query "DBInstances[0].{Status:DBInstanceStatus,Endpoint:Endpoint.Address,Port:Endpoint.Port}" --output table >/dev/null || fail "RDS describe failed"
info "RDS reachable via AWS API"

scripts/check-instance-types.sh

echo "[OK] OTEL stack validation passed"
