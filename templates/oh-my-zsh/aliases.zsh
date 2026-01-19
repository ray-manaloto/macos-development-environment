#!/usr/bin/env zsh
# Managed by macos-development-environment.

# Cloud workflow (SkyPilot)
alias cloud-run='sky launch -d -c agent-cluster agent_cloud.yaml'
alias cloud-ssh='ssh agent-cluster'
alias cloud-view='ssh -L 8123:localhost:8123 agent-cluster'
alias cloud-stop='sky down agent-cluster'

# Agent HUD helper (keeps repo script as source of truth)
alias agent-hud="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/agent-hud"
alias mde-status="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/status-dashboard.sh"
alias mde-mcp-sync="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/setup-mcp-servers.sh"
alias firebase="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/firebase-wrapper.sh"
