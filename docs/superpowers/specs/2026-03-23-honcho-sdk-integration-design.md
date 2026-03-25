# Honcho SDK Integration Design

**Date:** 2026-03-23
**Status:** Approved
**Scope:** Add honcho-ai Python SDK as library dependency with schema-driven config

## Summary

Integrate the `honcho-ai` Python SDK (v2.0.1) with the self-hosted Honcho
API-only stack. The SDK is exposed as a library dependency — no CLI wrapper.
A schema-driven codegen pipeline generates the config model. A new top-level
`generated/` directory consolidates all generated artifacts.

## Decision Record

### Adversarial review (3 agents)

- **yagni-critic:** Codegen only justified if schema-driven is policy (it is).
  Drop orjson postprocess. Drop CLI boilerplate.
- **sdk-critic:** Pin `>=2.0.0,<3.0.0`. Use `api_key=None` for no-auth.
  Handle 10+ error modes with `max_retries=0`. Import SDK response types
  directly — don't duplicate in our schema.
- **consistency-critic:** Merge into existing namespace or go library-only.
  Follow zero-arg handler pattern if adding CLI. Add per-file-ignores for
  generated code (moot with `generated/` directory).

### Key decisions

1. **Library-only** — no CLI subcommands. SDK used directly by mde modules.
2. **Schema-driven codegen** — `HonchoClientConfig` generated from JSON Schema.
3. **`generated/` at project root** — gitignored, holds intermediate build
   artifacts. Mise codegen tasks generate here, then copy Python files to
   import locations. **Copy targets are committed to git** so fresh clones
   work without running codegen.
4. **Import SDK response types directly** — no schema duplication for
   `WorkspaceResponse`, `QueueStatusResponse`, etc.
5. **No orjson postprocess** — Pydantic v2 handles serialization natively.

## Architecture

```
generated/                           ← gitignored, all build artifacts
  honcho_models.py                   ← codegen output (intermediate)

docs/schemas/
  honcho-client.schema.json          ← source of truth for config model

src/mde/
  domain/
    honcho_models.py                 ← copied from generated/ (committed to git)
    honcho.py                        ← get_client(), test_connection()
    memory_stack.py                  ← modified: adds honcho-sdk health check

tests/
  test_honcho_integration.py         ← mocked SDK tests

.mise.toml                           ← mde:codegen:honcho, mde:codegen:all
pyproject.toml                       ← honcho-ai dep, ruff/ty/pyright excludes
.gitignore                           ← add: generated/
```

## New Files to Create

- `generated/` — directory (no `__init__.py`, not a Python package)
- `docs/schemas/honcho-client.schema.json`
- `src/mde/domain/honcho.py` — client factory (in existing `domain/` directory)
- `src/mde/domain/honcho_models.py` — codegen output (committed to git)
- `tests/test_honcho_integration.py`

## Files to Modify

- `.gitignore` — add `generated/`
- `pyproject.toml` — add dep, add per-file-ignores, add ruff/ty/pyright excludes
- `.mise.toml` — add codegen tasks
- `src/mde/domain/memory_stack.py` — add honcho-sdk health check to `stack_verify()`

## Component Details

### 1. JSON Schema (`docs/schemas/honcho-client.schema.json`)

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

**Note:** No `required` array. All fields have defaults. This ensures
datamodel-codegen emits default values in the generated Pydantic model,
so `HonchoClientConfig()` works with zero arguments. The `get_config()`
function overrides defaults from env vars.

### 2. Codegen Pipeline

