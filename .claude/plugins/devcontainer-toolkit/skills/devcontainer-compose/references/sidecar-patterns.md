# Sidecar Compose Integration Patterns

## Pattern: Observability Stack via postStartCommand

When an observability stack (OTEL collector, Grafana, Loki, Tempo) serves host-side
processes, it must NOT use dockerComposeFile. Use postStartCommand instead.

### Architecture Decision

The observability stack is sidecar infrastructure, not a dev environment:
- Runs on the host Docker daemon
- Serves host-side AI agents (codex CLI, gemini CLI send telemetry to 127.0.0.1:4318)
- Has independent lifecycle (can start/stop without affecting dev env)
- Requires host-side secrets (e.g., GRAFANA_PASSWORD from Keychain)
- Uses host-side health probes (scratch-based collector has no shell)

Coupling sidecar telemetry infrastructure to dev environment lifecycle is architecturally wrong.

### Implementation

```json
{
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "postStartCommand": {
    "otel-stack": "docker compose -f docker/observability/compose.yaml up -d"
  },
  "forwardPorts": [4317, 4318, 3000, 3100, 3200, 13133],
  "portsAttributes": {
    "4317": { "label": "OTEL gRPC", "onAutoForward": "silent" },
    "4318": { "label": "OTEL HTTP", "onAutoForward": "silent" },
    "3000": { "label": "Grafana", "onAutoForward": "notify" },
    "3100": { "label": "Loki", "onAutoForward": "silent" },
    "3200": { "label": "Tempo", "onAutoForward": "silent" },
    "13133": { "label": "Collector Health", "onAutoForward": "silent" }
  }
}
```

### Common Pitfall: Unpublished Health Ports

Compose services need health check ports published to localhost. If the collector
health extension listens on port 13133 inside the container but this port is NOT
published in compose.yaml, host-side health probes will fail.

Fix: Add `127.0.0.1:13133:13133` to collector ports in compose.yaml.

## Pattern: Development Database via dockerComposeFile

When database is a direct dependency of the dev workflow:

```json
{
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "runServices": ["app", "postgres", "redis"],
  "shutdownAction": "stopCompose",
  "postCreateCommand": "npm run db:migrate",
  "forwardPorts": ["postgres:5432"]
}
```

## Decision Matrix

| Criterion | dockerComposeFile | postStartCommand |
|-----------|-------------------|------------------|
| Service lifecycle | Tied to devcontainer | Independent |
| Host-side consumers | Not supported | Supported |
| Secret management | Via devcontainer env | Host-side (Keychain, etc.) |
| Health probes | Container-side | Host-side HTTP |
| Config complexity | Higher (compose IS devcontainer) | Lower (image-based) |
| Restart behavior | Compose orchestrated | postStartCommand re-runs |
