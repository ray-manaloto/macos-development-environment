# Launchd Automation Runbook (AI-Optimized)

Audience: Claude Code / Codex CLI running maintenance and validation on this Mac.
Goal: update tools and managed scripts safely, with a clear command path and logs.

Note: launchd sections are macOS-only. For devcontainer/Linux operations, use
`docs/operational-checklist.md`.

## Scope
This runbook covers the two LaunchAgents and the scripts they invoke:
- Maintenance job (label: `com.ray-manaloto.macos-dev-maintenance`)
- Validation job (label: `com.ray-manaloto.macos-dev-validation`)

It also documents the wrapper scripts and the update order that the jobs enforce.

## Canonical Paths
- Maintenance plist: `~/Library/LaunchAgents/com.ray-manaloto.macos-dev-maintenance.plist`
- Maintenance wrapper: `~/Library/Application Support/com.ray-manaloto.macos-dev-maintenance/macos_dev_maintenance`
- Validation plist: `~/Library/LaunchAgents/com.ray-manaloto.macos-dev-validation.plist`
- Validation wrapper: `~/Library/Application Support/com.ray-manaloto.macos-dev-maintenance/macos_dev_validation`
- Repo scripts:
  - `scripts/macos-dev-maintenance.sh`
  - `scripts/post-setup-run.sh`
  - `scripts/install-validation-launchd.sh`
- Logs:
  - `~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/macos-dev-maintenance.out`
  - `~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/macos-dev-validation.out`
  - `~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/post-setup-summary.log`
  - `~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/post-setup-run.log`

Devcontainer/Linux log root (non-launchd): `~/.local/state/macos-dev-maintenance`.

## TL;DR (Copy/Paste)
```bash
# Install validation LaunchAgent and run it immediately
scripts/install-validation-launchd.sh

# Start maintenance job now
launchctl start com.ray-manaloto.macos-dev-maintenance

# Check job status
launchctl list | rg com.ray-manaloto.macos-dev

# Tail logs
tail -n 200 ~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/macos-dev-maintenance.out
```

## LaunchAgent: Validation (weekly)
Script: `scripts/install-validation-launchd.sh`

What it does:
1) Writes a wrapper to `~/Library/Application Support/com.ray-manaloto.macos-dev-maintenance/macos_dev_validation`.
2) Writes plist `~/Library/LaunchAgents/com.ray-manaloto.macos-dev-validation.plist`.
3) Loads the LaunchAgent with `launchctl load`.

Wrapper behavior:
- Resolves repo root from `MDE_REPO` (defaults to repo root at install time).
- Executes `scripts/post-setup-run.sh` if present.

Validation execution path:
`macos_dev_validation` -> `scripts/post-setup-run.sh` ->
- runs maintenance (wrapper if present, else `scripts/macos-dev-maintenance.sh`)
- runs `scripts/health-check.sh`
- runs `scripts/verify-tmux-setup.sh`
- runs `scripts/verify-tooling.sh`

Expected output:
- `post-setup-summary.log` ends with `Post-setup summary: PASS` or `FAIL`
- `macos-dev-validation.out` contains the launchd run output

Known issue (launchd install):
- The script assumes `~/Library/LaunchAgents` exists. If missing, the plist write will fail.
  Fix: `mkdir -p ~/Library/LaunchAgents` before running `scripts/install-validation-launchd.sh`.

## LaunchAgent: Maintenance (12-hour cadence)
Label: `com.ray-manaloto.macos-dev-maintenance`

The plist is expected at:
`~/Library/LaunchAgents/com.ray-manaloto.macos-dev-maintenance.plist`

Preferred remediation path now includes an installer/repair flow:
- `mise run mde:remediate` (creates/loads maintenance plist + wrapper, then
  validates status).
- `mise run mde:remediate --check` verifies launchd state without mutation.

Wrapper behavior:
- Expected wrapper path: `~/Library/Application Support/com.ray-manaloto.macos-dev-maintenance/macos_dev_maintenance`
- Repo fallback: `scripts/macos-dev-maintenance.sh` (direct run)

## Maintenance Script: `scripts/macos-dev-maintenance.sh`
Purpose: update toolchain and managed scripts in a deterministic order.

Key environment flags:
- `MDE_AUTOFIX` (default 0 here, defaults to 1 in the plist)
- `MDE_AUTOFIX_STRICT` (default 0)
- `MDE_UPDATE_AGENT_TOOLS` (default 1)
- `MDE_UPDATE_MCP` (default 1)
- `MDE_UPDATE_OMZ` (default 0)
- `MDE_UV_CACHE_PRUNE` (default 0)

Secrets loading order:
1) `mise env` with `fnox` (`~/.config/fnox/config.toml` plus repo overlays)
2) 1Password service account (`OP_SERVICE_ACCOUNT_TOKEN`)
3) Provider-backed values such as Keychain or repo-local `fnox.local.toml`

Update sequence (high level):
1) Homebrew formula + cask upgrades (skips sudo-only casks like `osquery`)
2) `mise` self-update, runtime upgrades, reshim
3) `bun` global update
4) cleanup duplicate CLIs (`claude`, `gemini`)
5) `uv` self update (non-Homebrew installs) + tool upgrades
6) `pixi` self update + global update
7) agent tool updates (if enabled)
8) MCP server sync (if enabled)
9) oh-my-zsh update (if enabled)
10) always-on config sync (`scripts/ensure-managed-configs.sh`, chezmoi-first)
11) optional auto-fix (remove conflicting managers, tmux plugins)

Failure behavior:
- A non-zero exit from any step yields a non-zero overall exit.
- Launchd logs capture the failure context.

## Secret Authority
- Host and repo automation use `mise` + `fnox` for secret resolution.
- No plaintext repo-managed secret file is required for supported flows.

## Validation / Troubleshooting
- Status dashboard: `scripts/status-dashboard.sh`
- Health check: `scripts/health-check.sh`
- Full verification: `scripts/verify-all.sh`
- Deterministic repair entrypoint: `scripts/mde-remediate.sh`
- Launchd status:
  - `launchctl list | rg com.ray-manaloto.macos-dev`
  - `launchctl start com.ray-manaloto.macos-dev-maintenance`

### Trust/Bootstrap Failure Signatures
If config sync fails during bootstrap or verification with errors like:
- `not trusted`
- `error parsing config file`
- `source state ... not initialized`

Recovery sequence:
1. `mise trust`
2. `scripts/ensure-managed-configs.sh`
3. `mise run mde:update`
4. `scripts/mde-verify --json`

## Known Issues / History (from git + chat)
- SkyPilot API server sometimes left a stale process on port 46580. The status
  script now kills stale listeners before checking. (git history)
- AWS caller identity warning was caused by an invalid JMESPath query and has
  been corrected in `scripts/sky-status.sh` (chat history).
- Large instance types are now highlighted by the status script to reduce cost
  surprises (chat history).

## Reader Checklist (AI)
- Confirm `~/Library/LaunchAgents` exists.
- Confirm plist files exist and are loaded.
- Check logs for last run.
- If missing, run `scripts/install-validation-launchd.sh` and start maintenance.
