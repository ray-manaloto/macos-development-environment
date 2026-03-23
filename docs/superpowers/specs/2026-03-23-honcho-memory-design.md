# Honcho Persistent Memory — Design Spec

**Date**: 2026-03-23
**Status**: Draft
**PR**: B (follows PR A2 — LGTM observability stack)

## Context

PR A2 delivered observability (traces/logs via LGTM Docker stack). This PR adds
persistent semantic memory so Claude Code sessions can recall prior work,
preferences, and project context across sessions.

### Design Decisions (for future AI agents)

<!-- WHY: These comments explain the rationale behind architectural choices.
     AI agents working on this codebase should read these to understand constraints
     before making changes. Each decision has a reference to the discussion that
     produced it. -->

1. **Honcho complements existing memory, does not replace it.**
   The project has 3 existing memory layers: auto-memory (~/.claude/projects/),
   .remember/ plugin (session buffer), and research trail (YAML provenance).
   Honcho adds a 4th layer: semantic search over past sessions. None of the
   existing layers are removed.
   _Rationale: each layer serves a different purpose — auto-memory for prefs,
   .remember for session continuity, research trail for provenance, Honcho for
   cross-session semantic recall._

2. **Use the official `plastic-labs/claude-honcho` plugin, don't build custom.**
   The official plugin provides hooks (SessionStart/End/PostToolUse/PreCompact/Stop),
   MCP server, skills (/interview, /config, /status, /setup), and self-hosted
   support (`endpoint.environment = "local"` → `http://localhost:8000/v3`).
   _Rationale: assemble-don't-build policy. The plugin is battle-tested, MIT licensed,
   and maintained by the Honcho team. Building a custom TypeScript plugin would
   duplicate 2000+ lines of hook/MCP/config code._

3. **Bake for builds, Compose for runtime.**
   Docker Bake (HCL) defines all image build targets with inheritance, pinning,
   and multi-platform support. Compose handles runtime orchestration (networking,
   volumes, healthchecks, depends_on). These are complementary tools — Bake is
   NOT a superset of Compose.
   _Rationale: Docker best practice as of 2025. Bake consolidates build config
   that would otherwise be scattered across `docker build` commands or Compose
   `build:` blocks. See https://docs.docker.com/guides/compose-bake/_

4. **Root Compose with `include` for modular sub-stacks.**
   A single `docker/compose.yaml` uses the Compose `include:` directive to pull
   in sub-stack Compose files (observability, memory). Each sub-stack is
   self-contained with its own configs but shares the root network.
   _Rationale: Docker's recommended pattern for multi-service projects since
   Compose v2.20. Replaces the old pattern of separate `docker-compose.yml`
   files invoked with `-f` flags._

5. **Rename `docker-compose.yml` → `compose.yaml`.**
   Modern Docker convention uses `compose.yaml` (not `docker-compose.yml`).
   Docker Compose auto-discovers `compose.yaml` in the current directory.
   _Rationale: Official Docker docs migrated to this naming in 2024. The `.yml`
   extension and `docker-compose` prefix are legacy._

6. **Self-hosted Honcho, not SaaS.**
   The Honcho API runs locally via Docker alongside PostgreSQL+pgvector and Redis.
   No external API calls for memory operations — all data stays on-machine.
   _Rationale: privacy (session transcripts contain code), latency (local API
   calls vs cloud roundtrip), and cost (no SaaS subscription)._

