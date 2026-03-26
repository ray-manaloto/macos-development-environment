# devcontainer.json Properties — Complete Reference

## Image Configuration

### image
- **Type**: String
- **Description**: Base container image (OCI reference)
- **Alternative to**: `build`
- **Example**: `"mcr.microsoft.com/devcontainers/base:ubuntu"`

### build
- **Type**: Object
- **Properties**:
  - `dockerfile`: Path to Dockerfile
  - `context`: Build context directory
  - `args`: Build arguments (key-value object)
  - `target`: Build target for multi-stage builds
  - `cacheFrom`: Cache sources for layer reuse
  - `cacheTo`: Cache destinations

## Workspace & Mounts

### workspaceFolder
- **Type**: String
- **Default**: `/workspaces/<workspace-folder-name>`
- **Description**: Container-side path where host workspace is mounted

### mounts
- **Type**: Array of mount objects
- **Properties per mount**:
  - `source`: Host path or volume name
  - `target`: Container path
  - `type`: `"bind"` or `"volume"`
  - `readonly`: Boolean

## User & Permissions

### containerUser
- **Type**: String
- **Description**: User for ALL container operations

### remoteUser
- **Type**: String
- **Description**: User that editor/IDE runs as

### updateRemoteUserUID
- **Type**: Boolean
- **Description**: Sync host UID to container remoteUser (Linux only)

## Environment Variables

### containerEnv
- **Type**: Object (key: var name, value: var value)
- **Scope**: Container environment during lifecycle execution
- **Substitution**: `${localEnv:VAR}`, `${containerEnv:VAR}`, `${localWorkspaceFolder}`

### remoteEnv
- **Type**: Object
- **Scope**: Container environment when editor is attached
- **Additional vars**: `${containerWorkspaceFolder}`, `${localWorkspaceFolderBasename}`

## Port Forwarding

### forwardPorts
- **Type**: Array of ports (numbers or strings)
- **Format**: Integer or `"service:port"` (Compose)
- **Example**: `[3000, 8080, "db:5432"]`

### portsAttributes
- **Type**: Object (key: port or range, value: attributes)
- **Attributes**: `label`, `protocol`, `onAutoForward`, `requireLocalPort`, `elevateIfNeeded`
- **onAutoForward values**: `"openBrowser"`, `"notify"`, `"silent"`, `"ignore"`

### otherPortsAttributes
- **Type**: Object
- **Description**: Defaults for ports not in portsAttributes

## Security

### privileged
- **Type**: Boolean
- **Description**: Run in privileged mode (avoid if possible)

### capAdd
- **Type**: Array of Linux capability strings
- **Example**: `["SYS_PTRACE"]`

### securityOpt
- **Type**: Array
- **Example**: `["seccomp=unconfined"]`

### init
- **Type**: Boolean
- **Description**: Use init process to reap zombies

### runArgs
- **Type**: Array of strings
- **Description**: Raw Docker arguments to `docker run`

## IDE Customizations

### customizations
- **Type**: Object with IDE-specific sub-objects
- **Sub-objects**: `vscode`, `github`, `jetbrains`

```json
{
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python"],
      "settings": { "python.linting.enabled": true }
    }
  }
}
```

## Host Requirements

### hostRequirements
- **Type**: Object
- **Properties**: `cpus`, `memory`, `gpu`, `storage`

## Advanced

### name
- **Type**: String — Human-readable container name

### userEnvProbe
- **Type**: String
- **Values**: `"loginInteractiveShell"`, `"interactiveShell"`, `"loginShell"`, `"none"`

### shutdownAction (non-compose)
- **Type**: String
- **Values**: `"stopContainer"`, `"none"`
