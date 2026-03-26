# Docker Compose Properties — Complete Reference

## dockerComposeFile

- **Type**: String or Array of strings
- **Description**: Path(s) to docker-compose.yml file(s)
- **Multiple files**: Merged in order specified (later files override earlier)
- **Example**: `["docker-compose.yml", "docker-compose.dev.yml"]`

## service (REQUIRED with dockerComposeFile)

- **Type**: String
- **Description**: Which service in docker-compose.yml to use as dev container
- **The service becomes the dev container** — this is the critical distinction
- **Example**: `"app"` or `"backend"`

## runServices

- **Type**: Array of strings
- **Description**: Services to start alongside dev container service
- **Default**: All services in compose file
- **Allows partial startup** for faster development
- **Example**: `["app", "db", "redis"]` (skip elasticsearch, kafka, etc.)

## shutdownAction

- **Type**: String
- **Values**: `"stopCompose"` | `"stopContainer"` | `"none"`
- **Description**: What happens when dev container closes
- `stopCompose`: All services stop (default)
- `stopContainer`: Only dev container stops, sidecars continue
- `none`: Everything continues running
- **Default**: `"stopCompose"`

## overrideCommand

- **Type**: Boolean
- **Description**: Replace container's default CMD with sleep to keep it running
- **Default**: `true` (for image-based containers)
- **Set to `false`** if container has custom entrypoint to execute

## Complete Compose Example

```json
{
  "name": "Full Stack Development",
  "dockerComposeFile": ["docker-compose.yml", "docker-compose.dev.yml"],
  "service": "app",
  "runServices": ["app", "db", "redis"],
  "shutdownAction": "stopCompose",
  "workspaceFolder": "/workspace",
  "forwardPorts": ["db:5432", "redis:6379"],
  "remoteEnv": {
    "DATABASE_URL": "postgresql://user:pass@db:5432/mydb",
    "REDIS_URL": "redis://redis:6379"
  },
  "postCreateCommand": "npm run db:migrate"
}
```

## Multi-Database Setup

```json
{
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "runServices": ["postgres", "redis", "elasticsearch"],
  "postCreateCommand": ["npm", "run", "db:migrate"]
}
```

## Health Check Patterns (per database)

- **PostgreSQL**: `pg_isready -U postgres`
- **MySQL**: `mysqladmin ping`
- **MongoDB**: `mongosh --eval "db.adminCommand('ping')"`
- **Redis**: `redis-cli ping`