7. **Hybrid hook integration: official plugin hooks + mde lifecycle management.**
   The claude-honcho plugin registers its own hooks for memory save/restore.
   The mde package provides `uv run mde-py memory {up,down,status}` for Docker
   lifecycle management. No custom Python SDK client needed — the plugin's
   TypeScript MCP server handles all Honcho API communication.
   _Rationale: separation of concerns. The plugin owns memory read/write logic,
   mde owns infrastructure lifecycle. No Python SDK module avoids duplicating
   what the plugin already does in TypeScript._

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Claude Code Session                                      │
│                                                          │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │ mde hooks    │    │ claude-honcho plugin          │   │
│  │ (Python)     │    │ (TypeScript/Bun)              │   │
│  │              │    │                               │   │
│  │ session_start│    │ SessionStart → load context   │   │
│  │ guard_install│    │ SessionEnd   → save messages  │   │
│  │ log_outcome  │    │ PostToolUse  → track changes  │   │
│  │ post_compact │    │ PreCompact   → persist state  │   │
│  │              │    │ Stop         → flush buffers  │   │
│  └──────────────┘    │ UserPrompt   → refresh ctx    │   │
│                      │                               │   │
│                      │ MCP Server → memory tools     │   │
│                      │ Skills → /interview, /status  │   │
│                      └──────────┬───────────────────┘   │
│                                 │                        │
└─────────────────────────────────┼────────────────────────┘
                                  │ HTTP (localhost:8000/v3)
┌─────────────────────────────────┼────────────────────────┐
│ Docker (docker/compose.yaml)    │                        │
│                                 ▼                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │ memory stack (docker/memory/compose.yaml)         │   │
│  │                                                   │   │
│  │  honcho-api ──► PostgreSQL 15 + pgvector         │   │
│  │  (FastAPI)      (vector embeddings, sessions)     │   │
│  │       │                                           │   │
│  │  honcho-deriver ──► Redis 8.2                    │   │
│  │  (background     (cache, pub/sub)                │   │
│  │   reasoning)                                      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ observability stack (docker/observability/...)     │   │
│  │  Collector → Tempo, Loki → Grafana               │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

## File Structure

```
docker/
├── docker-bake.hcl                    # Build definitions for ALL images
│                                      # Groups: "default" (all), "observability", "memory"
│                                      # Targets inherit from "_common" for shared security
├── compose.yaml                       # Root orchestrator — includes sub-stacks
│                                      # Entry point: `docker compose -f docker/compose.yaml up`
├── .env.example                       # All required env vars with documentation
│
├── observability/
│   ├── compose.yaml                   # LGTM stack (renamed from docker-compose.yml)
│   ├── collector-config.yaml          # (existing, unchanged)
│   ├── tempo-config.yaml              # (existing, unchanged)
│   ├── loki-config.yaml              # (existing, unchanged)
│   └── grafana/provisioning/          # (existing, unchanged)
│
└── memory/
    ├── compose.yaml                   # Honcho stack: api, deriver, postgres, redis
    ├── init.sql                       # PostgreSQL init: CREATE EXTENSION vector
    └── .env.example                   # Honcho-specific env vars documented

src/mde/
├── domain/
│   ├── observability_stack.py         # Updated: new compose path, shared helpers
│   ├── memory_stack.py                # NEW: Honcho Docker lifecycle (up/down/status/verify)
│   └── docker_stacks.py              # NEW: shared compose helpers, path constants, health checks
│                                      # All health check logic lives HERE, not in one-off scripts.
│                                      # Compose healthchecks call `uv run mde-py` subcommands
│                                      # so they go through ruff/ty/pytest like everything else.
├── validate/
│   ├── docker.py                      # Updated: validate bake file, compose structure, version
│   └── memory.py                      # NEW: validate Honcho stack health (API + PG + Redis)
└── cli.py                             # Updated: add 'memory' subcommand
```

## Docker Bake File

<!-- WHY docker-bake.hcl exists:
     Before Bake, build config was either:
     (a) scattered across `docker build` commands in scripts, or
     (b) embedded in Compose `build:` blocks which mix build and runtime concerns.
     Bake centralizes all build definitions in one typed, inheritable file.
     Runtime orchestration stays in Compose where it belongs.
     Bake can also READ Compose files as build sources, so builds defined in
     Compose `build:` blocks are automatically available to `docker buildx bake`.

     IMPORTANT: Bake is a BUILD tool, not a pull tool. Pre-built images (Grafana,
     Tempo, Loki, PostgreSQL, Redis) are pinned by digest in Compose files only.
     Bake targets exist only for images we actually build (honcho-api, honcho-deriver).
     Pre-built image versions are documented in comments below for reference. -->

