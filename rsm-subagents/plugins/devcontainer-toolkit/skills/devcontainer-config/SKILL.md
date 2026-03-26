---
name: devcontainer-config
description: >
  This skill should be used when the user asks to "edit devcontainer.json",
  "add a devcontainer feature", "configure devcontainer settings",
  "change devcontainer image", or mentions devcontainer.json configuration.
  Also triggers on "add a service to devcontainer", "change workspace folder",
  or "update post-create command".
---

# Devcontainer Configuration

Edit and manage devcontainer.json files following the Dev Container specification.

## Core Properties

### Image-Based Configuration

```json
{
  "name": "project-name",
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "remoteUser": "vscode",
  "postCreateCommand": "bash .devcontainer/post-create.sh"
}
```

### Docker Compose-Based Configuration

```json
{
  "name": "project-name",
  "dockerComposeFile": ["docker-compose.yml"],
  "service": "app",
  "workspaceFolder": "/workspace",
  "runServices": ["app", "db", "redis"],
  "shutdownAction": "stopCompose"
}
```

## Adding Features

Features are reusable units of installation code:

```json
{
  "features": {
    "ghcr.io/devcontainers/features/node:1": { "version": "20" },
    "ghcr.io/devcontainers/features/python:1": { "version": "3.12" }
  }
}
```

## Environment Variables

```json
{
  "containerEnv": { "ENV_VAR": "value" },
  "remoteEnv": { "RUNTIME_VAR": "${localEnv:HOST_VAR}" }
}
```

- `containerEnv` — set at container creation (available to all processes)
- `remoteEnv` — set at connection time (available to user processes)
- `${localEnv:VAR}` — reference host machine environment variables

## Port Forwarding

```json
{
  "forwardPorts": [3000, 8080, "db:5432"]
}
```

## Lifecycle Commands

```json
{
  "postCreateCommand": "npm install",
  "postStartCommand": "npm run dev",
  "postAttachCommand": "echo 'Connected!'"
}
```

## CLI Commands

```bash
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . <command>
devcontainer build --workspace-folder .
devcontainer read-configuration --workspace-folder .
```

## Validation

After editing devcontainer.json:
1. Run `devcontainer read-configuration --workspace-folder .` to check syntax
2. Run `devcontainer up --workspace-folder .` to test
3. Verify services start with `docker compose ps`
