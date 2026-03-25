# Honcho SDK Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the honcho-ai Python SDK as a library dependency with schema-driven config, client factory, and SDK health check in `memory verify`.

**Architecture:** JSON Schema → datamodel-codegen → Pydantic model for config. Thin client factory in `src/mde/domain/honcho.py` with `get_client()` and `test_connection()`. SDK connectivity check added to existing `memory verify` command. New `generated/` directory at project root for intermediate codegen artifacts.

**Tech Stack:** honcho-ai 2.0.1 (SDK), datamodel-codegen (codegen), pydantic v2 (models), pytest (tests), ruff/ty (quality)

**Spec:** `docs/superpowers/specs/2026-03-23-honcho-sdk-integration-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `docs/schemas/honcho-client.schema.json` | Create | JSON Schema for HonchoClientConfig |
| `generated/` | Create dir | Intermediate codegen artifacts (gitignored) |
| `src/mde/domain/honcho_models.py` | Create (codegen) | Generated Pydantic config model (committed) |
| `src/mde/domain/honcho.py` | Create | Client factory: get_config, get_client, test_connection |
| `tests/test_honcho_integration.py` | Create | Unit tests for config, client, connection |
| `src/mde/domain/memory_stack.py` | Modify | Add SDK health check to stack_verify() |
| `.gitignore` | Modify | Add `generated/` |
| `pyproject.toml` | Modify | Add dep, per-file-ignores, ruff/ty/pyright excludes |
| `.mise.toml` | Modify | Add codegen tasks |

---

### Task 1: Infrastructure — dependency, gitignore, excludes

**Files:**
- Modify: `pyproject.toml`
- Modify: `.gitignore`
- Create: `generated/` (directory — created by codegen task's `mkdir -p`)

- [ ] **Step 1: Add `honcho-ai` dependency and tighten `httpx`**

In `pyproject.toml`, add `honcho-ai` to dependencies and bump httpx:

```toml
dependencies = [
    "pydantic>=2.10",
    "pyyaml>=6.0",
    "tomli>=2.0; python_version < '3.11'",
    "claude-agent-sdk>=0.1.49",
    "httpx>=0.28",
    "claude-code-analytics>=0.1.1",
    "openlit>=1.38.1",
    "loguru>=0.7.3",
    "orjson>=3.11.7",
    "honcho-ai>=2.0.0,<3.0.0",
]
```

Changes: `httpx>=0.27` → `httpx>=0.28`, add `honcho-ai>=2.0.0,<3.0.0`.

- [ ] **Step 2: Add per-file-ignores for generated model**

In `pyproject.toml` `[tool.ruff.lint.per-file-ignores]`, add after the existing `"src/mde/hooks/agent_frontmatter_model.py"` block:

```toml
"src/mde/domain/honcho_models.py" = [
    "D100",     # generated file — no module docstring
    "D101",     # generated file — no class docstrings
    "ERA001",   # generated file — codegen header comments
    "E501",     # generated file — long descriptions from schema
    "COM812",   # generated file — trailing comma style
]
```

- [ ] **Step 3: Add `generated` to ruff, ty, pyright excludes**

In `pyproject.toml`:

Ruff — change `extend-exclude`:
```toml
extend-exclude = [".agents/skills", "generated"]
```

ty — change `[tool.ty.src] exclude`:
```toml
exclude = [".agents/skills", "src/mde/hooks/agent_frontmatter_model.py", "generated", "src/mde/domain/honcho_models.py"]
```

pyright — change `[tool.pyright] exclude`:
```toml
exclude = [
    "src/mde/hooks/agent_frontmatter_model.py",
    "generated",
    "src/mde/domain/honcho_models.py",
]
```

- [ ] **Step 4: Add `generated/` to `.gitignore`**

Append to `.gitignore`:

```
# Generated codegen artifacts (intermediate — copy targets are committed)
generated/
```

- [ ] **Step 5: Run `uv sync` to install honcho-ai**

Run: `uv sync`
Expected: Resolves and installs `honcho-ai==2.0.1` + dependencies.

- [ ] **Step 6: Verify import works**

Run: `uv run ruff --version && uv run pytest --co -q 2>&1 | head -5`
Expected: Tools resolve successfully (confirms honcho-ai is importable by the project).

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore uv.lock
git commit -m "feat: add honcho-ai SDK dependency and generated/ infra"
```

