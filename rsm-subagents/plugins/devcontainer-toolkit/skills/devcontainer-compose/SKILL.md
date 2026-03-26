---
name: devcontainer-compose
description: >
  This skill should be used when the user asks about "devcontainer Docker Compose",
  "dockerComposeFile", "runServices", "shutdownAction", "sidecar services",
  "compose integration", "postStartCommand for compose", "multi-container devcontainer",
  or needs to decide between dockerComposeFile mode and lifecycle-based compose
  management for dev environments.
---

# Dev Container Docker Compose Integration

## Overview

The devcontainer spec provides two distinct patterns for Docker Compose integration.
Choosing the wrong pattern causes architectural problems — coupling unrelated lifecycles
or losing host-side service access. This skill provides the decision framework.

## Two Patterns

### Pattern A: dockerComposeFile + service (Compose IS the devcontainer)

The compose service becomes the dev container. All services share the devcontainer lifecycle.

```json
{
  "dockerComposeFile": ["docker-compose.yml", "docker-compose.dev.yml"],
  "service": "app",
  "runServices": ["app", "db", "redis"],
  "shutdownAction": "stopCompose",
  "forwardPorts": ["db:5432"],
  "remoteEnv": {
    "DATABASE_URL": "postgresql://user:pass@db:5432/mydb"
  }
}
```

**Properties:**
- `dockerComposeFile`: Path(s) to compose files. Multiple files merged in order.
- `service` (REQUIRED): Which compose service IS the dev container.
- `runServices`: Subset of services to start (default: all).
- `shutdownAction`: `"stopCompose"` | `"stopContainer"` | `"none"`.
- `overrideCommand`: Replace container CMD with sleep (default: true).

### Pattern B: postStartCommand (Compose as sidecar infrastructure)

Keep the image-based devcontainer.json. Start compose services via lifecycle events.

```json
{
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "postStartCommand": {
    "otel-stack": "docker compose -f docker/observability/compose.yaml up -d",
    "check-health": "sleep 5 && curl -sf http://localhost:13133/health || true"
  },
  "forwardPorts": [4317, 4318, 3000, 13133],
  "portsAttributes": {
    "4317": { "label": "OTEL gRPC", "onAutoForward": "silent" },
    "3000": { "label": "Grafana", "onAutoForward": "notify" }
  }
}
```

## Decision Framework

### Choose Pattern A when:
- The dev container IS a compose service (app code runs inside it)
- All services share a lifecycle (start/stop together)
- No host-side consumers of sidecar services
- Database/cache are direct dependencies of the dev workflow

### Choose Pattern B when:
- Sidecar infrastructure serves host-side processes (AI CLIs, monitoring agents)
- Services need independent lifecycle management (can start/stop without dev env)
- Services require host-side secrets or health probes
- Image-based devcontainer.json simplicity is preferred
- Compose services run on the host Docker daemon, not inside the container

### When Sidecar Infrastructure Serves Outside Processes

Infrastructure that serves processes running outside the dev container (monitoring agents,
CLI tools, CI runners) must use Pattern B. Coupling it to dockerComposeFile ties the
infrastructure lifecycle to the dev environment, breaking external consumers.
See `references/sidecar-patterns.md` for detailed examples.

## Port Forwarding for Compose Services

When using Pattern B, forward compose service ports so code inside the devcontainer
can reach them:

```json
{
  "forwardPorts": [4317, 4318, 3000, 3100, 3200, 13133],
  "portsAttributes": {
    "3000": { "label": "Grafana", "onAutoForward": "notify" },
    "4317": { "label": "OTEL gRPC", "onAutoForward": "silent" }
  }
}
```

Use `"onAutoForward": "silent"` for infrastructure ports, `"notify"` for user-facing UIs.

## Common Mistakes

1. **Using dockerComposeFile for sidecar infra** — Couples dev environment to infrastructure lifecycle
2. **Missing `service` property** — Required when using dockerComposeFile, specifies which service IS the container
3. **Not publishing health ports** — Compose services need health check ports published to localhost
4. **Forgetting forwardPorts** — Code inside devcontainer can't reach host-side compose services without forwarding

## Additional Resources

### Reference Files

For detailed compose properties, real-world patterns, and multi-database setups:
- **`references/compose-properties.md`** — All dockerComposeFile/service/runServices/shutdownAction details
- **`references/sidecar-patterns.md`** — Real-world sidecar compose integration examples

### Related Skills

- **devcontainer-lifecycle** — Lifecycle event execution order and parallel commands
- **devcontainer-setup** — Generate devcontainer.json with appropriate compose pattern
