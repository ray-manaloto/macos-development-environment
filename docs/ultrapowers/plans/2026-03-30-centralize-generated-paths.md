# Centralize .generated/ Path Management — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use ultrapowers:subagent-driven-development (recommended) or ultrapowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace 50+ hardcoded `.generated/` paths with a single `MdePaths(BaseSettings)` model backed by mise environment variables, add 2 new quality checks (vulture, import-linter), and delete 287 stale transcript files. (jscpd deferred to a follow-up PR — requires npm global install + threshold tuning.)

**Architecture:** Two-layer composition — chezmoi renders `{{ .chezmoi.sourceDir | dir }}` to an absolute repo root at apply time, then mise expands `$MDE_PROJECT_DIR` references at shell activation via `env_shell_expand = true`. Python reads these via pydantic-settings `BaseSettings` with cascading defaults in `model_post_init`.

**Tech Stack:** mise (env vars), chezmoi (template rendering), pydantic-settings 2.x (BaseSettings), vulture 2.16+ (dead code), import-linter 2.11+ (architectural contracts)

**Spec:** `docs/ultrapowers/specs/2026-03-30-centralized-generated-paths-design.md`
**Research:** `docs/research/trail/findings/2026-03-30-*.yaml` (4 files)

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `home/dot_config/mise/config.toml.tmpl` | Modify | Add `env_shell_expand = true` + MDE_* env vars to `[env]` |
| `src/mde/lib/paths.py` | Rewrite | `MdePaths(BaseSettings)` model + `get_paths()` singleton + backward-compat aliases |
| `src/mde/hooks/_common.py` | Modify | Replace duplicate `repo_root()` with import from `paths.py` |
| `src/mde/hooks/_remember_local.py` | Modify | Replace inline `remember_dir()` with import from `paths.py` |
| `src/mde/hooks/persist_transcripts.py` | Modify | Redirect dest to `get_paths().dir_transcripts` |
| `src/mde/hooks/post_compact.py` | Modify | Use `get_paths().generated_dir` |
| `src/mde/hooks/context_snapshot.py` | Modify | Use `get_paths().dir_context` |
| `src/mde/hooks/save_memory_on_clear.py` | Modify | Use `get_paths().dir_remember` |
| `src/mde/hooks/remember_precompact.py` | Modify | Use `get_paths().dir_remember` |
| `src/mde/debate/invoke.py` | Modify | Use `get_paths().generated_dir` for debate/gemini paths |
| `src/mde/dream/extract.py` | Modify | Use `get_paths()` for learnings/dream dirs |
| `src/mde/dream/state.py` | Modify | Use `get_paths().dir_dream` |
| `src/mde/validate/paths.py` | Create | 9-check path validator |
| `src/mde/validate/__init__.py` | Modify | Register `validate_paths`, add `paths_only` parameter |
| `src/mde/quality.py` | Modify | Add vulture + import-linter checks |
| `pyproject.toml` | Modify | Add deps, vulture/import-linter config, complexity thresholds |
| `.gitignore` | Modify | Add `.import_linter_cache/` |
| `.claude/rules/generated-paths.md` | Create | Reference doc for env vars |
| `tests/mde/test_paths.py` | Create | Unit tests for MdePaths |
| `tests/mde/test_validate_paths.py` | Create | Validator tests |
| `.claude/rules/no-warning-suppression.md` | Modify | Add research + human approval gates for suppressions |
| `CLAUDE.md` | Modify | Reference generated-paths.md for .generated/ paths |
| `AGENTS.md` | Modify | Reference generated-paths.md for .generated/ paths |

**Spec divergences (research-corrected):**
- Spec uses `Field(alias=...)` → plan uses `Field(validation_alias=...)` (avoids changing `model_dump()` keys; see pydantic-settings research)
- Spec adds vulture/import-linter to mise `[tools]` → plan adds as uv dev deps only (vulture not in mise registry; see vulture research)
- Spec includes jscpd → deferred to follow-up (requires npm global + threshold tuning)

---

## Task 1: Create feature branch + add dependencies

**Files:**
- Modify: `pyproject.toml`
- Modify: `.gitignore`

- [ ] **Step 1: Create feature branch**

```bash
git checkout -b feat/centralize-generated-paths
```

- [ ] **Step 2: Add pydantic-settings as explicit runtime dependency**

In `pyproject.toml`, add to `[project.dependencies]`:
```
"pydantic-settings>=2.13",
```

Note: pydantic-settings is already available as a transitive dep (v2.13.1), but must be declared explicitly since `MdePaths(BaseSettings)` is a core API.

- [ ] **Step 3: Add vulture and import-linter as dev dependencies**

```bash
uv add --group dev "vulture>=2.16" "import-linter>=2.11"
```

- [ ] **Step 4: Add .import_linter_cache/ to .gitignore**

Append to `.gitignore`:
```
.import_linter_cache/
```

- [ ] **Step 5: Verify deps install cleanly**