---

### Task 2: JSON Schema and codegen pipeline

**Files:**
- Create: `docs/schemas/honcho-client.schema.json`
- Modify: `.mise.toml`
- Create (codegen): `generated/honcho_models.py` → `src/mde/domain/honcho_models.py`

- [ ] **Step 1: Create the JSON Schema**

Create `docs/schemas/honcho-client.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "HonchoClientConfig",
  "description": "Configuration for connecting to a Honcho API server.",
  "type": "object",
  "properties": {
    "base_url": {
      "type": "string",
      "default": "http://localhost:8000",
      "description": "Honcho API server URL."
    },
    "workspace_id": {
      "type": "string",
      "default": "mde",
      "description": "Workspace ID for scoping all operations."
    },
    "api_key": {
      "type": ["string", "null"],
      "default": null,
      "description": "API key. Null for no-auth (AUTH_USE_AUTH=false)."
    },
    "timeout": {
      "type": "number",
      "default": 10,
      "exclusiveMinimum": 0,
      "description": "Request timeout in seconds. Must be positive."
    },
    "max_retries": {
      "type": "integer",
      "default": 0,
      "minimum": 0,
      "description": "Max retry attempts. 0 for fail-fast."
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 2: Add codegen mise tasks**

In `.mise.toml`, add after the `mde:codegen:skillsmp` task (around line 240):

```toml
[tasks."mde:codegen:honcho"]
description = "Generate Honcho config model from JSON Schema"
run = """
mkdir -p generated && \
uv run datamodel-codegen \
  --input docs/schemas/honcho-client.schema.json \
  --input-file-type jsonschema \
  --output generated/honcho_models.py \
  --output-model-type pydantic_v2.BaseModel \
  --target-python-version 3.12 \
  --use-annotated \
  --use-union-operator \
  --field-constraints \
  --use-default-kwarg \
  --collapse-root-models \
  --strict-nullable \
  --use-one-literal-as-default \
  --formatters ruff-format ruff-check && \
cp generated/honcho_models.py src/mde/domain/honcho_models.py
"""

[tasks."mde:codegen:all"]
description = "Run all codegen tasks"
depends = ["mde:codegen:statusline", "mde:codegen:skillsmp", "mde:codegen:honcho"]
```

- [ ] **Step 3: Run codegen**

Run: `mise run mde:codegen:honcho`
Expected: Creates `generated/honcho_models.py` and copies to `src/mde/domain/honcho_models.py`.

- [ ] **Step 4: Verify generated model imports cleanly**

Run: `uv run ruff check src/mde/domain/honcho_models.py`
Expected: No errors (per-file-ignores suppress codegen noise).

Verification of defaults and constraints is covered by tests in Task 3/4.

- [ ] **Step 6: Commit**

```bash
git add docs/schemas/honcho-client.schema.json .mise.toml src/mde/domain/honcho_models.py
git commit -m "feat: add Honcho client config schema and codegen pipeline"
```

---

### Task 3: Client factory module — tests first (TDD)

**Files:**
- Create: `tests/test_honcho_integration.py`
- Create: `src/mde/domain/honcho.py`

- [ ] **Step 1: Write failing tests for `get_config()`**

Create `tests/test_honcho_integration.py`:

```python
"""Tests for the Honcho SDK client factory."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from mde.domain.honcho_models import HonchoClientConfig


class TestGetConfig:
    """Tests for get_config() env var handling."""

    def test_defaults_without_env_vars(self) -> None:
        from mde.domain.honcho import get_config

        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
        assert config.base_url == "http://localhost:8000"
        assert config.workspace_id == "mde"
        assert config.api_key is None
        assert config.timeout == 10
        assert config.max_retries == 0

    def test_reads_env_vars(self) -> None:
        from mde.domain.honcho import get_config

        env = {
            "HONCHO_BASE_URL": "http://custom:9000",
            "HONCHO_WORKSPACE_ID": "test-ws",
            "HONCHO_API_KEY": "secret-key",
            "HONCHO_TIMEOUT": "30",
            "HONCHO_MAX_RETRIES": "3",
        }
        with patch.dict("os.environ", env, clear=True):
            config = get_config()
        assert config.base_url == "http://custom:9000"
        assert config.workspace_id == "test-ws"
        assert config.api_key == "secret-key"
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_malformed_timeout_raises_valueerror(self) -> None:
        from mde.domain.honcho import get_config

        with patch.dict("os.environ", {"HONCHO_TIMEOUT": "abc"}, clear=True):
            with pytest.raises(ValueError, match="HONCHO_TIMEOUT must be a number"):
                get_config()

    def test_malformed_max_retries_raises_valueerror(self) -> None:
        from mde.domain.honcho import get_config

        with patch.dict("os.environ", {"HONCHO_MAX_RETRIES": "xyz"}, clear=True):
            with pytest.raises(ValueError, match="HONCHO_MAX_RETRIES must be an integer"):
                get_config()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_honcho_integration.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mde.domain.honcho'`

- [ ] **Step 3: Write `get_config()` implementation**

Create `src/mde/domain/honcho.py` with the full module from the spec (component 3, lines 162-256). The complete file:

```python
"""Honcho SDK client factory.

