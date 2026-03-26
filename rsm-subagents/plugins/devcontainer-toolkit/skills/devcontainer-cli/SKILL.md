---
name: devcontainer-cli
description: >
  This skill should be used when the user asks about "devcontainer CLI", "devcontainer up",
  "devcontainer exec", "devcontainer build", "devcontainer read-configuration",
  "run-user-commands", "CI devcontainer", "install devcontainer CLI", or needs to
  automate devcontainer operations from the command line.
---

# Dev Container CLI Reference

## Overview

The devcontainer CLI (`@devcontainers/cli`) provides full container lifecycle management
through subcommands and flags. All commands support JSON output for programmatic integration.
Install via `npm install -g @devcontainers/cli` or manage through mise.

## Core Commands

### devcontainer up
Create and start a development container.

```bash
devcontainer up --workspace-folder .
devcontainer up --workspace-folder . --remove-existing-container
devcontainer up --workspace-folder . --config .devcontainer/custom.json
```

**Key flags:**
- `--workspace-folder <path>` — Workspace directory (required)
- `--config <path>` — Custom devcontainer.json path
- `--remove-existing-container` — Delete and recreate
- `--skip-post-create` — Skip postCreateCommand and later
- `--skip-non-blocking-commands` — Stop after updateContentCommand
- `--mount <spec>` — Add mounts (repeatable)
- `--remote-env <KEY=VALUE>` — Add env vars (repeatable)
- `--id-label <KEY=VALUE>` — Container tracking labels
- `--image-name <image>` — Specify output image name

**JSON output:**
```json
{"outcome": "success", "containerId": "<id>", "remoteUser": "<user>", "remoteWorkspaceFolder": "/path"}
```

### devcontainer exec
Execute a command in a running container.

```bash
devcontainer exec --workspace-folder . -- npm test
devcontainer exec --workspace-folder . --remote-env CI=true -- pytest
```

**Key flags:**
- `--workspace-folder <path>` — Target workspace
- `--id-label <KEY=VALUE>` — Target by label
- `--remote-env <KEY=VALUE>` — Add env vars for command
- Arguments after `--` passed to target command

### devcontainer build
Build container image from configuration.

```bash
devcontainer build --workspace-folder . --image-name ghcr.io/org/repo:tag
devcontainer build --workspace-folder . --image-name img --platform linux/amd64,linux/arm64 --push
```

**Key flags:**
- `--workspace-folder <path>` — Source workspace (required)
- `--image-name <image>` — Output image reference (required)
- `--no-cache` — Skip layer caching
- `--platform <platforms>` — Multi-platform build
- `--push` — Push to registry after build
- `--cache-from <image>` — Pull build cache from registry

### devcontainer run-user-commands
Re-execute lifecycle commands on a running container.

```bash
devcontainer run-user-commands --workspace-folder .
devcontainer run-user-commands --workspace-folder . --skip-non-blocking-commands
```

Use case: Re-run setup after config changes, debug lifecycle issues.

### devcontainer read-configuration
Output merged configuration for debugging.

```bash
devcontainer read-configuration --workspace-folder . --include-merged-configuration
```

Use case: Debug config resolution, understand feature merging, validate overrides.

## CI/CD Patterns

### GitHub Actions
```yaml
- uses: devcontainers/ci@v0.3
  with:
    imageName: ghcr.io/${{ github.repository }}/devcontainer
    push: filter
    refFilterForPush: refs/heads/main
```

### Manual CI Build
```bash
devcontainer build --workspace-folder . \
  --image-name ghcr.io/org/repo:$SHA \
  --cache-from ghcr.io/org/repo:main \
  --push
```

### Running Tests in CI
```bash
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . -- npm test
```

## Additional Resources

### Reference Files

For complete flag reference and all 11 subcommands:
- **`references/cli-full-reference.md`** — All subcommands, flags, and output formats

### Related Skills

- **devcontainer-lifecycle** — Understanding lifecycle events the CLI manages
- **devcontainer-features** — Feature CLI subcommands (test, package, publish)
