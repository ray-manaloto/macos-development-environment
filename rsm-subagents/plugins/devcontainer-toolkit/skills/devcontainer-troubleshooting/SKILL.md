---
name: devcontainer-troubleshooting
description: >
  This skill should be used when the user encounters devcontainer failures,
  container startup errors, service health check failures, or networking
  issues. Triggers on "devcontainer won't start", "container crash",
  "service unhealthy", "port not accessible", "devcontainer build failed",
  or "compose services not starting".
---

# Devcontainer Troubleshooting

Debug and fix devcontainer failures using a systematic approach.

## Self-Improving Debug Protocol

Follow this cycle iteratively until resolved:

### 1. Gather Evidence

```bash
# Check devcontainer configuration
devcontainer read-configuration --workspace-folder .

# Check container status
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check compose service status
docker compose -f <compose-file> ps

# Check container logs
docker compose -f <compose-file> logs <service> --tail 50

# Check devcontainer CLI version
devcontainer --version
```

### 2. Common Failure Patterns

#### Container Won't Start

**Check image availability:**
```bash
docker pull <image-name>
```

**Check devcontainer.json syntax:**
```bash
devcontainer read-configuration --workspace-folder . 2>&1
```

**Check post-create command:**
- Verify the script exists and is executable
- Check for missing dependencies in the container

#### Service Unhealthy

**Check health endpoint from host:**
```bash
curl -s http://localhost:<port>/health
```

**Check container logs for errors:**
```bash
docker compose -f <compose-file> logs <service> --tail 100 | grep -i error
```

**Scratch-based images (no shell):**
- Cannot exec into the container
- Must probe health from host side using urllib/curl

#### Port Not Accessible

**Check port forwarding in devcontainer.json:**
```json
{ "forwardPorts": [4318, 3000] }
```

**Check if port is bound on host:**
```bash
lsof -i :<port>
```

**Check compose port mapping:**
```bash
docker compose -f <compose-file> port <service> <container-port>
```

#### Build Failed

**Check Dockerfile syntax and base image:**
```bash
devcontainer build --workspace-folder . 2>&1
```

**Check feature installation:**
- Features may fail if the base image is incompatible
- Try removing features one at a time to isolate

### 3. Research When Stuck

```bash
# Search for solutions in skill registries
uv run mde-py research skill-discover "devcontainer <error>" --json

# Query devcontainer spec docs
ctx7 docs /devcontainers/spec "<error message>"
ctx7 docs /devcontainers/cli "<error message>"
```

### 4. After Fixing

1. Verify the fix: `devcontainer up --workspace-folder .`
2. Check all services: `docker compose ps`
3. Run health checks: probe each service endpoint
4. Document the fix in findings if it reveals a pattern