```hcl
# docker/docker-bake.hcl
#
# Centralized build definitions for mde Docker images we build from source.
# Compose files handle runtime (up/down/networking/volumes) and pin pre-built images.
# Bake handles builds (multi-platform, attestations, build args).
#
# DESIGN DECISION: Only images we build from source get Bake targets.
# Pre-built images (Grafana, Tempo, Loki, PostgreSQL, Redis) are pinned by
# digest directly in their respective compose.yaml files. Bake cannot pull
# images — `docker buildx bake` is a build tool, not `docker pull`.
#
# Usage:
#   docker buildx bake -f docker/docker-bake.hcl              # build all
#   docker buildx bake -f docker/docker-bake.hcl honcho-api    # build single target
#
# Pre-built images (pinned in Compose, documented here for reference):
#   observability/compose.yaml:
#     otel/opentelemetry-collector-contrib:0.107.0@sha256:b6552779...
#     grafana/tempo:2.6.1@sha256:ef4384fc...
#     grafana/loki:2.9.10@sha256:35b02acc...
#     grafana/grafana:11.4.0@sha256:d8ea3779...
#   memory/compose.yaml:
#     pgvector/pgvector:pg15-trixie@sha256:<pin at implementation time>
#     redis:8.2@sha256:<pin at implementation time>

# --- Shared base target ---
# All buildable targets inherit from _common for consistent metadata.
# Underscore prefix means Bake won't build it directly.
target "_common" {
  annotations = ["org.opencontainers.image.source=https://github.com/ray-manaloto/macos-development-environment"]
  attest = [
    "type=provenance,mode=max",
    "type=sbom"
  ]
}

# --- Groups ---
# `docker buildx bake` with no args builds "default" (all buildable targets).
group "default" {
  targets = ["honcho-api", "honcho-deriver"]
}

# --- Memory targets ---
# Honcho API and deriver share the same upstream image but have different
# entrypoints. Both use the upstream ghcr.io/plastic-labs/honcho image
# directly — no custom Dockerfile needed unless we layer config on top.
#
# DECISION: Use upstream image directly in Compose (no custom build).
# These Bake targets exist as documentation and for future customization
# (e.g., adding a config overlay Dockerfile). They are currently no-ops
# because Compose references the upstream image by tag+digest.
# To enable custom builds, add a Dockerfile.honcho and update Compose
# to use `image: mde/honcho-api:latest` instead of the upstream ref.

target "honcho-api" {
  inherits   = ["_common"]
  context    = "memory"
  dockerfile = "Dockerfile.honcho"
  tags       = ["mde/honcho-api:latest"]
  args = {
    HONCHO_VERSION = "v3.0.3"
  }
}

target "honcho-deriver" {
  inherits   = ["_common"]
  context    = "memory"
  dockerfile = "Dockerfile.honcho"
  tags       = ["mde/honcho-deriver:latest"]
  args = {
    HONCHO_VERSION = "v3.0.3"
  }
}
```

## Memory Compose Stack