```bash
uv sync
uv run vulture --version
uv run lint-imports --version
```
Expected: vulture 2.16+, import-linter 2.11+

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock .gitignore
git commit -m "feat: add pydantic-settings, vulture, import-linter deps"
```

---

## Task 2: Write MdePaths tests (TDD red)

**Files:**
- Create: `tests/mde/test_paths.py`

- [ ] **Step 1: Write all MdePaths unit tests**

```python
"""Tests for centralized MdePaths model."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _clear_paths_cache() -> Generator[None, None, None]:
    """Clear get_paths() lru_cache before and after each test.

    Without this, monkeypatched env vars in one test leak into
    subsequent tests that call get_paths() or repo_root().
    """
    from mde.lib.paths import get_paths

    get_paths.cache_clear()
    yield
    get_paths.cache_clear()


class TestMdePathsCascade:
    """Cascading default behavior."""

    def test_cascade_from_project_dir(self, tmp_path: Path) -> None:
        """All paths derive from project_dir when nothing else is set."""
        from mde.lib.paths import MdePaths

        paths = MdePaths(project_dir=tmp_path)
        assert paths.generated_dir == tmp_path / ".generated"
        assert paths.dir_remember == tmp_path / ".generated" / "remember"
        assert paths.dir_learnings == tmp_path / ".generated" / "learnings"
        assert paths.dir_transcripts == tmp_path / ".generated" / "transcripts"
        assert paths.dir_schemas == tmp_path / ".generated" / "schemas"
        assert paths.dir_reports == tmp_path / ".generated" / "reports"
        assert paths.dir_context == tmp_path / ".generated" / "context"
        assert paths.dir_dream == tmp_path / ".generated" / "dream"

    def test_override_generated_dir_cascades(self, tmp_path: Path) -> None:
        """Overriding generated_dir cascades to all child dirs."""
        from mde.lib.paths import MdePaths

        custom_gen = tmp_path / "custom-gen"
        paths = MdePaths(project_dir=tmp_path, generated_dir=custom_gen)
        assert paths.dir_remember == custom_gen / "remember"
        assert paths.dir_dream == custom_gen / "dream"
        assert paths.dir_learnings == custom_gen / "learnings"

    def test_override_individual_child(self, tmp_path: Path) -> None:
        """Individual child dirs can be overridden without affecting siblings."""
        from mde.lib.paths import MdePaths

        paths = MdePaths(project_dir=tmp_path, dir_remember=tmp_path / "my-remember")
        assert paths.dir_remember == tmp_path / "my-remember"
        assert paths.dir_learnings == tmp_path / ".generated" / "learnings"


class TestMdePathsEnvVars:
    """Environment variable loading via BaseSettings."""

    def test_env_var_loading(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """MDE_* env vars populate the model."""
        from mde.lib.paths import MdePaths

        monkeypatch.setenv("MDE_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("MDE_GENERATED_DIR", str(tmp_path / "gen"))
        paths = MdePaths()
        assert paths.project_dir == tmp_path
        assert paths.generated_dir == tmp_path / "gen"
        assert paths.dir_remember == tmp_path / "gen" / "remember"

    def test_env_var_for_child_dir(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """MDE_DIR_REMEMBER env var overrides the cascaded default."""
        from mde.lib.paths import MdePaths

        monkeypatch.setenv("MDE_PROJECT_DIR", str(tmp_path))
        monkeypatch.setenv("MDE_DIR_REMEMBER", str(tmp_path / "custom-remember"))
        paths = MdePaths()
        assert paths.dir_remember == tmp_path / "custom-remember"
        assert paths.dir_learnings == tmp_path / ".generated" / "learnings"

    def test_fallback_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without env vars, project_dir detected via git."""
        from mde.lib.paths import MdePaths

        for key in list(os.environ):
            if key.startswith("MDE_"):
                monkeypatch.delenv(key, raising=False)
        paths = MdePaths()
        assert paths.project_dir is not None
        assert paths.generated_dir == paths.project_dir / ".generated"


