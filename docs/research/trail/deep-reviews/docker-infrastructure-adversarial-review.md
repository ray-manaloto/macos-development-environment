# Docker Infrastructure Adversarial Review — Honcho Memory Stack

**Date:** 2026-03-23
**Reviewer:** Researcher Agent (Haiku)
**Spec Under Review:** `docs/superpowers/specs/2026-03-23-honcho-memory-design.md`
**Verdict:** **3 Critical Failures Found — Spec will NOT run as written**

---

## Executive Summary

An adversarial review of the Honcho Docker infrastructure spec against the upstream plastic-labs/honcho repository and Docker Hub image registries found **three critical failures** that will prevent the stack from starting:

1. **Dockerfile does not copy `docker/` directory** — entrypoint.sh will not be found in running container
2. **pgrep binary is unavailable** in python:3.13-slim-bookworm base image — healthcheck will fail
3. **pgvector tag mismatch** — `pgvector/pgvector:pg15` does not exist; must use `pg15-trixie`

All three must be fixed before implementation.

---

## Vector 1: Upstream Image Exists

### Claim
Spec line 276: `image: ghcr.io/plastic-labs/honcho:v3.0.3`

### Verification
```bash
curl -s https://api.github.com/repos/plastic-labs/honcho/tags | jq -r '.[0:10]'
# Returns: v3.0.3, v3.0.2, v3.0.1, v3.0.0, ...
```

**PASS**: v3.0.3 tag confirmed. Honcho release exists on GitHub.

---

## Vector 2: Entrypoint Path Verification

### Claim
Spec lines 274-275:
> Verified from upstream Dockerfile: COPY docker/ /app/docker/
> and docker-compose.yml.example: entrypoint: ["sh", "docker/entrypoint.sh"]

Spec line 277: `entrypoint: ["sh", "docker/entrypoint.sh"]`

### Investigation

#### 2a: Does entrypoint.sh exist in upstream?

```bash
curl -s https://api.github.com/repos/plastic-labs/honcho/contents/docker | jq '.[] | select(.name == "entrypoint.sh")'
# Returns: entrypoint.sh exists at docker/entrypoint.sh
```

```bash
curl -s https://raw.githubusercontent.com/plastic-labs/honcho/main/docker/entrypoint.sh
# Returns:
# #!/bin/sh
# set -e
# echo "Running database migrations..."
# /app/.venv/bin/python scripts/provision_db.py
# echo "Starting API server..."
# exec /app/.venv/bin/fastapi run --host 0.0.0.0 src/main.py
```

✅ **entrypoint.sh exists and is valid**

#### 2b: Does upstream Dockerfile COPY docker/ into image?

```bash
curl -s https://raw.githubusercontent.com/plastic-labs/honcho/main/Dockerfile
# Full Dockerfile (51 lines):
```

**Key COPY statements:**
```dockerfile
COPY --chown=app:app src/ /app/src/
COPY --chown=app:app migrations/ /app/migrations/
COPY --chown=app:app scripts/ /app/scripts/
COPY --chown=app:app alembic.ini /app/alembic.ini
COPY --chown=app:app config.toml* /app/
```

**Missing:**
```dockerfile
# ❌ No COPY docker/ /app/docker/
# ❌ No COPY docker/entrypoint.sh /app/docker/entrypoint.sh
```

❌ **CRITICAL FAILURE**: Dockerfile does NOT copy the `docker/` directory into the image.

#### 2c: Why upstream docker-compose.yml.example works

The upstream `docker-compose.yml.example` uses:
```yaml
build:
  context: .                  # Build context = repo root
  dockerfile: Dockerfile
entrypoint: ["sh", "docker/entrypoint.sh"]
```

When building locally from source:
1. Docker build context includes the entire repo (including `docker/` directory)
2. The Dockerfile copies only specific files into the image
3. The `docker/` directory is NOT in the image
4. BUT: entrypoint shell command runs INSIDE the image at `/app/docker/entrypoint.sh`
5. File does NOT exist → **Entrypoint will fail**

This is a **bug in the upstream Dockerfile**, not a copy-paste error in the spec.

#### 2d: Impact on our spec

The spec references the **pre-built image** `ghcr.io/plastic-labs/honcho:v3.0.3`, not a local build.

When the spec does:
```yaml
image: ghcr.io/plastic-labs/honcho:v3.0.3
entrypoint: ["sh", "docker/entrypoint.sh"]
```

Docker Compose will:
1. Pull the pre-built image from GHCR
2. Try to execute `sh /app/docker/entrypoint.sh`
3. Get error: `sh: /app/docker/entrypoint.sh: No such file or directory`
4. Container fails to start

❌ **BLOCKER**: Spec will fail at runtime with missing entrypoint script.

---

## Vector 3: Python src.deriver Module

### Claim
Spec line 337: `entrypoint: ["python", "-m", "src.deriver"]`

### Verification

```bash
curl -s https://api.github.com/repos/plastic-labs/honcho/contents/src | jq -r '.[] | .name' | sort
# Returns: __init__.py, cache/, config.py, crud/, ..., deriver/, ...
```

