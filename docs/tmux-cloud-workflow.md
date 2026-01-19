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

Example commands:
- `sky launch -d -c agent-cluster templates/agent_cloud.yaml`
- `sky status`
- `sky down agent-cluster`

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