Provides a pre-configured Honcho client reading connection
parameters from environment variables with schema-validated defaults.

Note: The Honcho server runs in API-only mode (EMBED_MESSAGES=false,
deriver disabled). Methods requiring LLM processing (chat, search,
representation) will return errors. CRUD operations work normally.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from honcho import Honcho

from mde.domain.honcho_models import HonchoClientConfig


def get_config() -> HonchoClientConfig:
    """Build config from env vars with schema defaults."""
    raw_timeout = os.environ.get("HONCHO_TIMEOUT", "10")
    raw_retries = os.environ.get("HONCHO_MAX_RETRIES", "0")
    try:
        timeout = float(raw_timeout)
    except ValueError:
        msg = f"HONCHO_TIMEOUT must be a number, got: {raw_timeout!r}"
        raise ValueError(msg) from None
    try:
        max_retries = int(raw_retries)
    except ValueError:
        msg = f"HONCHO_MAX_RETRIES must be an integer, got: {raw_retries!r}"
        raise ValueError(msg) from None
    return HonchoClientConfig(
        base_url=os.environ.get("HONCHO_BASE_URL", "http://localhost:8000"),
        workspace_id=os.environ.get("HONCHO_WORKSPACE_ID", "mde"),
        api_key=os.environ.get("HONCHO_API_KEY"),
        timeout=timeout,
        max_retries=max_retries,
    )


def get_client(config: HonchoClientConfig | None = None) -> Honcho:
    """Return a configured Honcho SDK client."""
    from honcho import Honcho as _Honcho

    if config is None:
        config = get_config()
    return _Honcho(
        api_key=config.api_key,
        base_url=config.base_url,
        workspace_id=config.workspace_id,
        timeout=config.timeout,
        max_retries=config.max_retries,
    )


def test_connection(config: HonchoClientConfig | None = None) -> tuple[bool, str]:
    """Test connectivity to the Honcho API.

    Returns (success, message) tuple. Uses the SDK's workspaces() list
    endpoint as a health probe (public API, no private method access).
    """
    try:
        from honcho import (  # noqa: PLC0415
            AuthenticationError,
            ConnectionError as HonchoConnectionError,
            NotFoundError,
            RateLimitError,
            ServerError,
            TimeoutError as HonchoTimeoutError,
        )
    except ImportError:
        return False, "honcho-ai SDK not installed"

    try:
        client = get_client(config)
        # Use public SDK method as health probe — list workspaces is a
        # lightweight read that validates connectivity, auth, and API version.
        client.workspaces()
    except HonchoConnectionError as e:
        return False, f"Connection failed: {e}"
    except HonchoTimeoutError:
        return False, f"Timeout after {(config or get_config()).timeout}s"
    except AuthenticationError:
        return False, "Auth required but no API key configured"
    except NotFoundError:
        return False, "Server does not support API v3"
    except RateLimitError:
        return False, "Rate limited — server is reachable but rejecting requests"
    except ServerError as e:
        return False, f"Server error: {e}"
    except Exception as e:  # noqa: BLE001
        return False, f"Unexpected error: {e}"
    else:
        return True, "Connected"
