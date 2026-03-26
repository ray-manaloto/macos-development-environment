# devcontainer-toolkit

Expert devcontainer management plugin for Claude Code with deep knowledge of the
Dev Container specification, lifecycle events, Docker Compose integration, CLI
automation, and feature system.

## Components

### Agent
- **devcontainer-specialist** — Autonomous devcontainer expert with full lifecycle,
  compose integration, and CLI knowledge. Triggers proactively when editing
  devcontainer.json or designing container-based dev environments.

### Skills
- **devcontainer-lifecycle** — 6 lifecycle events, execution order, parallel commands, failure semantics
- **devcontainer-compose** — Docker Compose integration patterns and decision framework
- **devcontainer-cli** — CLI commands, flags, CI/CD patterns
- **devcontainer-features** — Feature system, registries, composability
- **devcontainer-setup** — Project-aware devcontainer.json generation (`/devcontainer-setup`)

## Key Knowledge

This plugin knows the critical distinction between two compose patterns:
- **Pattern A** (dockerComposeFile): When compose service IS the dev container
- **Pattern B** (postStartCommand): When compose services are sidecar infrastructure

And all 6 lifecycle events in strict execution order:
```
HOST:       initializeCommand
CONTAINER:  onCreateCommand → updateContentCommand → postCreateCommand
ON START:   postStartCommand (runs every restart — ideal for sidecar services)
ON ATTACH:  postAttachCommand
```

## Installation

Project-level (already installed at `.claude/plugins/devcontainer-toolkit/`).
