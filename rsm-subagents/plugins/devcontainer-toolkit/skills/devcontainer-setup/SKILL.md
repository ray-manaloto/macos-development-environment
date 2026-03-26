---
name: devcontainer-setup
description: >
  This skill should be used when the user asks to "create a devcontainer",
  "set up a dev container", "initialize devcontainer.json", "add devcontainer to project",
  "configure development container", "devcontainer from scratch", or wants to create a
  new devcontainer configuration from scratch based on project analysis.
---

# Dev Container Setup

## Overview

Create a complete devcontainer configuration by analyzing the project and generating
appropriate devcontainer.json with lifecycle events, features, port forwarding, and
optional Docker Compose integration.

## Setup Process

### 1. Analyze Project

Detect project characteristics to determine configuration:

```bash
# Detect languages and frameworks
ls package.json pyproject.toml Cargo.toml go.mod Gemfile *.csproj 2>/dev/null
# Detect existing Docker files
ls Dockerfile docker-compose*.yml .dockerignore 2>/dev/null
# Detect existing devcontainer config
ls .devcontainer/devcontainer.json .devcontainer.json 2>/dev/null
```

### 2. Select Base Image

Choose based on detected project type:
- **Multi-language**: `mcr.microsoft.com/devcontainers/base:ubuntu`
- **Python**: `mcr.microsoft.com/devcontainers/python:3.12`
- **Node.js**: `mcr.microsoft.com/devcontainers/javascript-node:22`
- **Rust**: `mcr.microsoft.com/devcontainers/rust:1`
- **Go**: `mcr.microsoft.com/devcontainers/go:1`

### 3. Configure Features

Add features based on detected tooling needs:
- Docker usage → `ghcr.io/devcontainers/features/docker-in-docker:2`
- Node.js needed → `ghcr.io/devcontainers/features/node:1`
- Python needed → `ghcr.io/devcontainers/features/python:1`
- GitHub CLI → `ghcr.io/devcontainers/features/github-cli:1`

### 4. Configure Lifecycle Events

Map project setup steps to appropriate events:

| Project step | Lifecycle event | Rationale |
|-------------|----------------|-----------|
| OS packages | onCreateCommand | One-time setup |
| `npm install` / `pip install` | updateContentCommand | Refresh on content changes |
| Build/compile | postCreateCommand | After deps installed |
| Dev servers | postStartCommand | Every container start |
| Sidecar compose services | postStartCommand | Independent lifecycle |

### 5. Configure Ports and Environment

Forward ports for dev servers and sidecar services. Set environment variables
for development mode.

### 6. Add IDE Customizations

Configure VS Code extensions and settings relevant to the project:
```json
{
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python", "charliermarsh.ruff"],
      "settings": { "python.defaultInterpreterPath": "/usr/local/bin/python" }
    }
  }
}
```

## Common Patterns

### Python + Database
```json
{
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  "features": { "ghcr.io/devcontainers/features/docker-in-docker:2": {} },
  "onCreateCommand": "pip install -e '.[dev]'",
  "postStartCommand": {
    "db": "docker compose up -d postgres",
    "migrate": "sleep 3 && python manage.py migrate"
  },
  "forwardPorts": [8000, 5432]
}
```

### Node.js Full Stack
```json
{
  "image": "mcr.microsoft.com/devcontainers/javascript-node:22",
  "postCreateCommand": "npm ci",
  "postStartCommand": "npm run dev",
  "forwardPorts": [3000, 5173]
}
```

### GPU Development
```json
{
  "image": "nvidia/cuda:11.8-runtime-ubuntu22.04",
  "hostRequirements": { "gpu": true },
  "runArgs": ["--gpus", "all"],
  "features": { "ghcr.io/devcontainers/features/python:1": { "version": "3.11" } }
}
```

### Cache Persistence
```json
{
  "mounts": [
    { "source": "npm-cache", "target": "/home/node/.npm", "type": "volume" },
    { "source": "pip-cache", "target": "/home/node/.cache/pip", "type": "volume" }
  ]
}
```

## Quality Checklist

After generating devcontainer.json, verify:
- [ ] Feature versions pinned for reproducibility
- [ ] Named volumes for caches (node_modules, pip, cargo)
- [ ] `init: true` set to prevent zombie processes
- [ ] Port labels descriptive in portsAttributes
- [ ] Lifecycle events use correct scope (host vs container)
- [ ] Sidecar services use appropriate pattern (see devcontainer-compose skill)

## Additional Resources

### Reference Files

For complete property reference and advanced patterns:
- **`references/common-patterns.md`** — GPU, DinD, multi-database, cache persistence patterns
- **`references/properties-reference.md`** — All devcontainer.json properties with types and defaults

### Related Skills

- **devcontainer-lifecycle** — Lifecycle event execution order and semantics
- **devcontainer-compose** — Docker Compose integration decision framework
- **devcontainer-features** — Feature system for modular environment composition
- **devcontainer-cli** — CLI automation for CI/CD integration
