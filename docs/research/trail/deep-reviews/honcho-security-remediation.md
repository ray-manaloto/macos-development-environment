# Honcho Memory Stack: Security Remediation Guide

**Date:** 2026-03-23
**Severity:** HIGH (8 vulnerabilities, 1 CRITICAL)
**Finding:** [adversarial-security-review.yaml](../findings/adversarial-security-review.yaml)

## Executive Summary

The Honcho memory design spec (PR B) has good security fundamentals (read_only filesystems, cap_drop, resource limits) but contains 8 real gaps:

| Severity | Vector | Gap | Impact |
|----------|--------|-----|--------|
| CRITICAL | Supply chain | honcho:v3.0.3 lacks @sha256: digest | Undetected image substitution; tag re-push attacks |
| HIGH | Authentication | AUTH_USE_AUTH=false by default | Unauthenticated access to all session data if port 8000 exposed |
| MEDIUM | Secrets management | HONCHO_DB_PASSWORD in plaintext env | Visible in `docker inspect`, readable by sibling containers |
| MEDIUM | Secrets management | LLM API keys in .env (not versioned) | Keys exposed if .env committed or leaked |
| MEDIUM | Backup/recovery | No documented backup strategy | `docker compose down -v` deletes data forever |
| MEDIUM | Secret rotation | No rotation procedure | Must restart stack to rotate DB password |
| MEDIUM | Network isolation | Sub-stacks share Docker daemon | Escaping one container could reach observability stack |
| LOW | Cache auth | Redis without `requirepass` | localhost-only attack surface (low risk) |

---

## Detailed Remediation

### Vector 1: Image Supply Chain (CRITICAL)

**Problem:** Lines 276, 336 in `memory/compose.yaml`:
```yaml
image: ghcr.io/plastic-labs/honcho:v3.0.3  # No digest
```

The spec requires (line 494) "all images in Compose files must have @sha256: digest" but honcho images are not pinned.

**Attack Scenario:**
1. Attacker gains temporary access to plastic-labs org on GHCR
2. Re-pushes malicious code as `honcho:v3.0.3`
3. Next `docker compose pull` fetches malicious image
4. Deriver executes injected code with access to DB and API keys

**Remediation:**

```bash
# Step 1: Get the exact digest for honcho:v3.0.3
docker pull ghcr.io/plastic-labs/honcho:v3.0.3
docker inspect --format='{{index .RepoDigests 0}}' \
  ghcr.io/plastic-labs/honcho:v3.0.3
# Output: ghcr.io/plastic-labs/honcho@sha256:abc123...

# Step 2: Update memory/compose.yaml
```

**Updated `docker/memory/compose.yaml`:**
```yaml
services:
  honcho-api:
    # BEFORE: image: ghcr.io/plastic-labs/honcho:v3.0.3
    # AFTER:
    image: ghcr.io/plastic-labs/honcho:v3.0.3@sha256:REPLACE_WITH_ACTUAL_DIGEST

  honcho-deriver:
    # BEFORE: image: ghcr.io/plastic-labs/honcho:v3.0.3
    # AFTER:
    image: ghcr.io/plastic-labs/honcho:v3.0.3@sha256:REPLACE_WITH_ACTUAL_DIGEST
```

**Verification:**
- Run `uv run mde-py validate --docker` (should pass digest check)
- Run `docker buildx bake --print` (should show resolved image)

---

### Vector 2: Authentication Disabled by Default (HIGH)

**Problem:** Line 287 in `memory/compose.yaml`:
```yaml
- AUTH_USE_AUTH=${AUTH_USE_AUTH:-false}
```

Auth is disabled for "local use," but there's no enforcement preventing binding to `0.0.0.0:8000` instead of `127.0.0.1:8000`. If exposed, unauthenticated access to all sessions.

**Attack Scenario:**
1. Developer accidentally exposes honcho-api on `0.0.0.0:8000` (no `127.0.0.1` binding)
2. Attacker on network reaches API
3. Can list/read/delete all sessions and memories

**Remediation:**

**Option A: Enforcement at Compose Level (Recommended)**

Update `docker/memory/compose.yaml`:
```yaml
honcho-api:
  ports:
    # ONLY bind to localhost; fail if anyone tries 0.0.0.0
    - "127.0.0.1:8000:8000"
  # Add environment validation:
  environment:
    # ... existing ...
    - AUTH_USE_AUTH=${AUTH_USE_AUTH:-false}
  # NEW: Health check rejects if auth required but not set
  healthcheck:
    test: |
      [
        "CMD", "python", "-c",
        "import requests, os; \
         auth_enabled = os.getenv('AUTH_USE_AUTH') == 'true'; \
         if auth_enabled and not os.getenv('AUTH_JWT_SECRET'): exit(1); \
         requests.get('http://localhost:8000/openapi.json')"
      ]
    interval: 10s
    timeout: 5s
    start_period: 30s
    retries: 3
```

