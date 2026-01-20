# Tmux + Cloud Workflow

This workflow turns tmux into a persistent dashboard and uses SkyPilot to
run heavy agent tasks in the cloud.

## Install / Update

```bash
scripts/optimize-tmux.sh
```

Notes:
- On macOS, Homebrew tmux is recommended for clipboard integration.
- Force pixi with `TMUX_INSTALL=pixi scripts/optimize-tmux.sh`.
- TPM plugins are installed automatically (no prefix + I needed).
- Verification: `scripts/verify-tmux-setup.sh` (runs in weekly validation).

## Tmux Config
The script writes `~/.tmux.conf` from `templates/tmux.conf`. It only replaces
files that are already managed (contain the managed header). Use
`TMUX_FORCE_CONF=1` to override. A timestamped backup is created when
overwriting. Highlights:
- `tmux-256color` + RGB for accurate colors
- `set-clipboard on` for macOS clipboard support
- Status bar includes AWS profile + MDE dashboard summary
  (`scripts/status-dashboard.sh --tmux`)
- `prefix` stays at `C-b` with `C-a` as a secondary prefix
- Mouse support and large history for log review

## Cloud Burst (SkyPilot)
Template:
- `templates/agent_cloud.yaml`

Setup (AWS credentials from secrets.env):
- `scripts/setup-skypilot-aws.sh --init-config`
  - Creates `agent_cloud.yaml` in the repo root (copy of template).
  - Runs `sky check aws` to validate credentials.

Example commands:
- `sky launch -d -c agent-cluster agent_cloud.yaml`
- `scripts/sky-status.sh` (or `cloud-status` alias)
- `sky down agent-cluster`

Status notes:
- `scripts/sky-status.sh` adds AWS account + EC2 details after `sky status`.
- Cached AWS output defaults to 60s (override with `MDE_SKY_AWS_TTL=120`).
- Install AWS CLI for the extra AWS output (`mise use -g awscli@latest`).

Template notes:
- Uses `uv` for Python package installs on the remote host.

## Aliases (oh-my-zsh)
These are provided in `~/.oh-my-zsh/custom/aliases.zsh`:
- `cloud-run`
- `cloud-ssh`
- `cloud-view`
- `cloud-stop`
- `mde-status`

## Agent HUD
Launch the tmux layout:

```bash
scripts/agent-hud
```

Windows:
- `CODE`: editor
- `BRAIN`: langgraph dev + CLI pane
- `CLOUD`: SkyPilot status