```

- [ ] **Step 4: Run `get_config()` tests to verify they pass**

Run: `uv run pytest tests/test_honcho_integration.py::TestGetConfig -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/mde/domain/honcho.py tests/test_honcho_integration.py
git commit -m "feat: add Honcho SDK client factory with get_config() tests"
```

---

### Task 4: Client factory tests — `get_client()` and `test_connection()`

**Files:**
- Modify: `tests/test_honcho_integration.py`

- [ ] **Step 1: Add `get_client()` tests**

Append to `tests/test_honcho_integration.py`:

```python
class TestGetClient:
    """Tests for get_client() SDK construction."""

    def test_passes_config_to_sdk(self) -> None:
        # patch("honcho.Honcho") works because get_client() does a lazy import
        # inside the function body. If this import moves to module level,
        # change the mock target to "mde.domain.honcho._Honcho".
        config = HonchoClientConfig(
            base_url="http://test:8000",
            workspace_id="test-ws",
            api_key="test-key",
            timeout=5.0,
            max_retries=2,
        )
        with patch("honcho.Honcho") as mock_cls:
            from mde.domain.honcho import get_client

            get_client(config)
            mock_cls.assert_called_once_with(
                api_key="test-key",
                base_url="http://test:8000",
                workspace_id="test-ws",
                timeout=5.0,
                max_retries=2,
            )

    def test_uses_default_config_when_none(self) -> None:
        with (
            patch("honcho.Honcho") as mock_cls,
            patch.dict("os.environ", {}, clear=True),
        ):
            from mde.domain.honcho import get_client

            get_client()
            mock_cls.assert_called_once_with(
                api_key=None,
                base_url="http://localhost:8000",
                workspace_id="mde",
                timeout=10.0,
                max_retries=0,
            )
```

- [ ] **Step 2: Run to verify pass**

Run: `uv run pytest tests/test_honcho_integration.py::TestGetClient -v`
Expected: 2 tests PASS

- [ ] **Step 3: Add `test_connection()` tests**

Append to `tests/test_honcho_integration.py`:

```python
class TestTestConnection:
    """Tests for test_connection() health probe."""

    def test_success(self) -> None:
        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.return_value = []
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is True
        assert msg == "Connected"

    def test_connection_error(self) -> None:
        from honcho import ConnectionError as HonchoConnectionError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = HonchoConnectionError("refused")
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Connection failed" in msg

    def test_timeout_error(self) -> None:
        from honcho import TimeoutError as HonchoTimeoutError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = HonchoTimeoutError()
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Timeout" in msg

    def test_auth_error(self) -> None:
        from honcho import AuthenticationError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = AuthenticationError()
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Auth required" in msg

    def test_not_found_error(self) -> None:
        from honcho import NotFoundError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = NotFoundError()
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "API v3" in msg

    def test_server_error(self) -> None:
        from honcho import ServerError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = ServerError("boom")
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Server error" in msg

    def test_rate_limit_error(self) -> None:
        from honcho import RateLimitError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = RateLimitError()
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Rate limited" in msg

    def test_unexpected_error(self) -> None:
        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = RuntimeError("surprise")
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Unexpected error" in msg


class TestTestConnectionImportError:
    """Test test_connection() when SDK is not installed."""

    def test_import_error_returns_false(self) -> None:
        import builtins

        real_import = builtins.__import__

        def mock_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "honcho":
                raise ImportError("No module named 'honcho'")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "not installed" in msg


