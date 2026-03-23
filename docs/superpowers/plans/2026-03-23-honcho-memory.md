# Honcho Persistent Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add self-hosted Honcho memory stack with Docker Bake/Compose infrastructure, mde CLI lifecycle management, and official claude-honcho plugin integration.

**Architecture:** Root Compose with `include:` pulls in modular sub-stacks (observability, memory). Bake HCL defines buildable targets only. The official claude-honcho plugin handles all memory read/write via hooks and MCP server. The mde package owns Docker lifecycle and validation.

**Tech Stack:** Docker Compose v2.20+ (include directive), Docker Buildx Bake (HCL), PostgreSQL 15 + pgvector, Redis 8.2, Honcho v3.0.3, claude-honcho plugin (TypeScript/Bun), Python (mde library)

**Spec:** `docs/superpowers/specs/2026-03-23-honcho-memory-design.md`

---

### Task 1: Rename observability Compose file and create shared constants

**Files:**
- Rename: `docker/observability/docker-compose.yml` → `docker/observability/compose.yaml`
- Create: `src/mde/domain/docker_stacks.py`
- Modify: `src/mde/domain/observability_stack.py`
- Modify: `tests/mde/test_observability_stack.py`
- Test: `tests/mde/test_docker_stacks.py`

**Why first:** Everything else depends on the new path constants and the renamed file.

- [ ] **Step 1: Write test for shared path constants**

```python
# tests/mde/test_docker_stacks.py
"""Tests for shared Docker stack path constants."""

from __future__ import annotations

from mde.domain.docker_stacks import (
    DOCKER_DIR,
    MEMORY_COMPOSE,
    OBSERVABILITY_COMPOSE,
    ROOT_COMPOSE,
)


class TestPathConstants:
    """Verify Docker path constants resolve correctly."""

    def test_docker_dir_exists(self) -> None:
        assert DOCKER_DIR.is_dir()

    def test_observability_compose_path(self) -> None:
        assert OBSERVABILITY_COMPOSE.name == "compose.yaml"
        assert "docker/observability" in str(OBSERVABILITY_COMPOSE)

    def test_memory_compose_path(self) -> None:
        assert MEMORY_COMPOSE.name == "compose.yaml"
        assert "docker/memory" in str(MEMORY_COMPOSE)

    def test_root_compose_path(self) -> None:
        assert ROOT_COMPOSE.name == "compose.yaml"
        assert ROOT_COMPOSE.parent == DOCKER_DIR
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/mde/test_docker_stacks.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'mde.domain.docker_stacks'"

- [ ] **Step 3: Create docker_stacks.py with shared constants**

```python
# src/mde/domain/docker_stacks.py
"""Shared Docker stack path constants and helpers.

All Docker infrastructure paths are defined here. Modules like
observability_stack.py and memory_stack.py import from this module
to avoid duplicating path logic.

HISTORY: Created in PR B (2026-03-23) to consolidate paths when
the project moved from single-stack to multi-stack Docker architecture
with root Compose + include directive.
"""

from __future__ import annotations

from pathlib import Path

# All Docker infrastructure lives under docker/ in the project root.
# Path resolution: this file → src/mde/domain/ → src/mde/ → src/ → project root
DOCKER_DIR = Path(__file__).resolve().parents[3] / "docker"

# Root compose.yaml — single entry point that includes sub-stacks.
# Uses Compose v2.20+ `include:` directive.
ROOT_COMPOSE = DOCKER_DIR / "compose.yaml"

# Sub-stack compose files — each is self-contained with its own
# services, volumes, and configs.
OBSERVABILITY_COMPOSE = DOCKER_DIR / "observability" / "compose.yaml"
MEMORY_COMPOSE = DOCKER_DIR / "memory" / "compose.yaml"
```

- [ ] **Step 4: Rename the observability compose file**

```bash
git mv docker/observability/docker-compose.yml docker/observability/compose.yaml
```

- [ ] **Step 5: Update observability_stack.py to use shared constants**

Replace the `COMPOSE_FILE` constant in `src/mde/domain/observability_stack.py`:

```python
# Old:
# COMPOSE_FILE = (
#     Path(__file__).resolve().parents[3] / "docker" / "observability" / "docker-compose.yml"
# )

# New:
from mde.domain.docker_stacks import OBSERVABILITY_COMPOSE