class TestMdePathsTypeSafety:
    """Type coercion and field types."""

    def test_all_fields_are_path(self, tmp_path: Path) -> None:
        """Every path field returns a pathlib.Path instance."""
        from mde.lib.paths import MdePaths

        paths = MdePaths(project_dir=tmp_path)
        for name in (
            "project_dir", "generated_dir", "dir_remember", "dir_learnings",
            "dir_transcripts", "dir_schemas", "dir_reports", "dir_context", "dir_dream",
        ):
            assert isinstance(getattr(paths, name), Path), f"{name} is not a Path"

    def test_string_env_coerced_to_path(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """String env vars are auto-coerced to pathlib.Path."""
        from mde.lib.paths import MdePaths

        monkeypatch.setenv("MDE_PROJECT_DIR", str(tmp_path))
        paths = MdePaths()
        assert isinstance(paths.project_dir, Path)


class TestBackwardCompat:
    """Backward-compatible function aliases."""

    def test_repo_root_alias(self) -> None:
        """repo_root() returns same value as get_paths().project_dir."""
        from mde.lib.paths import get_paths, repo_root

        assert repo_root() == get_paths().project_dir

    def test_generated_dir_alias(self) -> None:
        """generated_dir() returns same value as get_paths().generated_dir."""
        from mde.lib.paths import generated_dir, get_paths

        assert generated_dir() == get_paths().generated_dir

    def test_common_repo_root_is_paths_repo_root(self) -> None:
        """_common.py must import repo_root from paths.py, not redefine it."""
        from mde.hooks._common import repo_root as common_rr
        from mde.lib.paths import repo_root as paths_rr

        assert common_rr is paths_rr


class TestGetPathsSingleton:
    """get_paths() caching behavior."""

    def test_get_paths_returns_same_instance(self) -> None:
        """get_paths() is cached — same instance each call."""
        from mde.lib.paths import get_paths

        assert get_paths() is get_paths()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/mde/test_paths.py -v
```
Expected: Multiple FAILs — `MdePaths` doesn't exist yet, `_common.repo_root` is not imported from `paths`.

- [ ] **Step 3: Commit failing tests**

```bash
git add tests/mde/test_paths.py
git commit -m "test: add MdePaths unit tests (red phase)"
```

---

## Task 3: Implement MdePaths model (TDD green)

**Files:**
- Rewrite: `src/mde/lib/paths.py`

- [ ] **Step 1: Rewrite paths.py with MdePaths BaseSettings model**

```python
"""Centralized MDE path configuration.

All `.generated/` subdirectory paths are managed here via a single
pydantic-settings ``BaseSettings`` model. Environment variables are set by
mise (via chezmoi-managed global config) and read automatically.

Usage:
    from mde.lib.paths import get_paths
    paths = get_paths()
    dest = paths.dir_remember  # Path(".generated/remember")

Testing:
    paths = MdePaths(project_dir=tmp_path)  # no env vars needed
"""

from __future__ import annotations

import contextlib
import os
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}

# Subdirectory names under .generated/ — single source of truth for defaults
_CHILD_DEFAULTS: dict[str, str] = {
    "dir_remember": "remember",
    "dir_learnings": "learnings",
    "dir_transcripts": "transcripts",
    "dir_schemas": "schemas",
    "dir_reports": "reports",
    "dir_context": "context",
    "dir_dream": "dream",
}


def _detect_repo_root() -> Path:
    """Detect git repo root via git rev-parse, falling back to cwd."""
    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            env=_GIT_ENV,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    return Path.cwd()


class MdePaths(BaseSettings):
    """Centralized MDE path configuration.

    Reads MDE_* environment variables (set by mise via chezmoi-managed global config).
    Applies cascading defaults: project_dir -> generated_dir -> child dirs.
    Pass explicit values in tests: ``MdePaths(project_dir=tmp_path)``.
    """

    model_config = SettingsConfigDict(
        env_prefix="MDE_",
        populate_by_name=True,
        extra="ignore",  # Allow unknown MDE_* env vars without crashing
    )

    # Layer 0: repo root — only field that touches git or chezmoi
    project_dir: Path | None = Field(
        default=None,
        description="Repository root (MDE_PROJECT_DIR). Detected via git if unset.",
    )
    # Layer 1: generated root — composes from project_dir
    generated_dir: Path | None = Field(
        default=None,
        description="Root of all runtime artifacts (MDE_GENERATED_DIR).",
    )
    # Layer 2: subdirectories — compose from generated_dir
    # NOTE: validation_alias (not alias) — avoids changing model_dump() key names.
    # See research finding 2026-03-30-pydantic-settings-basesettings.yaml.
    dir_remember: Path | None = Field(
        default=None, validation_alias="MDE_DIR_REMEMBER",
    )
    dir_learnings: Path | None = Field(
        default=None, validation_alias="MDE_DIR_LEARNINGS",
    )
    dir_transcripts: Path | None = Field(
        default=None, validation_alias="MDE_DIR_TRANSCRIPTS",
    )
    dir_schemas: Path | None = Field(
        default=None, validation_alias="MDE_DIR_SCHEMAS",
    )
    dir_reports: Path | None = Field(
        default=None, validation_alias="MDE_DIR_REPORTS",
    )
    dir_context: Path | None = Field(
        default=None, validation_alias="MDE_DIR_CONTEXT",
    )
    dir_dream: Path | None = Field(
        default=None, validation_alias="MDE_DIR_DREAM",
    )

    def model_post_init(self, _context: Any) -> None:
        """Apply cascading defaults: project_dir -> generated_dir -> child dirs."""
        if self.project_dir is None:
            self.project_dir = _detect_repo_root()
        if self.generated_dir is None:
            self.generated_dir = self.project_dir / ".generated"
        for field_name, subdir in _CHILD_DEFAULTS.items():
            if getattr(self, field_name) is None:
                setattr(self, field_name, self.generated_dir / subdir)


@lru_cache(maxsize=1)
def get_paths() -> MdePaths:
    """Return the singleton MdePaths instance.

    Cached for the process lifetime. All consumers use this
    instead of constructing MdePaths directly.
    """
    return MdePaths()


# ── Backward-compatible aliases (remove after full migration) ──


def repo_root() -> Path:
    """Return the repository root. Alias for get_paths().project_dir."""
    p = get_paths().project_dir
    assert p is not None  # noqa: S101 — always set by model_post_init
    return p