```yaml
# docker/memory/compose.yaml
#
# Honcho persistent memory stack for Claude Code sessions.
#
# HISTORY: Added in PR B (2026-03-23) to complement the observability stack
# from PR A2. Provides semantic memory via the Honcho API — Claude Code's
# official claude-honcho plugin connects to this at localhost:8000/v3.
#
# ARCHITECTURE DECISION: Self-hosted instead of SaaS because session
# transcripts contain source code. All data stays on-machine.
#
# DEPENDENCY: The claude-honcho plugin must be installed in Claude Code
# and configured with endpoint.environment = "local" to connect here.
# See: /plugin marketplace add plastic-labs/claude-honcho

name: mde-memory

services:
  honcho-api:
    # Honcho API server — FastAPI app serving the v3 REST API.
    # The claude-honcho plugin sends HTTP requests to localhost:8000/v3.
    #
    # ENTRYPOINT: The upstream Dockerfile does NOT copy docker/ into the image.
    # The upstream docker-compose.yml.example works by mounting the full source
    # tree as a volume (- .:/app), which is a dev-mode pattern we don't use.
    #
    # The image's built-in CMD is: ["fastapi", "run", "--host", "0.0.0.0", "src/main.py"]
    # But we need to run migrations first. The image DOES contain scripts/provision_db.py
    # (COPY --chown=app:app scripts/ /app/scripts/ in the Dockerfile).
    #
    # Solution: Override entrypoint with an inline shell command that runs
    # migrations then exec's the default CMD.
    image: ghcr.io/plastic-labs/honcho:v3.0.3
    # TODO: Pin digest at implementation time:
    #   docker pull ghcr.io/plastic-labs/honcho:v3.0.3
    #   docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/plastic-labs/honcho:v3.0.3
    entrypoint: ["sh", "-c", "python scripts/provision_db.py && exec fastapi run --host 0.0.0.0 src/main.py"]
    ports:
      # SECURITY: Bound to 127.0.0.1 ONLY. This is the primary mitigation for
      # AUTH_USE_AUTH=false. If this binding is changed to 0.0.0.0, auth MUST
      # be enabled or all session data is exposed to the network.
      - "127.0.0.1:8000:8000"
    environment:
      - DB_CONNECTION_URI=postgresql+psycopg://honcho:${HONCHO_DB_PASSWORD:?Set HONCHO_DB_PASSWORD}@honcho-db:5432/honcho
      - CACHE_URL=redis://honcho-redis:6379/0?suppress=true
      # Auth disabled for local use. To enable:
      # 1. Set AUTH_USE_AUTH=true in .env
      # 2. Set AUTH_JWT_SECRET=<random-secret> in .env (REQUIRED when auth is on)
      # Without AUTH_JWT_SECRET, JWT verification silently fails at runtime.
      - AUTH_USE_AUTH=${AUTH_USE_AUTH:-false}
      - AUTH_JWT_SECRET=${AUTH_JWT_SECRET:-}
    env_file:
      # .env file provides LLM API keys (LLM_ANTHROPIC_API_KEY, etc.)
      # and optional config overrides. See .env.example for full list.
      - path: .env
        required: false
    depends_on:
      honcho-db:
        condition: service_healthy
      honcho-redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/openapi.json')"]
      interval: 10s
      timeout: 5s
      start_period: 30s
      retries: 3
    security_opt:
      - no-new-privileges:true
    read_only: true
    cap_drop:
      - ALL
    tmpfs:
      # /tmp: general temp files, uv cache
      # /app/__pycache__: Python bytecode (PYTHONDONTWRITEBYTECODE=1 but defensive)
      # /app/alembic: Alembic version stamp may be written by provision_db.py
      # NOTE: If provision_db.py writes elsewhere, add those paths here.
      # Test with: docker compose run --rm honcho-api find / -writable 2>/dev/null
      - /tmp
      - /app/__pycache__
      - /app/alembic
    mem_limit: 512m
    cpus: 0.5
    restart: unless-stopped

  honcho-deriver:
    # Background worker that processes messages asynchronously.
    # Runs the "deriver" — Honcho's reasoning pipeline that creates
    # embeddings, summaries, and conclusions from stored messages.
    #
    # REQUIRES LLM API KEYS: The deriver calls LLM providers for reasoning.
    # Keys are loaded from .env file. Without them, the deriver starts but
    # silently skips reasoning tasks. See .env.example for required keys:
    #   LLM_ANTHROPIC_API_KEY, LLM_OPENAI_API_KEY (embeddings),
    #   LLM_GEMINI_API_KEY, LLM_GROQ_API_KEY (fallbacks)
    #
    # NOTE on CACHE_URL: The ?suppress=true parameter is Honcho-specific —
    # it suppresses Redis connection warnings when cache is temporarily
    # unavailable. This is standard Honcho configuration, not a Redis URL
    # extension.
    image: ghcr.io/plastic-labs/honcho:v3.0.3
    # TODO: Pin digest (same image as honcho-api, shared digest)
    entrypoint: ["python", "-m", "src.deriver"]
    environment:
      - DB_CONNECTION_URI=postgresql+psycopg://honcho:${HONCHO_DB_PASSWORD:?Set HONCHO_DB_PASSWORD}@honcho-db:5432/honcho
      - CACHE_URL=redis://honcho-redis:6379/0?suppress=true
      - METRICS_ENABLED=true
    env_file:
      - path: .env
        required: false
    depends_on:
      honcho-db:
        condition: service_healthy
      honcho-redis:
        condition: service_healthy
    healthcheck:
      # The deriver is a long-running background worker, not an HTTP server.
      # python:3.13-slim-bookworm does NOT include procps (no pgrep/ps/pidof).
      # Use pure Python /proc scan to check the deriver process is alive.
      test: ["CMD", "python", "-c", "import os,sys; sys.exit(0 if any('src.deriver' in open(f'/proc/{p}/cmdline','rb').read().decode('utf-8','ignore') for p in os.listdir('/proc') if p.isdigit()) else 1)"]
      interval: 30s
      timeout: 5s
      start_period: 15s
      retries: 3
    security_opt:
      - no-new-privileges:true
    read_only: true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp
      - /app/__pycache__
    mem_limit: 1g
    cpus: 1.0
    restart: unless-stopped

  honcho-db:
    # PostgreSQL 15 with pgvector extension for vector similarity search.
    # Stores all Honcho data: workspaces, peers, sessions, messages,
    # embeddings (1536-dim OpenAI text-embedding-3-small), collections.
    # HNSW indexing on pgvector for fast similarity queries.
    #
    # PORT 5433: Mapped to 5433 on host (not 5432) to avoid conflict with
    # any locally-installed PostgreSQL. Tests connect via localhost:5433.
    image: pgvector/pgvector:pg15-trixie
    # TODO: Pin digest at implementation time:
    #   docker pull pgvector/pgvector:pg15-trixie && docker inspect --format='{{index .RepoDigests 0}}' pgvector/pgvector:pg15-trixie
    command: ["postgres", "-c", "max_connections=200"]
    environment:
      - POSTGRES_DB=honcho
      - POSTGRES_USER=honcho
      - POSTGRES_PASSWORD=${HONCHO_DB_PASSWORD:?Set HONCHO_DB_PASSWORD}
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
      - honcho-pgdata:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U honcho -d honcho"]
      interval: 5s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      # PostgreSQL requires these caps for data directory ownership
      - CHOWN
      - DAC_OVERRIDE
      - FOWNER
      - SETGID
      - SETUID
    mem_limit: 512m
    cpus: 0.5
    restart: unless-stopped

  honcho-redis:
    # Redis cache for Honcho API and deriver worker.
    # Used for session caching, pub/sub between API and deriver,
    # and rate limiting.
    #
    # PORT 6380: Mapped to 6380 on host (not 6379) to avoid conflict with
    # any locally-installed Redis. Tests connect via localhost:6380.
    image: redis:8.2
    # TODO: Pin digest at implementation time:
    #   docker pull redis:8.2 && docker inspect --format='{{index .RepoDigests 0}}' redis:8.2
    ports:
      - "127.0.0.1:6380:6379"
    volumes:
      - honcho-redis-data:/data
    healthcheck:
      test: ["CMD-SHELL", "redis-cli ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
    read_only: true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp
    mem_limit: 128m
    cpus: 0.25
    restart: unless-stopped

volumes:
  honcho-pgdata:
  honcho-redis-data:
```

