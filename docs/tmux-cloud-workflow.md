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

## Tmux Config
The script writes `~/.tmux.conf` and creates a timestamped backup if one
already exists. Highlights:
- `tmux-256color` + RGB for accurate colors
- `set-clipboard on` for macOS clipboard support
- `prefix` stays at `C-b` with `C-a` as a secondary prefix
- Mouse support and large history for log review

## Cloud Burst (SkyPilot)
Template:
- `templates/agent_cloud.yaml`

Example commands:
- `sky launch -d -c agent-cluster templates/agent_cloud.yaml`
- `sky status`
- `sky down agent-cluster`

## Aliases (oh-my-zsh)
These are provided in `~/.oh-my-zsh/custom/aliases.zsh`:
- `cloud-run`
- `cloud-ssh`
- `cloud-view`
- `cloud-stop`

## Agent HUD
Launch the tmux layout:

```bash
scripts/agent-hud
```

Windows:
- `CODE`: editor
- `BRAIN`: langgraph dev + CLI pane
- `CLOUD`: SkyPilot status
