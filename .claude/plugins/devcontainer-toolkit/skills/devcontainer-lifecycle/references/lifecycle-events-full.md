# Lifecycle Events — Complete Reference

Source: devcontainers/spec official documentation, context7 queries 2026-03-25.

## 1. initializeCommand

- **When**: Runs first, before container is created
- **Scope**: HOST machine (not in container)
- **Use case**: Clone repos, download large files, GPU preparation
- **Supports parallel**: No (blocks until complete)
- **Syntax**: String (shell) or Array (direct exec)
- **Example**: `"echo 'Preparing host for container creation'"`

## 2. onCreateCommand

- **When**: Container exists but not yet fully initialized
- **Scope**: CONTAINER (inside running container)
- **Use case**: Install OS-level packages, setup databases
- **Supports parallel**: Can specify multiple named tasks as object
- **Syntax**: String, Array, or Object (named commands)
- **Example**:
  ```json
  {
    "dependencies": "apt-get update && apt-get install -y nodejs",
    "database": "npm run db:setup"
  }
  ```

## 3. updateContentCommand

- **When**: After onCreateCommand, before postCreateCommand
- **Scope**: CONTAINER
- **Use case**: Update dependencies (npm install, pip install, cargo build)
- **Supports parallel**: No
- **Syntax**: String or Array
- **Example**: `["npm", "install"]`

## 4. postCreateCommand

- **When**: After container fully initialized and content updated
- **Scope**: CONTAINER
- **Use case**: Build artifacts, compile projects, start watchers
- **Supports parallel**: Yes (object-based named commands)
- **Syntax**: String, Array, or Object (named commands)
- **Example**:
  ```json
  {
    "build": "npm run build",
    "watch": "npm run watch:css"
  }
  ```

## 5. postStartCommand

- **When**: Every time container starts/resumes from stop
- **Scope**: CONTAINER
- **Use case**: Start development servers, background tasks that don't persist
- **Supports parallel**: Yes (object-based named commands)
- **Syntax**: String, Array, or Object (named commands)
- **Example**: `["npm", "run", "dev"]`

**KEY**: This is the correct event for sidecar compose services because it runs on
every container start, including restarts. Services that were docker-compose-down'd
or that crashed will be restarted.

## 6. postAttachCommand

- **When**: Editor/IDE attaches to running container
- **Scope**: CONTAINER
- **Use case**: Final setup visible to developer (extensions, shell config)
- **Supports parallel**: Yes (object-based named commands)
- **Syntax**: String, Array, or Object (named commands)
- **Example**: `"echo 'Development environment ready!'"`

## Execution Flow Diagram

```
Host Machine:
  initializeCommand
  ↓
Container Creation & Feature Installation:
  (Container starts)
  (Feature install scripts run)
  ↓
Inside Container (Sequential):
  onCreateCommand
  ↓
  updateContentCommand
  ↓
  postCreateCommand
  ↓
(Container running, waiting for attachment)
  ↓
On Editor Attach:
  postAttachCommand

Container Restart (after stop/resume):
  postStartCommand
  (No re-run of creation commands)
```

## Command Syntax Details

### String syntax
Runs in shell (/bin/sh or /bin/bash):
- Supports pipes, &&, ||, redirects
- Less predictable (depends on shell)
- Use for complex shell logic

### Array syntax
Runs directly without shell:
- More secure (no shell injection)
- Faster (no shell overhead)
- Must break command + args: `["npm", "run", "build"]` not `["npm run build"]`

### Object syntax (parallel named commands)
All commands in object run in parallel:
- Execution order within object is undefined
- Each command has independent exit code/logging
- Use for independent tasks (build, watch, server all at once)

## Failure Semantics

- If `initializeCommand` fails: container creation does not proceed
- If `onCreateCommand` fails: updateContentCommand and all later commands are skipped
- If `updateContentCommand` fails: postCreateCommand and later skipped
- If `postCreateCommand` fails: postStartCommand and postAttachCommand skipped
- `postStartCommand` failure: does not affect postAttachCommand
- `postAttachCommand` failure: logged but does not affect container operation

## waitFor Property

Controls which lifecycle event blocks further execution:
- `"initializeCommand"`: Unblock after host command
- `"onCreateCommand"`: Unblock after first container setup
- `"updateContentCommand"`: Unblock after deps updated (good for prebuilds)
- `"postCreateCommand"`: Unblock after full setup (default)