**Option B: Documentation (Fallback)**

Add to `.env.example`:
```bash
# Security: AUTH_USE_AUTH should be 'false' ONLY for localhost deployments
# (port 127.0.0.1:8000 binding enforced in compose.yaml).
# If deploying beyond localhost, set AUTH_USE_AUTH=true MANDATORY.
AUTH_USE_AUTH=false

# If AUTH_USE_AUTH=true, generate a random secret:
# python -c "import secrets; print(secrets.token_hex(32))"
AUTH_JWT_SECRET=
```

Add to design spec comment (line 283-287):
```yaml
# Auth disabled for local use. WARNING: If exposing API beyond localhost,
# set AUTH_USE_AUTH=true and AUTH_JWT_SECRET=<random> MANDATORY.
# Port binding enforces localhost-only (127.0.0.1:8000), preventing accidental
# network exposure.
```

**Verification:**
- `uv run mde-py memory up` and test: `curl -v http://0.0.0.0:8000/v3/sessions` (should fail)
- Test: `curl -v http://127.0.0.1:8000/v3/sessions` (should work without auth)

---

### Vector 3 & 4: Plaintext Secrets in Environment (MEDIUM)

**Problem:** Lines 281, 289-293:
- `DB_CONNECTION_URI` contains password: `postgresql+psycopg://honcho:${HONCHO_DB_PASSWORD}@...`
- `LLM_ANTHROPIC_API_KEY` in `.env` file (not confirmed in .gitignore)

Both are visible in `docker inspect` and within container filesystems.

**Attack Scenario:**
1. Attacker with host access runs `docker inspect mde-memory-honcho-api-1 | grep -i password`
2. Gets `HONCHO_DB_PASSWORD` in plaintext
3. Can connect directly to honcho-db or use it elsewhere

**Remediation:**

**Option A: Docker Secrets (Production)**

Only works with Docker Swarm; not available in Compose standalone. Skip for now.

**Option B: Secret Files (Compose v2.20+)**

Update `docker/memory/compose.yaml`:
```yaml
services:
  honcho-api:
    environment:
      # BEFORE:
      # - DB_CONNECTION_URI=postgresql+psycopg://honcho:${HONCHO_DB_PASSWORD}@honcho-db:5432/honcho
      # AFTER: Read password from secret file
      - DB_CONNECTION_URI=postgresql+psycopg://honcho:${HONCHO_DB_PASSWORD_FILE}/honcho-db:5432/honcho
      # Docker mounts secrets to /run/secrets/<name>
    secrets:
      - honcho_db_password  # Name defined below
    env_file:
      - path: .env
        required: false

  honcho-deriver:
    environment:
      # Same as honcho-api
      - DB_CONNECTION_URI=postgresql+psycopg://honcho:${HONCHO_DB_PASSWORD_FILE}/honcho-db:5432/honcho
    secrets:
      - honcho_db_password

secrets:
  honcho_db_password:
    file: ${HONCHO_DB_PASSWORD_FILE:-./.secrets/honcho_db_password}
    # Or use external secret store (Doppler, 1Password, etc.)
```

**Problem:** This approach requires Compose to read the secret file at startup, which still exposes password in the compose environment. Better approach: Use external secret store or fnox (already integrated in project).

**Option C: fnox Integration (Recommended)**

Since the project already uses fnox for secrets (see `secrets-management.md`), use it:

```bash
# Store HONCHO_DB_PASSWORD in macOS Keychain
fnox set HONCHO_DB_PASSWORD "$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"

# In memory stack, read from fnox
```

Update `docker/memory/compose.yaml`:
```yaml
services:
  honcho-api:
    environment:
      # Sourced from env at container start, not in Compose file
      - DB_CONNECTION_URI=postgresql+psycopg://honcho:${HONCHO_DB_PASSWORD}@honcho-db:5432/honcho
```