## Root Compose File

```yaml
# docker/compose.yaml
#
# Root orchestrator for all mde Docker stacks.
#
# PATTERN: Uses Compose `include:` directive (v2.20+) to pull in sub-stacks.
# Each sub-stack is self-contained with its own services, volumes, and configs.
# This file is the single entry point for `docker compose` commands.
#
# WHY NOT a single flat file: Sub-stacks have independent lifecycles.
# Observability can run without memory, and vice versa. The include pattern
# lets each team/PR own its stack without merge conflicts.
#
# USAGE:
#   docker compose -f docker/compose.yaml up                  # start all
#   docker compose -f docker/compose.yaml up honcho-api        # start one service
#   docker compose -f docker/compose.yaml --profile memory up  # (future: profile-gated)
#
# BREAKING CHANGE from PR A2:
#   Old: docker compose -f docker/observability/docker-compose.yml up
#   New: docker compose -f docker/compose.yaml up
#   The observability stack file was renamed from docker-compose.yml to compose.yaml.
#   All Python code paths updated in src/mde/domain/observability_stack.py.

# NETWORKING: Each included sub-stack gets its own default network (scoped by
# project name). Services within a stack can reach each other by hostname.
# Cross-stack communication is NOT needed — observability and memory are
# independent. If cross-stack access is ever needed (e.g., Honcho exporting
# metrics to OTEL collector), define a shared external network here and
# reference it in both sub-stack compose files.

include:
  - path: ./observability/compose.yaml
  - path: ./memory/compose.yaml
```

