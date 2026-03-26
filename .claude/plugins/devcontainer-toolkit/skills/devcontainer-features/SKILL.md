---
name: devcontainer-features
description: >
  This skill should be used when the user asks about "devcontainer features",
  "feature installation", "installsAfter", "feature registry", "ghcr.io features",
  "docker-in-docker feature", "composable dev environment", "create custom feature",
  "publish devcontainer feature", or needs to configure the devcontainer feature
  system for modular environment composition.
---

# Dev Container Feature System

## Overview

Features are composable, OCI-distributed modules that add tools and capabilities to
dev containers. Each feature is a self-contained package with install scripts, lifecycle
commands, and metadata. Features enable building modular dev environments without
monolithic Dockerfiles.

## Feature Configuration

### Adding Features
```json
{
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/node:1": { "version": "18" },
    "ghcr.io/devcontainers/features/python:1": { "version": "3.12" }
  }
}
```

### Reference Format
`<registry>/<namespace>/<feature>:<version>`

- **Registry**: `ghcr.io`, `mcr.microsoft.com`, or custom OCI registry
- **Namespace**: Organization or user (e.g., `devcontainers`)
- **Feature**: Descriptive name (e.g., `docker-in-docker`, `node`, `python`)
- **Version**: Semver required for reproducibility (e.g., `2`, `1.0`, `1.0.5`)

### Feature Metadata (devcontainer-feature.json)

Each feature defines:
- Feature ID and version
- Lifecycle commands: onCreateCommand, postCreateCommand, postAttachCommand
- Dependencies via `installsAfter`
- Configuration schema for options
- Container metadata (mounts, privileged, capAdd)

## Installation Order

1. Parse all features from devcontainer.json
2. Resolve `installsAfter` dependencies
3. Execute feature install scripts in topological order
4. Merge metadata (capabilities, mounts, env vars)
5. Final merged config passed to container creation

## Common Features

### Docker-in-Docker
```json
{
  "ghcr.io/devcontainers/features/docker-in-docker:2": {},
  "mounts": [
    { "source": "dind-var-lib-docker", "target": "/var/lib/docker", "type": "volume" }
  ]
}
```

### Language Runtimes
```json
{
  "ghcr.io/devcontainers/features/node:1": { "version": "22" },
  "ghcr.io/devcontainers/features/python:1": { "version": "3.12" },
  "ghcr.io/devcontainers/features/rust:1": { "version": "latest" }
}
```

### CLI Tools
```json
{
  "ghcr.io/devcontainers/features/github-cli:1": {},
  "ghcr.io/devcontainers/features/kubectl-helm-minikube:1": {}
}
```

## Best Practices

1. **Always pin versions** — Use specific semver for reproducible builds
2. **Use installsAfter** — Declare dependencies between features
3. **Prefer official features** — `ghcr.io/devcontainers/features/` maintained by spec authors
4. **Check feature options** — Many features accept configuration (version, variant, etc.)
5. **Use feature lifecycle** — Features can define their own onCreateCommand/postCreateCommand
6. **Volume mount caches** — Pair features with named volumes for persistent caches

## Feature CLI Commands

For full CLI reference, see the **devcontainer-cli** skill. Key feature subcommands:

```bash
devcontainer features test --workspace-folder . --features ghcr.io/org/feature:1
devcontainer features package ./src/my-feature --output-folder ./dist
devcontainer features publish ./dist --registry ghcr.io --namespace myorg
devcontainer features info ghcr.io/devcontainers/features/node:1
```

## Additional Resources

### Reference Files

For the complete feature specification and publishing workflow:
- **`references/feature-system.md`** — Full feature metadata, installation order, and publishing

### Related Skills

- **devcontainer-cli** — Full CLI reference including feature subcommands
- **devcontainer-setup** — Configuring features during project setup