class TestHonchoClientConfigValidation:
    """Tests for schema-enforced constraints on the generated model."""

    def test_rejects_zero_timeout(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            HonchoClientConfig(timeout=0)

    def test_rejects_negative_max_retries(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            HonchoClientConfig(max_retries=-1)

    def test_accepts_valid_config(self) -> None:
        config = HonchoClientConfig(timeout=5, max_retries=3)
        assert config.timeout == 5
        assert config.max_retries == 3


@pytest.mark.integration
class TestHonchoIntegration:
    """Integration tests requiring a running Honcho server.

    Skipped in CI. Run with: pytest -m integration
    Requires: mde-memory stack up (docker compose)
    """

    def test_real_connection(self) -> None:
        from mde.domain.honcho import test_connection

        ok, msg = test_connection()
        assert ok is True, f"Connection failed: {msg}"
```

- [ ] **Step 4: Run full test suite**

Run: `uv run pytest tests/test_honcho_integration.py -v`
Expected: All non-integration tests PASS (4 + 2 + 8 + 1 + 3 = 18 tests, 1 integration skipped)

- [ ] **Step 5: Commit**

```bash
git add tests/test_honcho_integration.py
git commit -m "test: add get_client and test_connection tests"
```

---

### Task 5: Integrate SDK check into `memory verify`

**Files:**
- Modify: `src/mde/domain/memory_stack.py:83-160`

- [ ] **Step 1: Add SDK health check to `stack_verify()`**

In `src/mde/domain/memory_stack.py`, after the existing `for name, cmd in checks:` loop (around line 160), add the SDK connectivity check before the `return` statement:

```python
    # SDK connectivity check (uses honcho-ai SDK, not subprocess)
    from mde.domain.honcho import test_connection

    ok, msg = test_connection()
    if ok:
        print(f"  HEALTHY: honcho-sdk ({msg})", file=sys.stderr)
    else:
        print(f"  UNHEALTHY: honcho-sdk ({msg})", file=sys.stderr)
        failures += 1

    return 1 if failures else 0
```

This replaces the existing `return 1 if failures else 0` at line 160.

- [ ] **Step 2: Verify ruff is clean**

Run: `uv run ruff check src/mde/domain/memory_stack.py src/mde/domain/honcho.py`
Expected: No errors

- [ ] **Step 3: Run quality gate**

Run: `uv run mde-py quality`
Expected: 6/6 passed (or at least lint + test pass)

- [ ] **Step 4: Commit**

```bash
git add src/mde/domain/memory_stack.py
git commit -m "feat: add SDK connectivity check to memory verify"
```

---

### Task 6: Quality gate and cleanup

**Files:**
- All modified files

- [ ] **Step 1: Run full quality gate**

Run: `uv run mde-py quality`
Expected: 6/6 passed. Read ALL output — address any warnings.

- [ ] **Step 2: Fix any warnings or lint issues**

If ruff, ty, or pyright flag anything, fix it. Common issues:
- Generated model may need additional per-file-ignores
- ty may flag the generated model — check if it's in the exclude list

- [ ] **Step 3: Create GitHub issue for future codegen migration**

Run:
```bash
gh issue create \
  --title "Migrate existing codegen outputs to generated/ pipeline" \
  --body "Move existing codegen output files to use the generated/ intermediate directory pattern introduced in the honcho-sdk-integration PR.

Files to migrate:
- src/mde/statusline/models.py
- src/mde/research/clients/skillsmp_models.py
- src/mde/hooks/agent_frontmatter_model.py

Pattern: schema → generated/*.py → cp to src/ import location.
Remove per-file-ignores for migrated files once they route through generated/." \
  --label "auto:agent-discovered"
```

- [ ] **Step 4: Final commit if any fixes were needed**

Stage only the specific files that were fixed (never `git add -A`):

```bash
git add <specific-files-that-changed>
git commit -m "fix: address quality gate findings"
```