def generated_dir() -> Path:
    """Return .generated/ dir. Alias for get_paths().generated_dir."""
    p = get_paths().generated_dir
    assert p is not None  # noqa: S101 — always set by model_post_init
    return p
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
uv run pytest tests/mde/test_paths.py -v
```
Expected: All pass EXCEPT `test_common_repo_root_is_paths_repo_root` (identity check fails until Task 4).

- [ ] **Step 3: Run quality gate**

```bash
uv run mde-py quality
```
Expected: All checks pass (existing 6/6).

- [ ] **Step 4: Commit**

```bash
git add src/mde/lib/paths.py
git commit -m "feat: add MdePaths(BaseSettings) centralized path model"
```

---

## Task 4: Consolidate duplicate repo_root()

**Files:**
- Modify: `src/mde/hooks/_common.py`
- Modify: `src/mde/hooks/_remember_local.py`

- [ ] **Step 1: Replace _common.py duplicate repo_root with import**

In `src/mde/hooks/_common.py`:
- Remove the `repo_root()` function definition (lines 31-43)
- Remove `contextlib` and `subprocess` imports if no longer used
- Add: `from mde.lib.paths import repo_root`
- Keep `repo_root` in `__all__`

```python
"""Shared utilities for Claude Code hook entry points."""

from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mde.lib.paths import repo_root
from mde.log import get_tracer, logger

if TYPE_CHECKING:
    from collections.abc import Generator

    from opentelemetry.trace import Span

_tracer = get_tracer("mde.hooks")

_GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}


def parse_hook_stdin() -> dict[str, Any]:
    """Parse Claude Code hook JSON from stdin."""
    return json.load(sys.stdin)


@contextmanager
def hook_span(
    name: str,
    event: str,
    data: dict[str, Any],
) -> Generator[Span]:
    """Open a traced span for a hook with standard attributes."""
    session_id = data.get("session_id", "")
    tool_use_id = data.get("tool_use_id", "")
    with _tracer.start_as_current_span(f"mde.hook.{name}") as span:
        span.set_attribute("hook.event", event)
        span.set_attribute("claude.session_id", session_id)
        if tool_use_id:
            span.set_attribute("claude.tool_use_id", tool_use_id)
        yield span


__all__ = ["hook_span", "logger", "parse_hook_stdin", "repo_root"]
```

- [ ] **Step 2: Replace _remember_local.py inline remember_dir**

In `src/mde/hooks/_remember_local.py`:
- Remove the `remember_dir()` function (lines 20-22)
- Change import: `from mde.hooks._common import _GIT_ENV, repo_root` → `from mde.hooks._common import _GIT_ENV`
- Add: `from mde.lib.paths import get_paths`
- Replace `remember_dir()` calls with `get_paths().dir_remember`

The `remember_dir()` function and its callers become:
```python
from mde.lib.paths import get_paths
# ...
def append_now_entry(event: str, message: str) -> bool:
    rdir = get_paths().dir_remember
    # ... rest unchanged, but 'rdir' is now Path, not function call
```

- [ ] **Step 3: Run the identity test**

```bash
uv run pytest tests/mde/test_paths.py::TestBackwardCompat::test_common_repo_root_is_paths_repo_root -v
```
Expected: PASS (identity check now succeeds).

- [ ] **Step 4: Run full test suite**

```bash
uv run pytest tests/ -x -q -m "not integration"
```
Expected: All pass — no consumer broke because `_common.repo_root` still re-exports `paths.repo_root`.

- [ ] **Step 5: Quality gate**

```bash
uv run mde-py quality
```

- [ ] **Step 6: Commit**

```bash
git add src/mde/hooks/_common.py src/mde/hooks/_remember_local.py
git commit -m "refactor: consolidate duplicate repo_root() into paths.py"
```

---

## Task 5: Redirect persist_transcripts to .generated/transcripts/

**Files:**
- Modify: `src/mde/hooks/persist_transcripts.py`

- [ ] **Step 1: Update persist_transcripts.py**

Change the destination from `docs/research/trail/deep-reviews/agent-transcripts/` to `get_paths().dir_transcripts`:

```python
# Before (line 82-83):
repo = repo_root()
dest_dir = repo / "docs" / "research" / "trail" / "deep-reviews" / "agent-transcripts"

# After:
from mde.lib.paths import get_paths
# ...
dest_dir = get_paths().dir_transcripts
```

Remove the `from mde.hooks._common import repo_root` import. Replace all `repo_root()` usage:

```python
# Before (lines 82-83):
repo = repo_root()
dest_dir = repo / "docs" / "research" / "trail" / "deep-reviews" / "agent-transcripts"

# After:
paths = get_paths()
dest_dir = paths.dir_transcripts

# Before (line 134):
dest=str(dest_dir.relative_to(repo)),

# After:
dest=str(dest_dir.relative_to(paths.project_dir)),
```

- [ ] **Step 2: Run tests**

```bash
uv run pytest tests/ -x -q -m "not integration"
```

- [ ] **Step 3: Quality gate**

```bash
uv run mde-py quality
```

- [ ] **Step 4: Commit**

```bash
git add src/mde/hooks/persist_transcripts.py
git commit -m "refactor: redirect persist_transcripts to .generated/transcripts/"
```

---

## Task 6: Update remaining consumers

**Files:**
- Modify: `src/mde/hooks/post_compact.py`
- Modify: `src/mde/hooks/context_snapshot.py`
- Modify: `src/mde/hooks/save_memory_on_clear.py`
- Modify: `src/mde/hooks/remember_precompact.py`
- Modify: `src/mde/debate/invoke.py`
- Modify: `src/mde/dream/extract.py`
- Modify: `src/mde/dream/state.py`

Migration pattern for each file:
```python
# Before:
from mde.hooks._common import repo_root
dest = repo_root() / ".generated" / "something"