Create startup script `src/mde/domain/memory_stack.py`:
```python
def stack_up(**kwargs):
    """Start memory stack, injecting secrets from fnox."""
    import subprocess
    import os
    from pathlib import Path

    # Load HONCHO_DB_PASSWORD from Keychain
    try:
        password = subprocess.run(
            ["fnox", "get", "HONCHO_DB_PASSWORD"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        raise RuntimeError("HONCHO_DB_PASSWORD not set in Keychain. Run: fnox set HONCHO_DB_PASSWORD")

    env = os.environ.copy()
    env["HONCHO_DB_PASSWORD"] = password

    # Load LLM keys from .env.local (not versioned)
    env_local = Path(".env.local")
    if env_local.exists():
        from dotenv import load_dotenv
        load_dotenv(env_local)

    subprocess.run(
        ["docker", "compose", "-f", "docker/memory/compose.yaml", "up", "-d"],
        env=env,
        check=True
    )
```

**File Organization:**
- `.env` (versioned): non-sensitive config
- `.env.local` (git-ignored): LLM API keys
- Keychain via fnox: HONCHO_DB_PASSWORD
- Confirm in `.gitignore`:
  ```
  .env.local
  docker/.env.local
  .secrets/
  ```

**Verification:**
- `docker inspect` should NOT show HONCHO_DB_PASSWORD or LLM keys
- `docker compose config` should show redacted values

---

### Vector 5: Data Persistence / Backup (MEDIUM)

**Problem:** Lines 443-445:
```yaml
volumes:
  honcho-pgdata:
  honcho-redis-data:
```

Unnamed volumes. `docker compose down -v` or accidental `docker volume rm` deletes data forever.

**Remediation:**

Create `docker/memory/backup.sh`:
```bash
#!/bin/bash
set -euo pipefail

# Backup PostgreSQL
BACKUP_DIR="./backups/$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$BACKUP_DIR"

echo "Backing up PostgreSQL..."
docker compose -f docker/memory/compose.yaml exec -T honcho-db \
  pg_dump -U honcho -d honcho \
  > "$BACKUP_DIR/honcho.sql"

echo "Backing up Redis..."
docker compose -f docker/memory/compose.yaml exec -T honcho-redis \
  redis-cli BGSAVE

echo "Backup complete: $BACKUP_DIR"
ls -lh "$BACKUP_DIR"
```

Add to `.mise.toml`:
```toml
[tasks.memory:backup]
description = "Backup Honcho memory stack (PostgreSQL + Redis)"
run = "bash docker/memory/backup.sh"

[tasks.memory:restore]
description = "Restore Honcho from backup"
run = "bash docker/memory/restore.sh"
```

Add to design spec (line 642, before "Reproducibility Checklist"):
```markdown
## Backup & Recovery

### Daily Backup

Run before any destructive operations:

```bash
uv run mde-py memory backup
```

### Restore from Backup

```bash
# List available backups
ls backups/

# Restore (requires stopped stack)
uv run mde-py memory down
uv run mde-py memory restore --from backups/2026-03-23_09-00-00
uv run mde-py memory up
```

### Volume Snapshot (Optional)

For added safety, use Docker's native snapshot feature:

```bash
# Create a snapshot of current volumes
docker volume inspect honcho-pgdata --format '{{.Mountpoint}}' | xargs -I {} sudo cp -r {} ./pgdata-snapshot-$(date +%s)
```
```

---

### Vector 6: Secret Rotation (MEDIUM)

**Problem:** No mechanism to rotate `HONCHO_DB_PASSWORD` without stopping the stack.

**Remediation:**

Update PostgreSQL to support online password changes:

```sql
-- This runs inside the container
ALTER USER honcho WITH PASSWORD 'new_password';
```

Create `src/mde/domain/memory_stack.py`:
```python
def rotate_db_password(new_password: str):
    """Rotate HONCHO_DB_PASSWORD without downtime."""
    import subprocess

    # Step 1: Change password in PostgreSQL
    subprocess.run([
        "docker", "compose", "-f", "docker/memory/compose.yaml",
        "exec", "-T", "honcho-db",
        "psql", "-U", "honcho", "-d", "honcho",
        "-c", f"ALTER USER honcho WITH PASSWORD '{new_password}';"
    ], check=True)

    # Step 2: Update Keychain
    subprocess.run(["fnox", "set", "HONCHO_DB_PASSWORD", new_password], check=True)

    # Step 3: Restart API to pick up new password
    subprocess.run([
        "docker", "compose", "-f", "docker/memory/compose.yaml",
        "restart", "honcho-api", "honcho-deriver"
    ], check=True)

    print("Database password rotated. Restarted API and deriver.")
```

Add CLI subcommand to `src/mde/cli.py`:
```python
memory_sub.add_parser(
    "rotate-password",
    help="Rotate HONCHO_DB_PASSWORD (generates new random secret)"
)
```