COMPOSE_FILE = OBSERVABILITY_COMPOSE
```

- [ ] **Step 6: Update test assertions**

In `tests/mde/test_observability_stack.py`, update `TestComposeFile`:

```python
class TestComposeFile:
    """Test compose file path is correct."""

    def test_compose_file_path(self) -> None:
        assert COMPOSE_FILE.name == "compose.yaml"
        assert "docker/observability" in str(COMPOSE_FILE)
```

- [ ] **Step 7: Run all tests to verify nothing broke**

Run: `uv run pytest tests/mde/test_docker_stacks.py tests/mde/test_observability_stack.py -v`
Expected: ALL PASS

- [ ] **Step 8: Run quality gate**

Run: `uv run mde-py quality`
Expected: 6/6 passed

- [ ] **Step 9: Commit**

```bash
git add src/mde/domain/docker_stacks.py tests/mde/test_docker_stacks.py
git add docker/observability/compose.yaml src/mde/domain/observability_stack.py
git add tests/mde/test_observability_stack.py
git commit -m "refactor: rename docker-compose.yml to compose.yaml, add shared path constants"
```

---

### Task 2: Create root Compose file and Docker Bake HCL

**Files:**
- Create: `docker/compose.yaml`
- Create: `docker/docker-bake.hcl`
- Create: `docker/.env.example`

**Why:** Infrastructure files that other tasks depend on.

- [ ] **Step 1: Create root compose.yaml**

Copy the Root Compose File section from the spec verbatim (lines 466-500).

- [ ] **Step 2: Create docker-bake.hcl**

Copy the Docker Bake File section from the spec verbatim (lines 172-246).

- [ ] **Step 3: Create .env.example**

```bash
# docker/.env.example
#
# Copy to docker/.env and fill in values.
# This file documents ALL environment variables used by Docker stacks.
# NEVER commit docker/.env — it contains secrets.

# --- Memory stack (Honcho) ---
HONCHO_DB_PASSWORD=changeme

# --- Honcho deriver LLM keys ---
# These use Honcho's LLM_ prefix, NOT standard provider key names.
LLM_OPENAI_API_KEY=sk-...          # REQUIRED: embeddings (text-embedding-3-small)
LLM_ANTHROPIC_API_KEY=sk-ant-...   # Claude for dialectic reasoning
LLM_GEMINI_API_KEY=...             # Gemini fallback
LLM_GROQ_API_KEY=gsk_...           # Groq fallback

# --- Honcho server auth (optional) ---
# AUTH_USE_AUTH=true
# AUTH_JWT_SECRET=<random-secret>

# --- Observability stack ---
# GRAFANA_PASSWORD is loaded from fnox/keychain, not this file.
```

- [ ] **Step 4: Add docker env files to .gitignore**

Append to `.gitignore`:
```gitignore
# Docker environment files (contain LLM API keys and passwords)
docker/.env
docker/memory/.env
docker/observability/.env
```

- [ ] **Step 5: Verify compose config parses**

Run: `docker compose -f docker/compose.yaml config`
Expected: Merged YAML output showing both observability and memory stacks (memory will fail until Task 3)

Note: This may fail because `docker/memory/compose.yaml` doesn't exist yet. That's expected — just verify no syntax errors in the root file.

- [ ] **Step 6: Verify bake HCL parses**

Run: `docker buildx bake -f docker/docker-bake.hcl --print`
Expected: JSON output showing resolved targets (may warn about missing Dockerfile — that's expected since we're using upstream images)

- [ ] **Step 7: Commit**

```bash
git add docker/compose.yaml docker/docker-bake.hcl docker/.env.example .gitignore
git commit -m "feat: add root compose.yaml with include directive and docker-bake.hcl"
```

---

### Task 3: Create memory stack Compose and supporting files

**Files:**
- Create: `docker/memory/compose.yaml`
- Create: `docker/memory/init.sql`
- Create: `docker/memory/.env.example`

**Why:** The actual Honcho services need to be defined before we can write Python lifecycle code.

- [ ] **Step 1: Create the memory directory**

```bash
mkdir -p docker/memory
```

- [ ] **Step 2: Create init.sql**

```sql
-- docker/memory/init.sql
-- PostgreSQL init script for Honcho.
-- Enables the pgvector extension required for vector similarity search.
-- This runs once when the database is first created.
CREATE EXTENSION IF NOT EXISTS vector;
```

- [ ] **Step 3: Create memory compose.yaml**

Copy the Memory Compose Stack section from the spec verbatim (lines 250-462).
Pin image digests by running:

```bash
docker pull ghcr.io/plastic-labs/honcho:v3.0.3 && docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/plastic-labs/honcho:v3.0.3
docker pull pgvector/pgvector:pg15-trixie && docker inspect --format='{{index .RepoDigests 0}}' pgvector/pgvector:pg15-trixie
docker pull redis:8.2 && docker inspect --format='{{index .RepoDigests 0}}' redis:8.2
```

Replace the TODO digest comments with actual `@sha256:` digests in the image references.

- [ ] **Step 4: Create memory .env.example**

```bash
# docker/memory/.env.example
#
# Copy to docker/memory/.env and fill in values.
# See docker/.env.example for the full variable reference.