# After:
from mde.lib.paths import get_paths
dest = get_paths().dir_something  # or get_paths().generated_dir / "something" for non-standard subdirs
```

- [ ] **Step 1: Update post_compact.py**

Replace `repo_root() / ".generated" / "compact-events.jsonl"` with `get_paths().generated_dir / "compact-events.jsonl"`.

- [ ] **Step 2: Update context_snapshot.py**

Replace `generated_dir() / "context-snapshot.json"` with `get_paths().dir_context / "context-snapshot.json"`. Note: this MOVES the file from `.generated/context-snapshot.json` to `.generated/context/context-snapshot.json`.

- [ ] **Step 3: Update save_memory_on_clear.py**

Replace hardcoded `.generated/remember/` references with `get_paths().dir_remember`.

- [ ] **Step 4: Update remember_precompact.py**

Replace any `.generated/remember/` references with `get_paths().dir_remember`.

- [ ] **Step 5: Update debate/invoke.py**

Replace:
- `Path.cwd() / ".generated" / "debate"` → `get_paths().generated_dir / "debate"`
- `Path.cwd() / ".generated" / "gemini"` → `get_paths().generated_dir / "gemini"`

Note: debate and gemini are transient subdirs, not in the MdePaths model. Use `generated_dir` as base.

- [ ] **Step 6: Update dream/extract.py**

Replace `generated_dir()` calls with `get_paths().generated_dir`, `get_paths().dir_learnings`, `get_paths().dir_dream` as appropriate.

- [ ] **Step 7: Update dream/state.py**

Replace `generated_dir()` with `get_paths().dir_dream`.

- [ ] **Step 8: Run full test suite**

```bash
uv run pytest tests/ -x -q -m "not integration"
```

- [ ] **Step 9: Quality gate**

```bash
uv run mde-py quality
```

- [ ] **Step 10: Commit**

```bash
git add src/mde/hooks/post_compact.py src/mde/hooks/context_snapshot.py \
  src/mde/hooks/save_memory_on_clear.py src/mde/hooks/remember_precompact.py \
  src/mde/debate/invoke.py src/mde/dream/extract.py src/mde/dream/state.py
git commit -m "refactor: migrate all consumers to centralized MdePaths"
```

---

## Task 7: Add chezmoi template env vars

**Files:**
- Modify: `home/dot_config/mise/config.toml.tmpl`

**Note:** The spec's Files Changed table lists adding vulture/import-linter to `[tools]` in this template — this is incorrect per research. Both tools are uv dev deps only (vulture not in mise registry). Do NOT add them to mise `[tools]`.

- [ ] **Step 1: Add env_shell_expand setting**

In `[settings]` section, add:
```toml
env_shell_expand = true  # Enable $VAR expansion in [env] — required for DRY path composition
```

- [ ] **Step 2: Add MDE_* env vars to [env] section**

After the existing env vars (GIT_TERMINAL_PROMPT, NOTEBOOKLM_HOME), add:
```toml
# MDE path management — single source of truth for .generated/ structure
# Layer 1: chezmoi renders {{ .chezmoi.sourceDir | dir }} to absolute repo root at `chezmoi apply`
# Layer 2: mise expands $MDE_PROJECT_DIR/$MDE_GENERATED_DIR at shell activation via env_shell_expand
# RULE: Only MDE_PROJECT_DIR uses the chezmoi template variable directly.
#       All other vars MUST compose from $MDE_PROJECT_DIR or $MDE_GENERATED_DIR.
MDE_PROJECT_DIR = "{{ .chezmoi.sourceDir | dir }}"
MDE_GENERATED_DIR = "$MDE_PROJECT_DIR/.generated"
MDE_DIR_REMEMBER = "$MDE_GENERATED_DIR/remember"
MDE_DIR_LEARNINGS = "$MDE_GENERATED_DIR/learnings"
MDE_DIR_TRANSCRIPTS = "$MDE_GENERATED_DIR/transcripts"
MDE_DIR_SCHEMAS = "$MDE_GENERATED_DIR/schemas"
MDE_DIR_REPORTS = "$MDE_GENERATED_DIR/reports"
MDE_DIR_CONTEXT = "$MDE_GENERATED_DIR/context"
MDE_DIR_DREAM = "$MDE_GENERATED_DIR/dream"
```

- [ ] **Step 3: Verify chezmoi template renders correctly**

```bash
chezmoi execute-template < home/dot_config/mise/config.toml.tmpl | grep MDE_
```
Expected: `MDE_PROJECT_DIR = "/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment"` and all other vars using `$MDE_PROJECT_DIR` or `$MDE_GENERATED_DIR`.

- [ ] **Step 4: Commit**

```bash
git add home/dot_config/mise/config.toml.tmpl
git commit -m "feat: add MDE_* env vars to global mise config template"
```

---

## Task 8: Add pyproject.toml tool config

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add vulture config**

```toml
[tool.vulture]
min_confidence = 80
paths = ["src/mde/"]
ignore_names = ["__hook_meta__", "test_*"]
ignore_decorators = ["@click.*", "@pytest.*"]
```

- [ ] **Step 2: Add import-linter config**

```toml
[tool.importlinter]
root_packages = ["mde"]
exclude_type_checking_imports = true