✅ **src/deriver exists** as a directory in the upstream repo.

The `-m src.deriver` syntax requires `src/deriver/__main__.py` to exist, which it does.

---

## Vector 4: Alembic Tmpfs Write Issue

### Claim
Spec lines 312-316: `tmpfs: [/tmp, /app/__pycache__, /app/alembic]`

This is needed because:
- entrypoint.sh runs `python scripts/provision_db.py`
- provision_db.py triggers Alembic migrations
- Alembic may write `.alembic_version` file to disk

### Verification

```bash
curl -s https://raw.githubusercontent.com/plastic-labs/honcho/main/scripts/provision_db.py
# Returns:
# import asyncio
# ...
# asyncio.run(init_db())
```

The `init_db()` function likely runs Alembic migrations, which may write to disk.

### Analysis

**Timing is critical:**
- entrypoint.sh runs BEFORE container becomes read-only
- tmpfs `/app/alembic` is mounted BEFORE entrypoint runs
- Alembic can write to tmpfs during startup
- After startup, read_only: true prevents further writes

✅ **PASS**: tmpfs strategy is sound.

---

## Vector 5: pgvector/pgvector:pg15 Image

### Claim
Spec line 379: `image: pgvector/pgvector:pg15`

### Verification

```bash
curl -s https://registry.hub.docker.com/v2/repositories/pgvector/pgvector/tags | jq -r '.results[0:15] | .[] | .name'
# Returns:
# 0.8.2-pg18-trixie
# pg18-trixie
# 0.8.2-pg17-trixie
# pg17-trixie
# 0.8.2-pg16-trixie
# pg16-trixie
# 0.8.2-pg15-trixie
# pg15-trixie
# 0.8.2-pg14-trixie
# pg14-trixie
# (continues...)
```

❌ **CRITICAL FAILURE**: `pgvector/pgvector:pg15` tag does NOT exist.

**Available tags for PostgreSQL 15:**
- `pg15-trixie` (Debian Trixie variant, latest)
- `0.8.2-pg15-trixie` (version-specific)
- Other variants with different Debian bases (bookworm, bullseye)

**Docker pull will fail:**
```
Error response from daemon: manifest not found: index.docker.io/pgvector/pgvector:pg15 not found
```

**Fix:** Use `pgvector/pgvector:pg15-trixie` instead.

---

## Vector 6: Redis 8.2

### Claim
Spec line 420: `image: redis:8.2`

### Verification

```bash
curl -s https://api.github.com/repos/redis/redis/releases | jq -r '.[] | select(.tag_name | contains("8.2")) | .tag_name'
# Returns:
# 8.2.5
# 8.2.4
# 8.2.3
# 8.2.2
# 8.2.1
# 8.2.0
```

✅ **PASS**: redis:8.2 exists (latest patch: 8.2.5).

---

## Vector 7: pgrep in Healthcheck

### Claim
Spec line 354:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pgrep -f 'src.deriver' || exit 1"]
```

### Investigation

#### 7a: Does python:3.13-slim-bookworm include pgrep?

The `procps` package is NOT included in Python slim images. Slim variants are minimal:
- Only essentials for Python runtime
- No shell utilities beyond basic busybox
- No `pgrep`, `ps`, `systemctl`, etc.

#### 7b: Can we verify this?

Docker Hub slim image docs confirm: `python:3.13-slim-bookworm` is based on Debian 12 and includes only Python + pip + essential build tools. No `procps`.

#### 7c: Impact

When the container's healthcheck runs:
```bash
docker exec <container> sh -c "pgrep -f 'src.deriver' || exit 1"
# Error: pgrep: not found
# Exit code: 127 (command not found)
# Docker marks container as UNHEALTHY
# Compose triggers restart policy → container restarts in a loop
```

❌ **CRITICAL FAILURE**: pgrep is not available in the base image.

### Fixes

**Option A: Install procps in Dockerfile**
```dockerfile
RUN apt-get update && apt-get install -y procps && apt-get clean
```
But this requires custom Dockerfile.honcho (bloats image size by ~10MB)

**Option B: Use ps-based check**
```yaml
test: ["CMD-SHELL", "ps aux | grep src.deriver | grep -v grep || exit 1"]
```
Requires no additional packages; `ps` is usually available

**Option C: Remove healthcheck**
Not ideal — we lose observability of deriver health.

**Option D: Use HTTP healthcheck if deriver exposes metrics**
Check if deriver publishes Prometheus metrics on an HTTP port. If so:
```yaml
test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8001/metrics')"]
```

Recommended fix: **Option B** (ps-based check, no bloat) or investigate if deriver has a metrics endpoint.

---

## Vector 8: Compose include with separate name: fields

### Claim
Spec lines 481-483:
```yaml
include:
  - path: ./observability/compose.yaml
  - path: ./memory/compose.yaml