## Validations & Verification

### New Validations (src/mde/validate/)

1. **Compose structure validation** — verify `docker/compose.yaml` exists and
   includes all expected sub-stacks
2. **Bake file validation** — verify `docker/docker-bake.hcl` parses without errors
   (`docker buildx bake --print`)
3. **Image digest pinning** — all images in Compose files must have `@sha256:` digest
4. **Port conflict detection** — no two services bind the same host port
5. **Healthcheck coverage** — every service must have a healthcheck defined
6. **Environment variable validation** — all `${VAR:?msg}` vars are documented in `.env.example`
7. **Memory stack health** — Honcho API responds to `/openapi.json`, PostgreSQL
   accepts connections, Redis responds to PING

### Updated Validations

1. **Docker validation** (`validate/docker.py`) — add `docker buildx bake --print`
   check, verify compose.yaml includes, check for legacy `docker-compose.yml` files
2. **Observability stack** — update compose file path from `docker-compose.yml` to
   `compose.yaml`

### Verification Commands

```bash
# --- Prerequisites ---
docker compose version --short                     # Must be >= 2.20.0 (include: directive)
docker buildx version                              # Must be available for bake

# --- Full quality gate (existing) ---
uv run mde-py quality                              # 6/6

# --- Memory stack lifecycle ---
uv run mde-py memory up                            # Start Honcho stack
uv run mde-py memory status                        # Show container status
uv run mde-py memory verify                        # Health check: API + PG + Redis
uv run mde-py memory down                          # Stop Honcho stack

# --- Docker infrastructure validation ---
uv run mde-py validate --docker                    # Compose structure + bake + digests + version

# --- Observability (updated path) ---
uv run mde-py observability up                     # Uses new compose.yaml path

# --- End-to-end: both stacks ---
docker compose -f docker/compose.yaml up -d --wait # Start everything via root compose
docker compose -f docker/compose.yaml ps           # Verify all healthy
docker compose -f docker/compose.yaml down          # Tear down everything

# --- Bake verification ---
docker buildx bake -f docker/docker-bake.hcl --print  # Validate HCL syntax, show resolved config

# --- Regression: no legacy files ---
# This should return empty:
find docker/ -name 'docker-compose.yml' -o -name 'docker-compose.yaml'
```

## Breaking Changes

| What | Old | New | Impact |
|------|-----|-----|--------|
| Compose filename | `docker-compose.yml` | `compose.yaml` | Modern Docker convention |
| Observability path | `docker/observability/docker-compose.yml` | `docker/observability/compose.yaml` | Python code + tests updated |
| Entry point | `docker compose -f docker/observability/docker-compose.yml` | `docker compose -f docker/compose.yaml` | CLI, mise tasks, docs |
| Compose constant | `COMPOSE_FILE` in `observability_stack.py` | Shared constant in `docker_stacks.py` | Test assertions updated |
| Compose version | Any | v2.20+ required | `include:` directive unavailable in older versions |
| Mise tasks | May reference old compose path | Must use new path | Check `.mise.toml` for docker commands |
| Grafana port | `3000` (observability) | `3000` (observability only) | Honcho's own Grafana is NOT included (we already have one) |

## CLI Dispatch Changes

The `memory` subcommand follows the same pattern as `observability`:

```python
# In cli.py — add to _build_parser():
memory_p = sub.add_parser("memory", help="Honcho memory stack management")
memory_sub = memory_p.add_subparsers(dest="memory_action")
memory_sub.add_parser("up", help="Start the memory stack")
memory_sub.add_parser("down", help="Stop the memory stack")
memory_sub.add_parser("status", help="Show stack container status")
memory_sub.add_parser("verify", help="Health check all memory services")

# In cli.py — add to _DISPATCH_TABLE:
"memory": _cmd_memory,

# src/mde/domain/docker_stacks.py — shared constants:
DOCKER_DIR = Path(__file__).resolve().parents[3] / "docker"
ROOT_COMPOSE = DOCKER_DIR / "compose.yaml"
OBSERVABILITY_COMPOSE = DOCKER_DIR / "observability" / "compose.yaml"
MEMORY_COMPOSE = DOCKER_DIR / "memory" / "compose.yaml"

# src/mde/domain/memory_stack.py — same pattern as observability_stack.py:
# stack_up() validates HONCHO_DB_PASSWORD, calls docker compose up
# stack_down() calls docker compose down
# stack_status() calls docker compose ps
# stack_verify() checks Honcho API /openapi.json, pg_isready, redis-cli ping

# src/mde/validate/docker.py — expanded checks:
# _check_compose_version() — `docker compose version --short` >= 2.20.0
# _check_compose_structure() — ROOT_COMPOSE exists and includes sub-stacks
# _check_bake_syntax() — `docker buildx bake --print` exits 0
# _check_legacy_compose_files() — no docker-compose.yml files remain
# _check_digest_pinning() — parse compose files, verify @sha256: on all images
```

## Plugin Installation

```bash
# Step 1: Register the Honcho plugin marketplace.
# This tells Claude Code where to find Honcho plugins.
# The marketplace repo is plastic-labs/claude-honcho on GitHub.
/plugin marketplace add plastic-labs/claude-honcho

# Step 2: Install the "honcho" plugin from that marketplace.
# The format is <plugin-name>@<marketplace-name>.
# This installs hooks, MCP server, and skills into Claude Code.
/plugin install honcho@honcho

# Step 3: Restart Claude Code for the plugin to take effect.
# You should see the Honcho pixel art on startup.

# Step 4: Configure for self-hosted.
# The /honcho:setup skill creates ~/.honcho/config.json interactively.
/honcho:setup
# Or configure manually for local endpoint:
# mkdir -p ~/.honcho && echo '{"apiKey":"local","endpoint":{"environment":"local"}}' > ~/.honcho/config.json
```

## Environment Variables

```bash
# --- Required for memory stack (Docker services) ---
HONCHO_DB_PASSWORD          # PostgreSQL password for Honcho (fnox-managed)

# --- Required for Honcho deriver (LLM reasoning pipeline) ---
# These use Honcho's LLM_ prefix, NOT the standard provider key names.
# The deriver calls multiple LLM providers for reasoning and embeddings.
LLM_OPENAI_API_KEY          # REQUIRED: OpenAI key for text-embedding-3-small (embeddings)
LLM_ANTHROPIC_API_KEY       # Claude for dialectic reasoning
LLM_GEMINI_API_KEY          # Gemini for deriver fallback reasoning
LLM_GROQ_API_KEY            # Groq for fast inference fallback

# --- Required for observability stack (existing) ---
GRAFANA_PASSWORD            # Grafana admin password (fnox-managed)

# --- Optional: Honcho server security ---
# Auth is disabled by default for local use (AUTH_USE_AUTH=false in compose).
# Enable if exposing the API beyond localhost.
AUTH_USE_AUTH                # Set to "true" to enable JWT auth
AUTH_JWT_SECRET              # Required when AUTH_USE_AUTH=true

# --- Optional: claude-honcho plugin config ---
# These configure the plugin, not the server. Set in shell env or ~/.honcho/config.json.
HONCHO_API_KEY              # Set to any value for local (no auth enforcement)
HONCHO_PEER_NAME            # Defaults to $USER
HONCHO_WORKSPACE            # Defaults to "claude_code"
```

## Reproducibility Checklist

<!-- For AI agents: run through this checklist after any change to the Docker
     infrastructure. Every item must pass before merging. -->