[[tool.importlinter.contracts]]
name = "lib must not import hooks"
type = "forbidden"
source_modules = ["mde.lib"]
forbidden_modules = ["mde.hooks", "mde.cli"]

[[tool.importlinter.contracts]]
name = "models must not import hooks or cli"
type = "forbidden"
source_modules = ["mde.models"]
forbidden_modules = ["mde.hooks", "mde.cli", "mde.dream", "mde.debate"]

[[tool.importlinter.contracts]]
name = "validate must not import hooks"
type = "forbidden"
source_modules = ["mde.validate"]
forbidden_modules = ["mde.hooks"]
```

- [ ] **Step 3: Add complexity thresholds**

```toml
[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-branches = 12
max-returns = 6
max-statements = 50
```

- [ ] **Step 4: Run new tools to verify config**

```bash
uv run vulture src/mde/
uv run lint-imports
```
Expected: vulture may find 2 existing issues (fix in Task 9). import-linter should pass.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add vulture, import-linter, complexity configs to pyproject.toml"
```

---

## Task 9: Fix existing dead code findings

**Files:**
- Modify: `src/mde/consensus.py` (line ~106: unused variable `cls`)
- Modify: `src/mde/statusline/schema.py` (line ~15: unused import `RateLimitType`)

- [ ] **Step 1: Fix consensus.py unused variable**

Read `src/mde/consensus.py` around line 106, remove or use the unused `cls` variable.

- [ ] **Step 2: Fix statusline/schema.py unused import**

Read `src/mde/statusline/schema.py` around line 15, remove unused `RateLimitType` import.

- [ ] **Step 3: Verify vulture passes clean**

```bash
uv run vulture src/mde/
```
Expected: Exit code 0 (no findings).

- [ ] **Step 4: Quality gate**

```bash
uv run mde-py quality
```

- [ ] **Step 5: Commit**

```bash
git add src/mde/consensus.py src/mde/statusline/schema.py
git commit -m "fix: remove dead code found by vulture (consensus.cls, RateLimitType)"
```

---

## Task 10: Add vulture + import-linter to quality gate

**Files:**
- Modify: `src/mde/quality.py`

- [ ] **Step 1: Add new checks to _LINT_CHECKS**

After the existing pyright check, add:
```python
("vulture", ["uv", "run", "vulture", "src/mde/"], "Dead code check"),
("import-linter", ["uv", "run", "lint-imports"], "Architectural contract check"),
```

- [ ] **Step 2: Run quality gate**

```bash
uv run mde-py quality
```
Expected: 8/8 passed (or 9/9 if counting mde-validate). All new checks should pass since Task 9 fixed existing findings.

- [ ] **Step 3: Commit**

```bash
git add src/mde/quality.py
git commit -m "feat: add vulture and import-linter to quality gate"
```

---

## Task 11: Write path validator tests (TDD red)

**Files:**
- Create: `tests/mde/test_validate_paths.py`

- [ ] **Step 1: Write validator tests**

```python
"""Tests for the paths validator."""

from __future__ import annotations

from pathlib import Path

import pytest

from mde.validate.paths import validate_paths


class TestValidatePathsEnvVarMissing:
    """Check 1: paths.env-var-missing."""

    def test_warns_when_mde_generated_dir_unset(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        for key in ("MDE_PROJECT_DIR", "MDE_GENERATED_DIR"):
            monkeypatch.delenv(key, raising=False)
        result = validate_paths(root=tmp_path)
        msgs = [f.message for f in result.findings]
        assert any("MDE_GENERATED_DIR" in m for m in msgs)


class TestValidatePathsRememberSymlink:
    """Check 3: paths.remember-symlink."""

    def test_error_when_remember_is_dir(self, tmp_path: Path) -> None:
        (tmp_path / ".remember").mkdir()
        result = validate_paths(root=tmp_path)
        assert not result.passed
        msgs = [f.message for f in result.findings]
        assert any("symlink" in m.lower() for m in msgs)

    def test_pass_when_remember_is_symlink(self, tmp_path: Path) -> None:
        target = tmp_path / ".generated" / "remember"
        target.mkdir(parents=True)
        (tmp_path / ".remember").symlink_to(target)
        result = validate_paths(root=tmp_path)
        symlink_errors = [
            f for f in result.findings
            if "symlink" in f.message.lower() and f.severity.value == "error"
        ]
        assert len(symlink_errors) == 0


class TestValidatePathsHardcodedRef:
    """Check 6: paths.hardcoded-ref."""

    def test_warns_on_hardcoded_generated(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "src" / "mde"
        src_dir.mkdir(parents=True)
        (src_dir / "bad.py").write_text('x = repo_root() / ".generated" / "foo"\n')
        result = validate_paths(root=tmp_path)
        msgs = [f.message for f in result.findings]
        assert any("hardcoded" in m.lower() or ".generated" in m for m in msgs)


class TestValidatePathsCompositionViolation:
    """Check 8: paths.composition-violation."""

    def test_error_on_chezmoi_template_in_child_var(self, tmp_path: Path) -> None:
        tpl_dir = tmp_path / "home" / "dot_config" / "mise"
        tpl_dir.mkdir(parents=True)
        (tpl_dir / "config.toml.tmpl").write_text(
            '[env]\n'
            'MDE_PROJECT_DIR = "{{ .chezmoi.sourceDir | dir }}"\n'
            'MDE_DIR_REMEMBER = "{{ .chezmoi.sourceDir | dir }}/.generated/remember"\n'
        )
        result = validate_paths(root=tmp_path)
        assert not result.passed
        msgs = [f.message for f in result.findings]
        assert any("composition" in m.lower() for m in msgs)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/mde/test_validate_paths.py -v
```
Expected: FAIL — `validate_paths` doesn't exist yet.

- [ ] **Step 3: Commit**

```bash
git add tests/mde/test_validate_paths.py
git commit -m "test: add path validator tests (red phase)"
```

---

## Task 12: Implement path validator (TDD green)

**Files:**
- Create: `src/mde/validate/paths.py`
- Modify: `src/mde/validate/__init__.py`

- [ ] **Step 1: Create validate/paths.py**

Implement all 9 checks as described in the spec. Key checks:
1. `paths.env-var-missing` — WARNING if MDE_GENERATED_DIR not in env
2. `paths.dir-missing` — WARNING if env var dirs don't exist
3. `paths.remember-symlink` — ERROR if `.remember` is a dir not symlink
4. `paths.mise-global-missing` — ERROR if `~/.config/mise/config.toml` lacks MDE_PROJECT_DIR
5. `paths.chezmoi-template-missing` — ERROR if template lacks MDE_PROJECT_DIR
6. `paths.hardcoded-ref` — WARNING for `.generated` literals in .py files (except paths.py)
7. `paths.reference-doc-missing` — ERROR if `.claude/rules/generated-paths.md` missing
8. `paths.composition-violation` — ERROR if child vars use chezmoi template directly
9. `paths.env-shell-expand-missing` — ERROR if mise config lacks `env_shell_expand = true`

The function signature:
```python
def validate_paths(root: Path | None = None) -> ValidationResult:
```

- [ ] **Step 2: Register in validate/__init__.py**

Add `paths_only: bool = False` parameter to `run_validators()`. Import and call `validate_paths()` in the full validation block after `validate_structural()`.

Add the `--paths` CLI flag in the `validate_all()` function.

- [ ] **Step 3: Run validator tests**

```bash
uv run pytest tests/mde/test_validate_paths.py -v
```
Expected: All pass.

- [ ] **Step 4: Quality gate**

```bash
uv run mde-py quality
```

- [ ] **Step 5: Commit**

```bash
git add src/mde/validate/paths.py src/mde/validate/__init__.py
git commit -m "feat: add 9-check paths validator"
```

---

## Task 13: Create reference doc + delete stale transcripts

**Files:**
- Create: `.claude/rules/generated-paths.md`
- Delete: `docs/research/trail/deep-reviews/agent-transcripts/*.md` (287 files)

- [ ] **Step 1: Create reference doc**

`.claude/rules/generated-paths.md`:
```markdown
# Centralized .generated/ Path Management

## Environment Variables

All MDE_* env vars are defined in the global mise config (`~/.config/mise/config.toml`),
managed via chezmoi template (`home/dot_config/mise/config.toml.tmpl`).

| Env Var | Composes From | Default | Purpose |
|---------|---------------|---------|---------|
| `MDE_PROJECT_DIR` | chezmoi template | `{{ .chezmoi.sourceDir \| dir }}` | Repository root |
| `MDE_GENERATED_DIR` | `$MDE_PROJECT_DIR` | `$MDE_PROJECT_DIR/.generated` | Runtime artifacts root |
| `MDE_DIR_REMEMBER` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/remember` | Remember plugin data |
| `MDE_DIR_LEARNINGS` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/learnings` | Agent discoveries |
| `MDE_DIR_TRANSCRIPTS` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/transcripts` | Agent transcripts |
| `MDE_DIR_SCHEMAS` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/schemas` | Schema cache |
| `MDE_DIR_REPORTS` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/reports` | Quality reports |
| `MDE_DIR_CONTEXT` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/context` | Context snapshots |
| `MDE_DIR_DREAM` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/dream` | Dream pipeline state |

## Python API

```python
from mde.lib.paths import get_paths
paths = get_paths()
paths.dir_remember     # Path to remember data
paths.generated_dir    # Path to .generated root
paths.project_dir      # Path to repo root
```

## Composition Rules

- Only `MDE_PROJECT_DIR` uses the chezmoi template `{{ .chezmoi.sourceDir | dir }}`
- All other vars compose from `$MDE_PROJECT_DIR` or `$MDE_GENERATED_DIR`
- mise `env_shell_expand = true` enables `$VAR` expansion at shell activation
- Adding a new subdirectory: (1) field in `MdePaths`, (2) entry in `_CHILD_DEFAULTS`, (3) env var in chezmoi template

## Validation

`uv run mde-py validate --paths` runs 9 checks. See `src/mde/validate/paths.py`.
```

- [ ] **Step 2: Delete stale agent transcripts**

```bash
rm -rf docs/research/trail/deep-reviews/agent-transcripts/
```

These 287 files are confirmed unused by the dream pipeline (research finding from earlier session).

- [ ] **Step 3: File GitHub Issue for transcript self-learning**

```bash
gh issue create \
  --title "feat: integrate agent transcript parsing into dream pipeline" \
  --body "Agent transcripts are now saved to .generated/transcripts/ via persist_transcripts hook. Parse these for self-improvement patterns and integrate with dream pipeline signal sources.\n\nContext: transcripts were previously saved to docs/research/trail/deep-reviews/agent-transcripts/ (287 files, now deleted). The dream pipeline currently scans 5 signal sources but not transcripts.\n\nRef: centralize-generated-paths spec Phase 4." \
  --label "auto:agent-discovered,enhancement"
```

- [ ] **Step 4: Quality gate**

```bash
uv run mde-py quality
```

- [ ] **Step 5: Commit**

```bash
git add .claude/rules/generated-paths.md
git rm -r docs/research/trail/deep-reviews/agent-transcripts/ 2>/dev/null || true
git commit -m "docs: add generated-paths reference, delete 287 stale transcripts"
```

---

## Task 14: Update docs and agent references

**Files:**
- Modify: `.claude/rules/no-warning-suppression.md`
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Add suppression gates to no-warning-suppression.md**

Append a "Suppression gates" section documenting the two-gate requirement from the spec:
1. Research gate: document what the finding says, what was reviewed, why it can't be resolved
2. Human approval gate: explicit approval with rule ID, justification, and approver name

- [ ] **Step 2: Update CLAUDE.md references**

Replace any direct `.generated/` path references with a pointer to `.claude/rules/generated-paths.md`. Add a brief note that paths are managed via `MDE_*` env vars.

- [ ] **Step 3: Update AGENTS.md references**

Update the `.generated/` reference in the Architecture section to mention `MDE_*` env vars and reference the generated-paths rule doc.

- [ ] **Step 4: Quality gate**

```bash
uv run mde-py quality
```

- [ ] **Step 5: Commit**

```bash
git add .claude/rules/no-warning-suppression.md CLAUDE.md AGENTS.md
git commit -m "docs: update suppression policy, CLAUDE.md, AGENTS.md for centralized paths"
```

---

## Task 15: Update .mise.toml tasks (if applicable)

**Files:**
- Modify: `.mise.toml` (project-level)

- [ ] **Step 1: Update schema:fetch-upstream task**

Find any task that references `.generated/schemas` and replace with `$MDE_DIR_SCHEMAS`.

- [ ] **Step 2: Verify**

```bash
mise run schema:fetch-upstream --dry-run 2>&1 || echo "Task may not exist"
```

- [ ] **Step 3: Commit if changes were made**

```bash
git add .mise.toml
git commit -m "refactor: use MDE_DIR_SCHEMAS in mise tasks"
```

---

## Task 16: Final verification + push

- [ ] **Step 1: Run full quality gate**

```bash
uv run mde-py quality
```
Expected: All checks pass (now 8 lint checks + pytest + mde-validate).

- [ ] **Step 2: Run validation with --paths flag**

```bash
uv run mde-py validate --paths
```
Expected: Path validator checks pass (some may warn about missing env vars if `chezmoi apply` hasn't been run yet — that's expected).

- [ ] **Step 3: Run full validation**

```bash
uv run mde-py validate --all
```

- [ ] **Step 4: Verify import-linter contracts**

```bash
uv run lint-imports --verbose
```
Expected: All 3 contracts pass.

- [ ] **Step 5: Verify vulture is clean**

```bash
uv run vulture src/mde/
```
Expected: Exit code 0.

- [ ] **Step 6: Push branch**

```bash
git push -u origin feat/centralize-generated-paths
```

- [ ] **Step 7: Create PR**

```bash
gh pr create \
  --title "feat: centralize .generated/ path management with MdePaths(BaseSettings)" \
  --body "$(cat <<'EOF'
## Summary
- Add MdePaths(BaseSettings) model for centralized path management
- Add MDE_* env vars to global mise config via chezmoi template
- Migrate all consumers from hardcoded .generated/ paths to get_paths()
- Add vulture (dead code) and import-linter (architectural contracts) to quality gate
- Delete 287 stale agent transcript files
- Add 9-check path validator

## Spec
docs/ultrapowers/specs/2026-03-30-centralized-generated-paths-design.md

## Test plan
- [ ] Unit tests for MdePaths cascading, env var loading, type safety
- [ ] Validator tests for all 9 path checks
- [ ] Quality gate passes (all checks including new vulture + import-linter)
- [ ] chezmoi template renders correct MDE_* values
- [ ] Existing tests unbroken by consumer migration
EOF
)"
```
