# Common Dev Container Patterns

## GPU Development
```json
{
  "image": "nvidia/cuda:11.8-runtime-ubuntu22.04",
  "hostRequirements": {
    "gpu": true,
    "memory": "8gb"
  },
  "runArgs": ["--gpus", "all"],
  "features": {
    "ghcr.io/devcontainers/features/python:1": { "version": "3.11" }
  }
}
```

## Docker-in-Docker (DinD)
```json
{
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  "mounts": [
    {
      "source": "dind-var-lib-docker",
      "target": "/var/lib/docker",
      "type": "volume"
    }
  ]
}
```

## Cache Persistence
```json
{
  "mounts": [
    { "source": "npm-cache", "target": "/home/node/.npm", "type": "volume" },
    { "source": "pip-cache", "target": "/home/node/.cache/pip", "type": "volume" },
    { "source": "cargo-cache", "target": "/home/node/.cargo/registry", "type": "volume" },
    { "source": "go-cache", "target": "/home/node/go/pkg", "type": "volume" }
  ]
}
```

## Multi-Database Setup (Compose)
```json
{
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "runServices": ["postgres", "redis", "elasticsearch"],
  "postCreateCommand": ["npm", "run", "db:migrate"]
}
```

## Monorepo with Multiple Services
```json
{
  "dockerComposeFile": ["docker-compose.yml", "docker-compose.dev.yml"],
  "service": "api",
  "runServices": ["api", "worker", "postgres", "redis"],
  "workspaceFolder": "/workspace",
  "postStartCommand": {
    "api": "npm run dev:api",
    "worker": "npm run dev:worker",
    "watch": "npm run watch"
  }
}
```

## Security-Hardened
```json
{
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "capAdd": ["SYS_PTRACE"],
  "securityOpt": ["seccomp=unconfined"],
  "init": true,
  "remoteUser": "vscode",
  "containerUser": "vscode",
  "updateRemoteUserUID": true
}
```

## Prebuild-Optimized
```json
{
  "waitFor": "updateContentCommand",
  "onCreateCommand": {
    "system": "apt-get update && apt-get install -y build-essential",
    "tools": "npm install -g typescript eslint"
  },
  "updateContentCommand": "npm ci",
  "postCreateCommand": "npm run build",
  "postStartCommand": "npm run dev"
}
```