Add to `.mise.toml`:
```toml
[tasks.memory:rotate-password]
description = "Rotate HONCHO_DB_PASSWORD (security maintenance)"
run = "uv run mde-py memory rotate-password"
```

**Policy:** Rotate password every 90 days or immediately if leaked. Document in CLAUDE.md.

---

### Vector 7: Network Isolation (MEDIUM)

**Problem:** Sub-stacks (memory, observability) share Docker daemon; lack explicit network boundaries.

**Remediation:**

Update `docker/compose.yaml`:
```yaml
# BEFORE: No network definition
# AFTER:

networks:
  memory:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

  observability:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/16

include:
  - path: ./observability/compose.yaml
  - path: ./memory/compose.yaml
```

Update `docker/memory/compose.yaml`:
```yaml
# Add to each service
services:
  honcho-api:
    networks:
      - memory
  honcho-deriver:
    networks:
      - memory
  honcho-db:
    networks:
      - memory
  honcho-redis:
    networks:
      - memory

# Add at end
networks:
  memory:
    external: true  # Defined in root compose.yaml
```

**Effect:** Containers in memory stack can reach each other but CANNOT reach observability containers (tempo, loki, etc.).

**Verification:**
```bash
uv run mde-py memory up
uv run mde-py observability up

# This should FAIL (no cross-stack access)
docker exec mde-memory-honcho-api-1 curl http://mde-observability-loki-1:3100/loki/api/v1/label

# This should SUCCEED (same-stack access)
docker exec mde-memory-honcho-api-1 curl http://honcho-db:5432 || true  # Connection refused is OK
```

---

### Vector 8: Redis Authentication (LOW)

**Problem:** Redis runs without `requirepass`. Localhost-only but still unprotected.

**Remediation:**

Update `docker/memory/compose.yaml`:
```yaml
honcho-redis:
  image: redis:8.2@sha256:DIGEST_HERE
  command:
    - "redis-server"
    - "--requirepass"
    - "${REDIS_PASSWORD:-$(python3 -c 'import secrets; print(secrets.token_hex(16))')}"
    - "--bind"
    - "127.0.0.1"  # Enforce localhost-only
  environment:
    - REDIS_PASSWORD=${REDIS_PASSWORD}
  # ... rest of config
```

Update `docker/memory/compose.yaml` (honcho-api and honcho-deriver):
```yaml
honcho-api:
  environment:
    # BEFORE: - CACHE_URL=redis://honcho-redis:6379/0?suppress=true
    # AFTER:
    - CACHE_URL=redis://:${REDIS_PASSWORD}@honcho-redis:6379/0?suppress=true
```

Add to `.env.example`:
```bash
# Redis authentication (optional but recommended)
REDIS_PASSWORD=                 # Generate: python3 -c 'import secrets; print(secrets.token_hex(16))'
```

**Note:** This is optional (LOW severity) because Redis is localhost-only and not exposed. Prioritize CRITICAL/HIGH vectors first.

---

## Verification Checklist

Before merging PR B:

- [ ] **Image pinning**: All images have @sha256: digest (especially honcho:v3.0.3)
- [ ] **Auth enforcement**: PORT binding is 127.0.0.1:8000 only (documented)
- [ ] **Secrets**: HONCHO_DB_PASSWORD NOT in .env (use fnox or Keychain)
- [ ] **LLM keys**: LLM_* keys in .env.local (git-ignored), not .env
- [ ] **Backup**: `uv run mde-py memory backup` works and creates timestamped backups
- [ ] **Network isolation**: Compose defines explicit networks for memory/observability
- [ ] **.gitignore**: Confirms .env.local, .secrets/, backups/ are excluded
- [ ] **validate --docker**: Passes all checks (version, digest, port conflicts, healthchecks)
- [ ] **Documentation**: Design spec updated with security mitigations and policies

## Timeline

**Before Merge (P0):**
1. Add @sha256: digest to honcho images (2 min)
2. Confirm .gitignore includes .env.local (2 min)
3. Add .env example with LLM key placement (2 min)

**Post-Merge, Before Deployment (P1):**
1. Implement fnox integration for HONCHO_DB_PASSWORD (30 min)
2. Add backup/restore scripts (45 min)
3. Configure explicit networks (15 min)

**Ongoing (P2):**
1. Monitor secret rotation policy (quarterly review)
2. Audit volume usage with `docker volume ls`
3. Test restore procedure quarterly

---

## References

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Secrets Management Policy](../../superpowers/secrets-management.md)
- [Honcho Upstream Config](https://github.com/plastic-labs/honcho/blob/main/src/config.py)
- [Adversarial Review Findings](../findings/adversarial-security-review.yaml)
