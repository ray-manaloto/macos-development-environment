# SkyPilot + AWS Setup (AI-Optimized)

Audience: Claude Code / Codex CLI executing cloud setup and cost controls.
Goal: configure AWS credentials, verify SkyPilot access, and manage clusters safely.

## Required Tools
- AWS CLI (`aws`)
- SkyPilot CLI (`sky`)

Recommended check:
```bash
aws --version
sky --version
```

## Secrets and Credentials
Primary source: `fnox` loaded through `mise`

Required keys for SkyPilot:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION` (recommended)

Optional:
- `MDE_AWS_PROFILE` (default `default`)

### What the setup script does
Script: `scripts/setup-skypilot-aws.sh`

- Loads `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` from `mise` + `fnox`.
- Writes `~/.aws/credentials` and `~/.aws/config` if not already managed.
- Adds a marker line to avoid overwriting non-managed files.
- Optionally creates `agent_cloud.yaml` from template.
- Runs `sky check aws` (with or without env, depending on `MDE_AWS_KEEP_ENV_FOR_SKY_CHECK`).
- Restarts SkyPilot API server by default (prevents stale port issues).

Command:
```bash
scripts/setup-skypilot-aws.sh --init-config
```

If `agent_cloud.yaml` already exists, add `--force` to overwrite.

## SkyPilot Status and Cost Signals
Script: `scripts/sky-status.sh`

Key behavior:
- Shows `sky status` output for your user.
- Fetches AWS account identity and running instances.
- Adds a large-instance warning table (size >= xlarge).
- Supports `--sky-only` to filter to `Name` tags starting with `sky-`.
- Caches AWS output for 60 seconds (override via `--ttl` or `--refresh`).

Examples:
```bash
scripts/sky-status.sh --refresh
scripts/sky-status.sh --sky-only --refresh
```

Large instance warning criteria:
- Instance type contains `xlarge` or `metal`.
- Adds hint: "large instance; check on-demand price".

## Stop/Start/Status Commands (documented)
There are no dedicated stop/start scripts in this repo today; use the CLI
commands below and `scripts/sky-status.sh` for status.

SkyPilot clusters (user-scoped):
```bash
# Stop all clusters for current user
sky stop -a -y

# Start a specific cluster
sky start <cluster-name>

# Status
sky status
```

Notes:
- Spot instances cannot be stopped (SkyPilot behavior).
- Stopping halts compute billing but EBS costs remain.

AWS EC2 (manual, use only for instances you own):
```bash
aws ec2 describe-instances --filters Name=instance-state-name,Values=pending,running --output table
aws ec2 stop-instances --instance-ids <id>
aws ec2 start-instances --instance-ids <id>
```

## AWS Login (Access Key / Secret Key)
This environment primarily uses static keys loaded from `fnox`.

If keys are present, `scripts/setup-skypilot-aws.sh` writes them to:
- `~/.aws/credentials` (profile: `MDE_AWS_PROFILE` or `default`)
- `~/.aws/config` (region + output json)

If keys are not present, the script skips writing and requires you to set
credentials externally.

AWS account id currently in use (from status): `532150070252`

## SkyPilot + AWS Validation
- `scripts/setup-skypilot-aws.sh` performs `sky check aws`.
- `scripts/sky-status.sh` prints account identity and instances.
- `scripts/validate-otel-stack.sh` verifies OTEL + Grafana + RDS when enabled.
  - Requires `GRAFANA_PASSWORD` and `DB_PASSWORD` in `fnox`.

## OpenLIT / OTEL Stack Requirements
If using SkyPilot to provision the RDS instance for the OTEL stack:
- Instance role must allow:
  - `rds:DescribeDBInstances`
  - `rds:CreateDBInstance`

Related docs: `docs/openlit-telemetry.md`

## History / Known Issues (git + chat)
- Stale SkyPilot API server on port 46580 can cause status issues.
  `scripts/sky-status.sh` kills stale listeners (commit history).
- AWS caller identity warning was caused by invalid JMESPath syntax and fixed
  in `scripts/sky-status.sh` (chat history).
- Large instance types are now flagged to avoid accidental cost spikes
  (chat history).
- AWS tools and status flows were hardened over time (git history).
- SkyPilot RDS tasks require IAM permissions for `DescribeDBInstances` and
  `CreateDBInstance` (git history).

## Chat History Timeline (local)
- 2026-01-23: `sky stop -a -y` used to stop all SkyPilot clusters.
- 2026-01-23: `i-0b0329816b11d057f` (`sky-grafana-server-3f4baec1-head`) was
  still running and was stopped via `aws ec2 stop-instances`. This indicates
  non-cluster EC2 resources may persist and need manual review.

## Local / Uncommitted Context (current working tree)
The working tree includes local-only additions (not committed) in directories
like `.agent/`, `.agents/`, `.claude/`, `.codex/`, `.cursor/`, `.gemini/`,
`.github/`, `.kiro/`, `.opencode/`, `.windsurf/`, plus additional configs and
scripts. Run `git status -sb` before assuming repo parity.

## Reader Checklist (AI)
- Ensure `fnox` has AWS keys and region.
- Run `scripts/setup-skypilot-aws.sh --init-config`.
- Run `scripts/sky-status.sh --refresh` and check large-instance warnings.
- Use `sky stop -a -y` to pause cost if needed (not spot).