**Mise task `mde:codegen:honcho`:**

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
```

**Aggregate task `mde:codegen:all` (NEW — does not exist yet):**

```toml
[tasks."mde:codegen:all"]
description = "Run all codegen tasks"
depends = ["mde:codegen:statusline", "mde:codegen:skillsmp", "mde:codegen:honcho"]
```

### 3. Client Factory (`src/mde/domain/honcho.py`)

```python
"""Honcho SDK client factory.

Provides a pre-configured Honcho client reading connection
parameters from environment variables with schema-validated defaults.
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

**Integration with `memory verify`:**

`stack_verify()` in `memory_stack.py` gains a 4th health check that calls
`test_connection()`. This surfaces SDK connectivity issues alongside Docker
container health, without adding a new CLI command:

```python
# Added to memory_stack.py stack_verify() checks list:
(
    "honcho-sdk",
    None,  # Not a subprocess check — uses SDK directly
),
```

After the existing subprocess checks, add:
```python
# SDK connectivity check (uses honcho-ai SDK, not subprocess)
from mde.domain.honcho import test_connection
ok, msg = test_connection()
if ok:
    print(f"  HEALTHY: honcho-sdk ({msg})", file=sys.stderr)
else:
    print(f"  UNHEALTHY: honcho-sdk ({msg})", file=sys.stderr)
    failures += 1
```

**Changes from v1 spec (addressing review findings #6, #11, #12):**
- Moved SDK imports inside try block so `ImportError` is caught correctly.
- Replaced `client._ensure_workspace()` (private) with `client.workspaces()`
  (public). Avoids `SLF001` ruff violation — no per-file-ignore needed.
- Added `RateLimitError` handling for completeness.

### 4. `generated/` Directory

**New files/entries:**
- Create `generated/` directory at project root
- Add to `.gitignore`: `generated/`
- Add to ruff `extend-exclude`: `"generated"`
- Add to ty `[tool.ty.src] exclude`: `"generated"`
- Add to pyright `exclude`: `"generated"`
- `generated/` has NO `__init__.py` — it's not a Python package
- Python files are copied to their import locations by codegen tasks

**Per-file-ignores for copy target:**

The copied file `src/mde/domain/honcho_models.py` IS in the linted source
tree. Add per-file-ignores in `pyproject.toml`:

```toml
"src/mde/domain/honcho_models.py" = [
    "D100",     # generated file — no module docstring
    "D101",     # generated file — no class docstrings
    "ERA001",   # generated file — codegen header comments
    "E501",     # generated file — long descriptions from schema
    "COM812",   # generated file — trailing comma style
]
```

Also add `src/mde/domain/honcho_models.py` to `[tool.ty.src] exclude` (matches existing precedent — `agent_frontmatter_model.py` is already excluded).

**Future migration** (separate PRs — tracked via GitHub issue):

Implementation will create a GitHub issue (`auto:agent-discovered` label)
to track migration of existing generated files to the `generated/` pipeline:
- `src/mde/statusline/models.py` → generate to `generated/`, copy to source
- `src/mde/research/clients/skillsmp_models.py` → same
- `src/mde/hooks/agent_frontmatter_model.py` → same
- Remove per-file-ignores for those files once all codegen outputs route
  through `generated/`

### 5. Dependencies

`pyproject.toml`:
```toml
dependencies = [
    ...
    "honcho-ai>=2.0.0,<3.0.0",
    "httpx>=0.28",   # tighten from >=0.27 to match honcho-ai transitive req
]
```

### 6. Tests (`tests/test_honcho_integration.py`)

**Mock target:** `patch("honcho.Honcho")` — this works because `get_client()`
uses a lazy import (`from honcho import Honcho as _Honcho`) inside the
function body. The patch intercepts before the name is bound on each call.
Note: moving the import to module level would require changing the mock
target to `mde.domain.honcho._Honcho`.

**Test cases:**
- Test `get_config()` reads env vars, falls back to schema defaults
- Test `get_config()` with no env vars returns valid defaults
- Test `get_config()` with malformed env vars (`HONCHO_TIMEOUT=abc`) raises
  `ValueError` with clear message
- Test `get_client()` passes config fields to SDK constructor
- Test `test_connection()` success path (mocked `workspaces()`)
- Test `test_connection()` error paths: `ConnectionError`, `TimeoutError`,
  `AuthenticationError`, `NotFoundError`, `ServerError`, `RateLimitError`
- Test `test_connection()` catch-all for unexpected exceptions
- Test `test_connection()` when SDK not installed (`ImportError`)
- Test `HonchoClientConfig` rejects `timeout=0` and `max_retries=-1`
- `@pytest.mark.integration` tests for real server (skipped without server)

### 7. What's NOT Included

- No CLI subcommands — SDK used as library only
- No orjson helpers — Pydantic v2 handles serialization
- No safe-method allowlist — consumers call SDK directly
- No schema duplication of SDK response types
- No migration of existing generated files (future PRs, tracked via GitHub issue)
- No `_ensure_workspace()` usage — public API only
- No fnox integration for API key — auth is disabled in API-only mode;
  add fnox/Keychain retrieval when `AUTH_USE_AUTH=true` is enabled

**Follow-up spec:** Agent session persistence — use `get_client()` to store
Claude Code session context (conversation history, tool usage, findings) in
Honcho sessions/messages. This is the first consumer of the SDK integration
and the reason for adding the dependency.
