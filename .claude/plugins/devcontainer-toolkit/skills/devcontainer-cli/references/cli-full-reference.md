# Dev Container CLI — Full Reference

Source: devcontainer 0.84.1 --help output, tested on darwin/arm64.

## All Subcommands

### Primary Lifecycle Commands

#### devcontainer up
Create and run dev container.

All flags:
- `--workspace-folder <path>` — Workspace directory (defaults to cwd)
- `--config <path>` — Path to devcontainer.json (overrides workspace search)
- `--override-config <path>` — Override any devcontainer.json
- `--id-label <KEY=VALUE>` — Container id labels for querying
- `--remove-existing-container` — Delete and recreate container
- `--expect-existing-container` — Fail if container doesn't exist
- `--skip-post-create` — Skip postCreateCommand and later
- `--skip-non-blocking-commands` — Stop after updateContentCommand
- `--prebuild` — Run only until prebuild point
- `--mount <spec>` — Add mounts (repeatable)
- `--remote-env <KEY=VALUE>` — Add env vars (repeatable)
- `--image-name <image>` — Output image name
- `--include-configuration` — Include config in JSON output
- `--include-merged-configuration` — Include merged config in output
- `--log-format json` — JSON log format

#### devcontainer set-up
Alias for `up` with different semantics (sets up without starting).

#### devcontainer exec
Execute command in running container.

Flags:
- `--workspace-folder <path>` — Target workspace
- `--id-label <KEY=VALUE>` — Target by label
- `--remote-env <KEY=VALUE>` — Add env vars for command
- `--` — Separator before target command and args

#### devcontainer run-user-commands
Execute lifecycle commands on running container.

Flags:
- `--workspace-folder <path>` — Target workspace (required)
- `--id-label <KEY=VALUE>` — Target by label
- `--skip-non-blocking-commands` — Stop after updateContentCommand
- `--prebuild` — Run only until prebuild point

#### devcontainer build
Build container image from config.

Flags:
- `--workspace-folder <path>` — Source workspace (required)
- `--image-name <image>` — Output image reference (required)
- `--config <path>` — Custom devcontainer.json
- `--no-cache` — Skip layer caching
- `--platform <platform1,platform2>` — Multi-platform build
- `--push` — Push to registry after build
- `--cache-from <image>` — Pull build cache
- `--cache-to <spec>` — Push build cache
- `--additional-features <json>` — Add features not in config

#### devcontainer read-configuration
Output merged configuration.

Flags:
- `--workspace-folder <path>` — Target workspace (required)
- `--config <path>` — Custom config file
- `--log-format json` — JSON output
- `--include-merged-configuration` — Show all merged details

### Feature Management

#### devcontainer features test
Test feature installation.

#### devcontainer features package
Package feature for distribution.

#### devcontainer features publish
Publish feature to OCI registry.

#### devcontainer features info
Get feature metadata.

#### devcontainer features resolve-dependencies
Resolve feature dependency graph.

#### devcontainer features generate-docs
Generate feature documentation.

### Template Management

#### devcontainer templates apply
Apply a devcontainer template.

#### devcontainer templates publish
Publish template to registry.

#### devcontainer templates metadata
Get template metadata.

#### devcontainer templates generate-docs
Generate template documentation.

### Maintenance

#### devcontainer outdated
Check for outdated features.

#### devcontainer upgrade
Upgrade features to latest versions.

## JSON Output Format

Most commands support JSON output. Common structure:
```json
{
  "outcome": "success",
  "containerId": "<docker-container-id>",
  "remoteUser": "<configured-user>",
  "remoteWorkspaceFolder": "/container/workspace/path"
}
```

Error format:
```json
{
  "outcome": "error",
  "message": "<error-description>",
  "description": "<detailed-error>"
}
```
