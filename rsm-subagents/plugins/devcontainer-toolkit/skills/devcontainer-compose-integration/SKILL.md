---
name: devcontainer-compose-integration
description: >
  This skill should be used when the user asks to "add Docker Compose services
  to devcontainer", "integrate observability stack with devcontainer",
  "migrate from docker compose to devcontainer CLI", "add sidecar services",
  or mentions running additional containers alongside the dev environment.
  Also triggers on "start OTEL collector via devcontainer", "manage compose
  services through devcontainer", or "runServices configuration".
---

# Docker Compose Integration with Devcontainer

Manage Docker Compose services through the devcontainer specification instead
of raw `docker compose` commands.

## Why Devcontainer Over Raw Docker Compose

The devcontainer spec natively supports Docker Compose orchestration:
- Single `devcontainer up` starts all services
- `shutdownAction: stopCompose` cleans up on disconnect
- Port forwarding managed declaratively
- Environment variables flow from host to containers
- Consistent lifecycle across local dev, CI, and codespaces

## Adding Compose Services

### Step 1: Reference the Compose File

In `devcontainer.json`, add the `dockerComposeFile` property:

```json
{
  "dockerComposeFile": ["docker-compose.yml", "../docker/observability/compose.yaml"],
  "service": "app",
  "workspaceFolder": "/workspace"
}
```

Paths are relative to the `.devcontainer/` directory.

### Step 2: Control Which Services Start

Use `runServices` to specify which services start with `devcontainer up`:

```json
{
  "runServices": ["app", "collector", "grafana", "loki", "tempo"]
}
```

Omit `runServices` to start all services defined in the compose files.

### Step 3: Configure Shutdown Behavior

```json
{
  "shutdownAction": "stopCompose"
}
```

Options:
- `"stopCompose"` — stops all compose services on disconnect
- `"none"` — leaves services running

### Step 4: Forward Ports

```json
{
  "forwardPorts": [4318, 3000, 3100, 3200]
}
```

Map container ports to host for access.

## Sidecar Services Pattern

For infrastructure services (OTEL collector, databases) that are NOT the dev
environment but run alongside it:

```json
{
  "name": "mde-devcontainer",
  "image": "ghcr.io/ray-manaloto/macos-development-environment/devcontainer:main",
  "dockerComposeFile": ["../docker/observability/compose.yaml"],
  "service": "app",
  "runServices": ["collector", "grafana", "loki", "tempo"],
  "shutdownAction": "stopCompose",
  "forwardPorts": [4318, 3000, 3100, 3200],
  "remoteEnv": {
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://collector:4318"
  }
}
```

## Migration from Raw Docker Compose

To migrate `observability_stack.py` from `docker compose` to devcontainer CLI:

1. Add `dockerComposeFile` to `.devcontainer/devcontainer.json`
2. Replace `subprocess.run(["docker", "compose", ...])` with
   `subprocess.run(["devcontainer", "up", "--workspace-folder", "."])`
3. Replace `docker compose ps` with `devcontainer read-configuration`
4. Keep health checks using host-side HTTP probes (unchanged)

## CLI Commands for Compose Services

```bash
# Start all services (including compose)
devcontainer up --workspace-folder .

# Execute command in the dev container (not sidecar services)
devcontainer exec --workspace-folder . <command>

# Check running services
docker compose -f docker/observability/compose.yaml ps
```

## Limitations

- `devcontainer exec` runs in the primary service only, not sidecars
- Health checks for sidecar services still need host-side probes
- Compose file paths must be relative to `.devcontainer/` directory