### Prerequisites
- [ ] `docker compose version --short` >= 2.20.0 (required for `include:` directive)
- [ ] `docker buildx version` available (required for bake)
- [ ] `bun --version` available (required for claude-honcho plugin hooks)

### Build & Config
- [ ] `docker buildx bake -f docker/docker-bake.hcl --print` exits 0
- [ ] `docker compose -f docker/compose.yaml config` exits 0 (validates YAML)
- [ ] All images in compose files have `@sha256:` digest pinning
- [ ] Every service has a healthcheck with interval, timeout, retries, start_period
- [ ] All `${VAR:?msg}` vars listed in `docker/.env.example` with descriptions
- [ ] All LLM keys use `LLM_` prefix (not bare `ANTHROPIC_API_KEY`)

### Security
- [ ] Port bindings use `127.0.0.1:` prefix (no wildcard binding)
- [ ] Containers use `security_opt: [no-new-privileges:true]`, `cap_drop: [ALL]`
- [ ] `read_only: true` on all containers with appropriate `tmpfs` mounts
- [ ] No `POSTGRES_HOST_AUTH_METHOD=trust` (password auth enforced)
- [ ] `docker/memory/.env` is in `.gitignore` (contains LLM API keys)
- [ ] `docker/.env` is in `.gitignore` if it exists
- [ ] All Honcho images pinned by `@sha256:` digest (supply chain protection)

### Runtime
- [ ] `uv run mde-py memory up` starts all 4 memory services
- [ ] `uv run mde-py memory verify` passes (API + PG + Redis health checks)
- [ ] `uv run mde-py memory down` cleanly stops all services
- [ ] `uv run mde-py observability up` still works with renamed compose path
- [ ] No port conflicts between memory and observability stacks

### Quality
- [ ] `uv run mde-py validate --docker` passes (compose structure + bake + digests + version)
- [ ] `uv run mde-py quality` passes 6/6
- [ ] Tests updated: compose file path assertions match new naming
- [ ] No legacy `docker-compose.yml` files remain in the repo
- [ ] Mise tasks updated if they reference old compose paths

## Operational Procedures

### Backup & Recovery

<!-- ADVERSARIAL FINDING: `docker compose down -v` deletes all volumes including
     honcho-pgdata. No backup = permanent data loss of all session memory. -->

```bash
# Backup Honcho database (run periodically or before destructive operations)
docker compose -f docker/compose.yaml exec honcho-db \
  pg_dump -U honcho honcho | gzip > backups/honcho-$(date +%Y%m%d).sql.gz

# Restore from backup
gunzip -c backups/honcho-YYYYMMDD.sql.gz | \
  docker compose -f docker/compose.yaml exec -T honcho-db psql -U honcho honcho
```

### Secret Rotation

```bash
# 1. Update HONCHO_DB_PASSWORD in fnox/keychain
# 2. Update the running PostgreSQL password:
docker compose -f docker/compose.yaml exec honcho-db \
  psql -U honcho -c "ALTER USER honcho PASSWORD 'new-password';"
# 3. Restart API and deriver to pick up new password:
docker compose -f docker/compose.yaml restart honcho-api honcho-deriver
```

### Known Limitations

<!-- For AI agents: these are acknowledged trade-offs, not bugs to fix. -->

1. **Plaintext secrets in `docker inspect`**: Container environment variables are visible
   via `docker inspect`. Mitigated by fnox-managed secrets and localhost-only access.
   Docker Secrets (Swarm-only) would fix this but adds Swarm dependency we don't need.

2. **No network-level isolation between stacks**: Sub-stacks share the Docker daemon.
   A compromised container could theoretically reach other stacks via Docker networking.
   Mitigated by `cap_drop: ALL`, `read_only: true`, and `no-new-privileges`.

3. **Migration re-runs on restart**: `provision_db.py` runs Alembic migrations on every
   container start. Alembic is idempotent — re-running already-applied migrations is a
   no-op. The tmpfs mount for `/app/alembic` is for migration stamp files only.

## Gitignore Requirements

```gitignore
# Docker environment files (contain LLM API keys and passwords)
docker/.env
docker/memory/.env
docker/observability/.env
```
