---
name: devcontainer-lifecycle
description: >
  This skill should be used when the user asks about "devcontainer lifecycle events",
  "postStartCommand", "postCreateCommand", "onCreateCommand", "lifecycle execution order",
  "parallel named commands", "waitFor property", "command failure semantics",
  "prebuild commands", "container startup hooks", or needs to understand when and how
  devcontainer lifecycle events execute.
---

# Dev Container Lifecycle Events

## Overview

The devcontainer specification defines 6 lifecycle events that execute in strict order
during container creation, startup, and editor attachment. Understanding execution order,
scope, and failure semantics is essential for reliable dev environment initialization.

## Execution Order (Strict)

```
HOST:       initializeCommand
CONTAINER:  onCreateCommand → updateContentCommand → postCreateCommand
ON START:   postStartCommand
ON ATTACH:  postAttachCommand
```

### Event Reference Table

| Event | Scope | When | Parallel | Re-runs on restart |
|-------|-------|------|----------|--------------------|
| initializeCommand | HOST | Before container creation | No | No |
| onCreateCommand | Container | Container exists, not initialized | YES (object) | No |
| updateContentCommand | Container | After onCreate | No | No |
| postCreateCommand | Container | After full initialization | YES (object) | No |
| postStartCommand | Container | Every start/resume | YES (object) | YES |
| postAttachCommand | Container | Editor attaches | YES (object) | YES |

### Key Insight: postStartCommand for Sidecar Services

`postStartCommand` runs on EVERY container start, including restarts. This makes it the
correct event for starting sidecar compose services that need to be running whenever the
dev environment is active.

## Command Syntax Formats

Three formats are supported (availability varies by event):

### String (shell execution)
```json
"postCreateCommand": "npm install && npm run build"
```
Runs in `/bin/sh`. Supports pipes, `&&`, `||`, redirects. Use for complex shell logic.

### Array (direct execution)
```json
"postCreateCommand": ["npm", "run", "build"]
```
Runs directly without shell. More secure (no injection). Use for simple commands.

### Object (parallel named commands)
```json
"postCreateCommand": {
  "build": "npm run build",
  "watch": "npm run watch:css",
  "db-seed": ["npm", "run", "db:seed"]
}
```
All commands run in parallel with independent exit codes and logging.
Supported by: onCreateCommand, postCreateCommand, postStartCommand, postAttachCommand.

## Failure Semantics

- If any creation command fails (onCreateCommand through postCreateCommand),
  ALL subsequent commands are SKIPPED
- postStartCommand and postAttachCommand only run if creation succeeded
- Each parallel named command has independent exit status
- No explicit timeout mechanism in the spec — use backgrounding wisely

## waitFor Property

Controls which lifecycle event blocks container readiness:
- Values: `"initializeCommand"` | `"onCreateCommand"` | `"updateContentCommand"` | `"postCreateCommand"`
- Default: `"postCreateCommand"` (blocks until full setup complete)
- Use case: Define prebuild cutoff point for CI optimization

## Common Patterns

### Fast startup with parallel initialization
```json
{
  "onCreateCommand": {
    "deps": "apt-get update && apt-get install -y build-essential",
    "db": "npm run db:setup"
  },
  "postStartCommand": {
    "dev-server": "npm run dev",
    "otel": "docker compose -f docker/otel/compose.yaml up -d"
  }
}
```

### Prebuild optimization
```json
{
  "waitFor": "updateContentCommand",
  "onCreateCommand": "apt-get update && apt-get install -y nodejs",
  "updateContentCommand": "npm ci",
  "postCreateCommand": "npm run build"
}
```

## Additional Resources

### Reference Files

For the complete lifecycle specification with all properties and edge cases:
- **`references/lifecycle-events-full.md`** — Complete event documentation with all syntax examples
- **`references/execution-guarantees.md`** — Timing, blocking, and failure behavior details

### Related Skills

- **devcontainer-compose** — Docker Compose integration patterns using lifecycle events
- **devcontainer-setup** — Generate devcontainer.json with correct lifecycle pipeline