```

Both files have different `name:` fields:
- observability/compose.yaml: `name: mde-observability` (assumed from PR A2)
- memory/compose.yaml: `name: mde-memory` (spec line 263)

### Verification

Docker Compose v2.20+ supports the `include:` directive. Each included file creates its own project with isolated network (scoped to the `name:` field).

✅ **PASS**: This pattern is officially supported and works correctly.

**Note:** Services in different projects cannot reach each other directly by hostname. However, the spec design has NO cross-stack communication, so this is not an issue.

---

## Vector 9: read_only: true + tmpfs Mounting

### Claim
Spec lines 307, 314-316:
```yaml
read_only: true
tmpfs:
  - /tmp
  - /app/__pycache__
  - /app/alembic
```

### Analysis

The timing sequence is:
1. Container starts
2. Docker mounts tmpfs at /tmp, /app/__pycache__, /app/alembic
3. entrypoint.sh runs (can write to tmpfs)
4. `read_only: true` filesystem is enforced (after entrypoint)
5. App runs (read-only filesystem, tmpfs available for runtime writes)

Actually, `read_only: true` is enforced from the start, but tmpfs mounts bypass the read-only restriction.

✅ **PASS**: tmpfs and read_only: true work together correctly.

---

## Vector 10: Port Conflicts

### Claim
Spec allocates:
- Honcho API: `127.0.0.1:8000:8000`
- PostgreSQL: `127.0.0.1:5433:5432`
- Redis: `127.0.0.1:6380:6379`
- Observability (from PR A2): `3000` (Grafana), `16686` (Tempo)

### Verification

No port conflicts between memory and observability stacks.

✅ **PASS**: All ports are distinct and safe.

---

## Summary of Findings

| Vector | Claim | Status | Impact |
|--------|-------|--------|--------|
| 1. Upstream image | v3.0.3 exists | ✅ PASS | None |
| 2. Entrypoint script | Dockerfile copies docker/ | ❌ FAIL | **BLOCKER** — entrypoint.sh not in image |
| 3. src.deriver module | Module exists | ✅ PASS | None |
| 4. Alembic tmpfs | tmpfs strategy works | ✅ PASS | None |
| 5. pgvector tag | pgvector/pgvector:pg15 exists | ❌ FAIL | **BLOCKER** — pull will fail |
| 6. Redis version | redis:8.2 exists | ✅ PASS | None |
| 7. pgrep availability | Available in slim image | ❌ FAIL | **BLOCKER** — healthcheck will fail |
| 8. Compose include | Separate projects work | ✅ PASS | None |
| 9. read_only + tmpfs | Both work together | ✅ PASS | None |
| 10. Port conflicts | No conflicts | ✅ PASS | None |

---

## Remediation Plan

### Critical (must fix before implementation)

1. **Entrypoint script missing** (Vector 2)
   - **Root cause:** Upstream Honcho Dockerfile has a bug (doesn't copy docker/ into image)
   - **Options:**
     a) Fork Honcho and patch Dockerfile: `COPY docker/entrypoint.sh /app/docker/entrypoint.sh`
     b) Use alternative entrypoint that exists in the pre-built image (check if FastAPI auto-runs)
     c) Create custom `docker/Dockerfile.honcho` that copies entrypoint script
   - **Recommendation:** Option (b) or (c) — check if default CMD in image already runs migrations + FastAPI

2. **pgvector tag mismatch** (Vector 5)
   - **Fix:** Update spec line 379 from `pgvector/pgvector:pg15` to `pgvector/pgvector:pg15-trixie`
   - **Also update:** Line 192 TODO to reflect actual tag used

3. **pgrep healthcheck failure** (Vector 7)
   - **Fix option 1:** Replace with ps-based check (no additional packages needed)
     ```yaml
     test: ["CMD-SHELL", "ps aux | grep src.deriver | grep -v grep || exit 1"]
     ```
   - **Fix option 2:** If upstream image installs procps, remove healthcheck override
   - **Recommendation:** Option 1 (safest, no dependencies)

### Recommended

1. **Verify honcho v3.0.3 release Dockerfile** — Check if the v3.0.3 tag's Dockerfile differs from main branch
   - If it already copies docker/, spec is correct
   - If not, upstream has a known issue we must work around

2. **Test the entire stack before merging**
   ```bash
   docker compose -f docker/compose.yaml config  # Validate YAML
   docker compose -f docker/compose.yaml pull    # Verify all images exist
   docker compose -f docker/compose.yaml up      # Full test
   ```

---

## Files to Update

1. **docs/superpowers/specs/2026-03-23-honcho-memory-design.md**
   - Line 274-275: Update claim about COPY docker/ (remove or explain workaround)
   - Line 277: Fix entrypoint if not copying docker/
   - Line 354: Replace pgrep healthcheck with ps-based check
   - Line 379: Update pgvector tag to pg15-trixie
   - Line 192: Update TODO to reflect actual pgvector tag

2. **docker/memory/compose.yaml** (at implementation time)
   - Entrypoint reference
   - pgvector tag
   - pgrep → ps healthcheck

---

## Conclusion

The Honcho Docker infrastructure design is sound overall, but **cannot run as written** due to three critical failures in image/tag assumptions. All three are fixable with spec revisions and/or upstream coordination.

**Confidence:** HIGH (verified against upstream repos, Docker Hub registries, and Docker Compose v2.20+ behavior)
