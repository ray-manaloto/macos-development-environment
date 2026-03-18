#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

pass_output=$'Enabled Infra: aws\n\nClusters\nNAME                                WORKSPACE  INFRA             RESOURCES                              STATUS  AUTOSTOP  LAUNCHED    HEAD_IP         COMMAND\nrm-rmanaloto-mde-otel-gw-prod-use1   default    AWS (us-east-1a)  1x(cpus=2, mem=2, t3.small, disk=50)   UP      -         7 mins ago  54.0.0.1        sky launch ...\nrm-rmanaloto-mde-graf-prod-use1      default    AWS (us-east-1a)  1x(cpus=2, mem=8, t3.large, disk=100)  UP      -         7 mins ago  54.0.0.2        sky launch ...\nrds-postgres                        default    AWS (us-east-1a)  1x(cpus=2, mem=2, t3.small, disk=256)  UP      -         7 mins ago  54.0.0.3        sky launch ...\n'

fail_output=$'Enabled Infra: aws\n\nClusters\nNAME                                WORKSPACE  INFRA             RESOURCES                              STATUS  AUTOSTOP  LAUNCHED    HEAD_IP         COMMAND\nrm-rmanaloto-mde-otel-gw-prod-use1   default    AWS (us-east-1a)  1x(cpus=2, mem=2, t3.small, disk=50)   UP      -         7 mins ago  54.0.0.1        sky launch ...\nrm-rmanaloto-mde-graf-prod-use1      default    AWS (us-east-1a)  1x(cpus=2, mem=8, m5.large, disk=100)  UP      -         7 mins ago  54.0.0.2        sky launch ...\nrds-postgres                        default    AWS (us-east-1a)  1x(cpus=2, mem=2, t3.small, disk=256)  UP      -         7 mins ago  54.0.0.3        sky launch ...\n'

SKY_STATUS_OUTPUT="$pass_output" scripts/check-instance-types.sh

if SKY_STATUS_OUTPUT="$fail_output" scripts/check-instance-types.sh >/dev/null 2>&1; then
  echo "Expected instance type validation to fail, but it passed"
  exit 1
fi