HONCHO_DB_PASSWORD=changeme
LLM_OPENAI_API_KEY=sk-...
LLM_ANTHROPIC_API_KEY=sk-ant-...
LLM_GEMINI_API_KEY=...
LLM_GROQ_API_KEY=gsk_...
```

- [ ] **Step 5: Verify root compose now includes memory**

Run: `docker compose -f docker/compose.yaml config --services`
Expected: Lists all services from both observability AND memory stacks

- [ ] **Step 6: Commit**

```bash
git add docker/memory/
git commit -m "feat: add Honcho memory stack compose with PostgreSQL+pgvector and Redis"
```

---

### Task 4: Create memory_stack.py lifecycle module

**Files:**
- Create: `src/mde/domain/memory_stack.py`
- Test: `tests/mde/test_memory_stack.py`

**Why:** Python lifecycle management (up/down/status/verify) following the observability_stack.py pattern.

- [ ] **Step 1: Write failing tests**

```python
# tests/mde/test_memory_stack.py
"""Tests for memory stack lifecycle management."""

from __future__ import annotations

import argparse
from unittest.mock import patch

from mde.domain.memory_stack import (
    dispatch,
    stack_down,
    stack_status,
    stack_up,
    stack_verify,
)


class TestStackUp:
    """Test stack_up validates HONCHO_DB_PASSWORD and starts compose."""

    def test_fails_without_db_password(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            result = stack_up()
            assert result != 0

    def test_succeeds_with_db_password(self) -> None:
        with (
            patch.dict("os.environ", {"HONCHO_DB_PASSWORD": "test123"}),
            patch("mde.domain.memory_stack.MEMORY_COMPOSE") as mock_cf,
            patch("subprocess.run") as mock_run,
        ):
            mock_cf.is_file.return_value = True
            mock_cf.__str__ = lambda _self: "/fake/compose.yaml"
            mock_run.return_value.returncode = 0
            result = stack_up()
            assert result == 0


class TestStackDown:
    """Test stack_down calls docker compose down."""

    def test_calls_docker_compose_down(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = stack_down()
            assert result == 0
            call_args = mock_run.call_args[0][0]
            assert "down" in call_args


class TestStackStatus:
    """Test stack_status calls docker compose ps."""

    def test_calls_docker_compose_ps(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = stack_status()
            assert result == 0


class TestStackVerify:
    """Test stack_verify checks service health."""

    def test_verify_reports_results(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "healthy"
            result = stack_verify()
            assert result == 0


class TestDispatch:
    """Test dispatch routes to correct handler."""

    def test_dispatch_up(self) -> None:
        args = argparse.Namespace(memory_action="up")
        with patch("mde.domain.memory_stack._ACTION_TABLE", {"up": lambda: 0}):
            assert dispatch(args) == 0

    def test_dispatch_unknown_returns_1(self) -> None:
        args = argparse.Namespace(memory_action=None)
        assert dispatch(args) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/mde/test_memory_stack.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement memory_stack.py**

Follow the exact pattern from `observability_stack.py` but for the memory stack. Key differences:
- Validates `HONCHO_DB_PASSWORD` instead of `GRAFANA_PASSWORD`
- Uses `MEMORY_COMPOSE` from `docker_stacks.py`
- Adds `stack_verify()` that checks HTTP, PG, and Redis health
- Uses `add_subparsers` pattern for CLI registration
- Dict-dispatch for subcommand routing

```python
# src/mde/domain/memory_stack.py
"""Honcho memory stack lifecycle management.

Manages the Docker Compose Honcho stack (API + deriver + PostgreSQL + Redis).

HISTORY: Added in PR B (2026-03-23). Follows the same pattern as
observability_stack.py — validates env vars, calls docker compose.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import TYPE_CHECKING

from mde.domain.docker_stacks import MEMORY_COMPOSE

if TYPE_CHECKING:
    from collections.abc import Callable


def stack_up() -> int:
    """Start the Honcho memory stack."""
    import subprocess

    password = os.environ.get("HONCHO_DB_PASSWORD", "")
    if not password:
        print(
            "ERROR: HONCHO_DB_PASSWORD not set. "
            "Add it to macOS Keychain: "
            "security add-generic-password -s HONCHO_DB_PASSWORD -a mde -w '<password>'",
            file=sys.stderr,
        )
        return 1

    if not MEMORY_COMPOSE.is_file():
        print(f"ERROR: Compose file not found: {MEMORY_COMPOSE}", file=sys.stderr)
        return 1

    result = subprocess.run(
        ["docker", "compose", "-f", str(MEMORY_COMPOSE), "up", "-d", "--wait"],
        timeout=120,
    )
    return result.returncode


def stack_down() -> int:
    """Stop the Honcho memory stack."""
    import subprocess

    result = subprocess.run(
        ["docker", "compose", "-f", str(MEMORY_COMPOSE), "down"],
        timeout=60,
    )
    return result.returncode


def stack_status() -> int:
    """Show Honcho stack container status."""
    import subprocess

    result = subprocess.run(
        ["docker", "compose", "-f", str(MEMORY_COMPOSE), "ps", "--format", "table"],
        timeout=10,
    )
    return result.returncode


def stack_verify() -> int:
    """Verify all Honcho stack services are healthy."""
    import subprocess

    checks = {
        "honcho-api": [
            "docker", "compose", "-f", str(MEMORY_COMPOSE),
            "exec", "-T", "honcho-api",
            "python", "-c",
            "import urllib.request; urllib.request.urlopen('http://localhost:8000/openapi.json')",
        ],
        "honcho-db": [
            "docker", "compose", "-f", str(MEMORY_COMPOSE),
            "exec", "-T", "honcho-db",
            "pg_isready", "-U", "honcho", "-d", "honcho",
        ],
        "honcho-redis": [
            "docker", "compose", "-f", str(MEMORY_COMPOSE),
            "exec", "-T", "honcho-redis",
            "redis-cli", "ping",
        ],
    }
    failed = 0
    for name, cmd in checks.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  {name}: healthy")
            else:
                print(f"  {name}: UNHEALTHY", file=sys.stderr)
                failed += 1
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"  {name}: UNREACHABLE", file=sys.stderr)
            failed += 1
    return 1 if failed else 0


def add_subparsers(sub: argparse._SubParsersAction) -> None:
    """Register the 'memory' subcommand and its children."""
    mem_p = sub.add_parser("memory", help="Honcho memory stack management")
    mem_sub = mem_p.add_subparsers(dest="memory_action")
    mem_sub.add_parser("up", help="Start the memory stack")
    mem_sub.add_parser("down", help="Stop the memory stack")
    mem_sub.add_parser("status", help="Show stack container status")
    mem_sub.add_parser("verify", help="Health check all memory services")


_ACTION_TABLE: dict[str, Callable[[], int]] = {
    "up": stack_up,
    "down": stack_down,
    "status": stack_status,
    "verify": stack_verify,
}


def dispatch(args: argparse.Namespace) -> int:
    """Route to the correct memory subcommand handler."""
    action = getattr(args, "memory_action", None)
    handler = _ACTION_TABLE.get(action)  # type: ignore[arg-type]
    if handler is None:
        print("Usage: mde-py memory {up,down,status,verify}", file=sys.stderr)
        return 1
    return handler()
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/mde/test_memory_stack.py -v`
Expected: ALL PASS

- [ ] **Step 5: Run quality gate**

Run: `uv run mde-py quality`
Expected: 6/6

- [ ] **Step 6: Commit**

```bash
git add src/mde/domain/memory_stack.py tests/mde/test_memory_stack.py
git commit -m "feat: add memory stack lifecycle management (up/down/status/verify)"
```

---

### Task 5: Wire memory subcommand into CLI

**Files:**
- Modify: `src/mde/cli.py`
- Test: `tests/mde/test_cli_memory.py`

- [ ] **Step 1: Write failing test**

```python
# tests/mde/test_cli_memory.py
"""Tests for memory CLI subcommand wiring."""

from __future__ import annotations

from unittest.mock import patch

from mde.cli import run


class TestMemoryCLI:
    """Test memory subcommand is wired in CLI."""

    def test_memory_up_dispatches(self) -> None:
        with patch("mde.domain.memory_stack.stack_up", return_value=0) as mock:
            result = run(["memory", "up"])
            mock.assert_called_once()
            assert result == 0

    def test_memory_no_action_shows_help(self) -> None:
        result = run(["memory"])
        assert result == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/mde/test_cli_memory.py -v`
Expected: FAIL

- [ ] **Step 3: Add memory to cli.py**

In `_build_parser()`, add after the observability import:

```python
from mde.domain.memory_stack import add_subparsers as _add_memory_subparsers
_add_memory_subparsers(sub)
```

Add `_cmd_memory` function and add to `_DISPATCH_TABLE`:

```python
def _cmd_memory(args: argparse.Namespace) -> int:
    action = getattr(args, "memory_action", None)
    with _traced_command("memory", action=action) as ctx:
        ctx["span"].set_attribute("memory.action", str(action))
        from mde.domain.memory_stack import dispatch as mem_dispatch
        result = mem_dispatch(args)
        ctx["result"] = result
        return result

# In _DISPATCH_TABLE:
"memory": _cmd_memory,
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/mde/test_cli_memory.py tests/mde/test_memory_stack.py -v`
Expected: ALL PASS

- [ ] **Step 5: Run quality gate**

Run: `uv run mde-py quality`
Expected: 6/6

- [ ] **Step 6: Commit**

```bash
git add src/mde/cli.py tests/mde/test_cli_memory.py
git commit -m "feat: wire memory subcommand into mde CLI"
```

---

### Task 6: Add mise tasks for memory stack

**Files:**
- Modify: `.mise.toml`

- [ ] **Step 1: Add memory tasks to .mise.toml**

Add after the existing `mde:observability:*` tasks:

```toml
[tasks."mde:memory:up"]
description = "Start Honcho memory stack (API + PostgreSQL + Redis + deriver)"
run = "uv run mde-py memory up"

[tasks."mde:memory:down"]
description = "Stop Honcho memory stack"
run = "uv run mde-py memory down"

[tasks."mde:memory:status"]
description = "Show Honcho memory stack status"
run = "uv run mde-py memory status"

[tasks."mde:memory:verify"]
description = "Health check all Honcho memory services"
run = "uv run mde-py memory verify"
```

- [ ] **Step 2: Verify tasks are visible**

Run: `mise tasks | grep memory`
Expected: Shows all 4 memory tasks

- [ ] **Step 3: Commit**

```bash
git add .mise.toml
git commit -m "feat: add mise tasks for memory stack lifecycle"
```

---

### Task 7: Expand Docker validation

**Files:**
- Modify: `src/mde/validate/docker.py`
- Test: `tests/mde/test_validate_docker.py`

- [ ] **Step 1: Write failing tests for new validation checks**

```python
# tests/mde/test_validate_docker.py
"""Tests for expanded Docker validation."""

from __future__ import annotations

from unittest.mock import patch

from mde.validate.docker import validate_docker


class TestDockerValidation:
    """Test Docker validation checks."""

    def test_checks_compose_version(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "2.32.0\n"
            result = validate_docker()
            assert result.total_errors == 0

    def test_warns_on_old_compose_version(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "2.19.0\n"
            result = validate_docker()
            # Should have a warning about compose version
            assert any("2.20" in str(f) for f in result.findings)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/mde/test_validate_docker.py -v`

- [ ] **Step 3: Expand validate/docker.py**

Add these checks to `validate_docker()`:
- `_check_compose_version()` — parse `docker compose version --short`, warn if < 2.20.0
- `_check_compose_structure()` — verify `docker/compose.yaml` exists
- `_check_legacy_compose_files()` — warn if any `docker-compose.yml` files exist under `docker/`

```python
def _check_compose_version(result: ValidationResult) -> None:
    """Verify Docker Compose version supports include directive (v2.20+)."""
    try:
        proc = subprocess.run(
            ["docker", "compose", "version", "--short"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        result.files_checked += 1
        if proc.returncode == 0:
            version_str = proc.stdout.strip().lstrip("v")
            parts = version_str.split(".")
            if len(parts) >= 2:
                major, minor = int(parts[0]), int(parts[1])
                if major < 2 or (major == 2 and minor < 20):
                    result.add_warning(
                        "docker",
                        f"Docker Compose {version_str} < 2.20.0 — include: directive unavailable",
                        rule="docker.compose-version",
                    )
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass


def _check_compose_structure(result: ValidationResult) -> None:
    """Verify root compose.yaml exists."""
    from mde.domain.docker_stacks import ROOT_COMPOSE

    result.files_checked += 1
    if not ROOT_COMPOSE.is_file():
        result.add_warning(
            str(ROOT_COMPOSE),
            "Root compose.yaml not found — docker infrastructure incomplete",
            rule="docker.root-compose-missing",
        )


def _check_legacy_compose_files(result: ValidationResult) -> None:
    """Warn if legacy docker-compose.yml files remain."""
    from mde.domain.docker_stacks import DOCKER_DIR

    for path in DOCKER_DIR.rglob("docker-compose.yml"):
        result.add_warning(
            str(path),
            "Legacy docker-compose.yml found — rename to compose.yaml",
            rule="docker.legacy-compose-file",
        )
    for path in DOCKER_DIR.rglob("docker-compose.yaml"):
        result.add_warning(
            str(path),
            "Legacy docker-compose.yaml found — rename to compose.yaml",
            rule="docker.legacy-compose-file",
        )
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/mde/test_validate_docker.py -v`
Expected: ALL PASS

- [ ] **Step 5: Run quality gate**

Run: `uv run mde-py quality`
Expected: 6/6

- [ ] **Step 6: Commit**

```bash
git add src/mde/validate/docker.py tests/mde/test_validate_docker.py
git commit -m "feat: expand Docker validation (compose version, structure, legacy files)"
```

---

### Task 8: Install and configure claude-honcho plugin

**Files:**
- Create: `~/.honcho/config.json` (user config, not in repo)
- Modify: `.claude/settings.json` (add plugin enablement)

**Why last:** Plugin installation is a manual step that depends on the Docker stack being functional.

- [ ] **Step 1: Install the plugin marketplace**

Run in Claude Code: `/plugin marketplace add plastic-labs/claude-honcho`

- [ ] **Step 2: Install the honcho plugin**

Run in Claude Code: `/plugin install honcho@honcho`

- [ ] **Step 3: Configure for self-hosted**

Run in Claude Code: `/honcho:setup`

Or manually:
```bash
mkdir -p ~/.honcho
cat > ~/.honcho/config.json << 'EOF'
{
  "apiKey": "local",
  "peerName": "rmanaloto",
  "endpoint": {
    "environment": "local"
  },
  "sessionStrategy": "git-branch",
  "saveMessages": true,
  "enabled": true,
  "logging": true
}
EOF
```

- [ ] **Step 4: Verify plugin loads on restart**

Restart Claude Code. Expected: Honcho pixel art banner and "Loading memory..." on startup.

- [ ] **Step 5: Run end-to-end verification**

```bash
# Start memory stack
uv run mde-py memory up

# Verify all services healthy
uv run mde-py memory verify

# Verify plugin can connect (check Claude Code logs)
# The SessionStart hook should print memory context

# Full quality gate
uv run mde-py quality
```

- [ ] **Step 6: Commit settings changes**

```bash
git add .claude/settings.json
git commit -m "feat: enable claude-honcho plugin for persistent memory"
```

---

### Task 9: Final verification and reproducibility

**Files:** None (verification only)

- [ ] **Step 1: Run the full reproducibility checklist**

Work through every item in the spec's Reproducibility Checklist section:

```bash
# Prerequisites
docker compose version --short        # >= 2.20.0
docker buildx version                 # available
bun --version                         # available

# Build & Config
docker buildx bake -f docker/docker-bake.hcl --print
docker compose -f docker/compose.yaml config > /dev/null

# Runtime
uv run mde-py memory up
uv run mde-py memory verify
uv run mde-py memory down
uv run mde-py observability up
uv run mde-py observability down

# Quality
uv run mde-py validate --docker
uv run mde-py quality

# Regression
find docker/ -name 'docker-compose.yml' -o -name 'docker-compose.yaml'
# Should return empty
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS (300+ tests)

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address verification findings"
```
