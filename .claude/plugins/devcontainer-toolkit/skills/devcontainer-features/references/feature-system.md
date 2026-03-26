# Dev Container Feature System — Complete Reference

## Feature References

Format: `<registry>/<namespace>/<feature>:<version>`

- **Registry**: `ghcr.io`, `mcr.microsoft.com`, or custom OCI registry
- **Namespace**: `devcontainers` (official), organization name, or user
- **Feature ID**: Descriptive name (docker-in-docker, node, python, etc.)
- **Version**: Semver required for reproducibility (1, 1.0, 1.0.5)

## Feature Metadata (devcontainer-feature.json)

Located in feature source repository, defines:
- Feature ID and version
- Lifecycle commands: onCreateCommand, postCreateCommand, postAttachCommand
- Dependencies via `installsAfter`
- Configuration schema for options
- Container metadata (mounts, privileged, capAdd, etc.)

## Installation Order

1. Parse all features from devcontainer.json
2. Resolve `installsAfter` dependencies
3. Execute feature install scripts in topological order
4. Merge metadata (capabilities, mounts, env vars)
5. Final merged config passed to container creation

## Feature Lifecycle Commands

Each feature can define its own lifecycle commands that merge with the user's:
- `onCreateCommand` — Runs during container creation
- `postCreateCommand` — Runs after container fully initialized
- `postAttachCommand` — Runs when editor attaches

Feature lifecycle commands run AFTER the user's lifecycle commands at each stage.

## installsAfter

```json
{
  "installsAfter": [
    "ghcr.io/devcontainers/features/common-utils"
  ]
}
```

Ensures specific features install before others. Used within feature definitions
to declare dependencies. The CLI resolves the dependency graph topologically.

## Official Feature Registry

The `ghcr.io/devcontainers/features/` namespace contains maintained features:

### Languages
- `python:1` — Python with pip, venv
- `node:1` — Node.js with npm/yarn
- `rust:1` — Rust with cargo
- `go:1` — Go language
- `java:1` — Java JDK
- `dotnet:2` — .NET SDK
- `ruby:1` — Ruby with rbenv

### Tools
- `docker-in-docker:2` — Docker daemon inside container
- `docker-outside-of-docker:1` — Use host Docker from container
- `github-cli:1` — GitHub CLI
- `kubectl-helm-minikube:1` — Kubernetes tools
- `terraform:1` — Terraform
- `aws-cli:1` — AWS CLI
- `azure-cli:1` — Azure CLI

### Utilities
- `common-utils:2` — zsh, git, sudo configuration
- `git:1` — Git with LFS
- `git-lfs:1` — Git Large File Storage
- `sshd:1` — SSH server

## Publishing Custom Features

### Package
```bash
devcontainer features package ./src/my-feature --output-folder ./dist
```

### Publish to GHCR
```bash
devcontainer features publish ./dist \
  --registry ghcr.io \
  --namespace myorg
```

### Feature Structure
```
my-feature/
├── devcontainer-feature.json
├── install.sh
└── README.md
```

### devcontainer-feature.json
```json
{
  "id": "my-feature",
  "version": "1.0.0",
  "name": "My Feature",
  "description": "Installs my tool",
  "options": {
    "version": {
      "type": "string",
      "default": "latest",
      "description": "Tool version to install"
    }
  },
  "installsAfter": ["ghcr.io/devcontainers/features/common-utils"],
  "onCreateCommand": "my-tool --setup",
  "capAdd": ["SYS_PTRACE"]
}
```
