# Centralized .generated/ Path Management

**Date**: 2026-03-30
**Status**: Design
**Branch**: `feat/centralize-generated-paths`

## Problem

`.generated/` paths are hardcoded across 50+ files: Python source, agent definitions, policy rules, mise tasks, and hooks. The duplicate `repo_root()` in `_common.py` and `paths.py` is a concrete example of the drift this causes. Adding a new subdirectory requires updating multiple files.

## Approach: Global mise env via chezmoi template

Add `MDE_*` env vars to the **global** mise config template (`home/dot_config/mise/config.toml.tmpl`), which chezmoi manages. Use chezmoi's `{{ .chezmoi.sourceDir | dir }}` to resolve the repo root at template render time (consistent with existing `.chezmoi.toml.tmpl` pattern). After `chezmoi apply`, these become hardcoded absolute paths in `~/.config/mise/config.toml`. Mise injects them into every shell session — available system-wide.

### Why this approach

- **System-wide availability**: Like fnox secrets, these vars are available in every terminal, not just inside the project directory
- **chezmoi as source of truth**: The template uses `{{ .chezmoi.sourceDir | dir }}` (= repo root), consistent with existing `sourceDir` pattern in `.chezmoi.toml.tmpl`
- **No runtime template resolution**: After `chezmoi apply`, paths are static absolute strings in the rendered config
- **Native consumption**: Python reads `os.environ.get()`, mise tasks use `$VAR`, chezmoi templates use `{{ env "VAR" }}`

### Why `{{ .chezmoi.sourceDir | dir }}` not `.chezmoi.workingTree`

Both resolve to the same value (the repo root). However, `.chezmoi.sourceDir | dir` is the pattern already used in `.chezmoi.toml.tmpl` and documented in `.claude/rules/chezmoi-config-safety.md`. Using the same pattern everywhere prevents confusion. `.chezmoi.workingTree` is valid but less commonly documented.

### Research findings

| System | Variable | Value | Notes |
|---|---|---|---|
| mise Tera | `{{config_root}}` | Dir containing `.mise.toml` | Stable, always repo root for project config |
| mise Tera | `{{cwd}}` | Current working directory | Unstable — changes based on `cd` |
| mise Tera | `{{env.VAR}}` | Other env vars | Works in `[tools]`, documented for `[env]` |
| mise setting | `env_shell_expand` | `$VAR` expansion | After Tera rendering, for composition |
| chezmoi | `.chezmoi.workingTree` | Git-managed directory root | `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment` |
| chezmoi | `.chezmoi.sourceDir` | Source state directory | `.../home` (because `.chezmoiroot = home`) |
| chezmoi | `{{ env "VAR" }}` | Runtime env var | Works if mise activates before chezmoi |
| chezmoi | `.chezmoidata.toml` | Static data file | Only available during `chezmoi apply`, not runtime |

**Decision**: Use `{{ .chezmoi.sourceDir | dir }}` in the global mise config template. This is consistent with the existing `.chezmoi.toml.tmpl` pattern and resolves to the repo root.

## Environment Variables

All defined in `home/dot_config/mise/config.toml.tmpl` under `[env]`:

| Env Var | Composes From | Default Value | Purpose | Consumers |
|---|---|---|---|---|
| `MDE_PROJECT_DIR` | chezmoi template | `{{ .chezmoi.sourceDir \| dir }}` | Repository root | paths.py, agents, mise tasks |
| `MDE_GENERATED_DIR` | `$MDE_PROJECT_DIR` | `$MDE_PROJECT_DIR/.generated` | Root of all runtime artifacts | paths.py, .gitignore, agents |
| `MDE_DIR_REMEMBER` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/remember` | Remember plugin data | remember hooks, .remember symlink |
| `MDE_DIR_LEARNINGS` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/learnings` | Agent learning discoveries | dream pipeline, subagents |
| `MDE_DIR_TRANSCRIPTS` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/transcripts` | Agent session transcripts | persist_transcripts hook |
| `MDE_DIR_SCHEMAS` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/schemas` | Upstream schema cache | schema:fetch-upstream task |
| `MDE_DIR_REPORTS` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/reports` | Validation/quality reports | validators, quality gate |
| `MDE_DIR_CONTEXT` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/context` | Context snapshots | context_snapshot hook |
| `MDE_DIR_DREAM` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/dream` | Dream pipeline state | dream/state.py |

**Composition rule**: Only `MDE_PROJECT_DIR` uses the chezmoi template. All others compose from `$MDE_PROJECT_DIR` or `$MDE_GENERATED_DIR` via mise `env_shell_expand = true`. This is enforced by the `validate_paths` validator (Check 8: `paths.composition-violation`).

## Implementation Plan

### Phase 1: Chezmoi template + mise global config

**File**: `home/dot_config/mise/config.toml.tmpl`

Add to existing `[env]` section (after `_.fnox-env`):

```toml
[settings]
env_shell_expand = true  # Enable $VAR expansion in [env] — required for DRY composition

[env]
_.fnox-env = { tools = true }
# ... existing vars ...

# MDE path management — single source of truth for .generated/ structure
# Layer 1: chezmoi renders {{ .chezmoi.sourceDir | dir }} to absolute repo root at `chezmoi apply`
# Layer 2: mise expands $MDE_PROJECT_DIR/$MDE_GENERATED_DIR at shell activation via env_shell_expand
# RULE: Only MDE_PROJECT_DIR uses the chezmoi template variable directly.
#       All other vars MUST compose from $MDE_PROJECT_DIR or $MDE_GENERATED_DIR.
#       This ensures changing MDE_GENERATED_DIR cascades to all child paths.
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

**Composition requirement**: Only `MDE_PROJECT_DIR` may reference the chezmoi template directly. All other `MDE_*` vars MUST compose from `$MDE_PROJECT_DIR` or `$MDE_GENERATED_DIR` via mise's `env_shell_expand`. This ensures:
- Changing `MDE_GENERATED_DIR` (e.g., `MDE_GENERATED_DIR="/tmp/mde-gen"`) cascades to all child vars
- New subdirectories only need to reference `$MDE_GENERATED_DIR`, not the chezmoi template
- Testing with alternate paths requires overriding a single variable

### Phase 2: Update paths.py — MdePaths BaseSettings model

**File**: `src/mde/lib/paths.py`

Replace individual functions with a single `pydantic-settings` model that reads all MDE_* env vars, applies cascading defaults, and provides a typed API:

```python
from __future__ import annotations

import contextlib
import os
import subprocess
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

_GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}


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
    Pass explicit values in tests: MdePaths(project_dir=tmp_path).
    """

    model_config = {"env_prefix": "MDE_", "populate_by_name": True}

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
    dir_remember: Path | None = Field(default=None, alias="MDE_DIR_REMEMBER")
    dir_learnings: Path | None = Field(default=None, alias="MDE_DIR_LEARNINGS")
    dir_transcripts: Path | None = Field(default=None, alias="MDE_DIR_TRANSCRIPTS")
    dir_schemas: Path | None = Field(default=None, alias="MDE_DIR_SCHEMAS")
    dir_reports: Path | None = Field(default=None, alias="MDE_DIR_REPORTS")
    dir_context: Path | None = Field(default=None, alias="MDE_DIR_CONTEXT")
    dir_dream: Path | None = Field(default=None, alias="MDE_DIR_DREAM")

    def model_post_init(self, __context: object) -> None:
        """Apply cascading defaults: project_dir -> generated_dir -> child dirs."""
        if self.project_dir is None:
            self.project_dir = _detect_repo_root()
        if self.generated_dir is None:
            self.generated_dir = self.project_dir / ".generated"
        _child_defaults = {
            "dir_remember": "remember",
            "dir_learnings": "learnings",
            "dir_transcripts": "transcripts",
            "dir_schemas": "schemas",
            "dir_reports": "reports",
            "dir_context": "context",
            "dir_dream": "dream",
        }
        for field_name, subdir in _child_defaults.items():
            if getattr(self, field_name) is None:
                object.__setattr__(self, field_name, self.generated_dir / subdir)


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
    assert p is not None  # always set by model_post_init
    return p


def generated_dir() -> Path:
    """Return .generated/ dir. Alias for get_paths().generated_dir."""
    p = get_paths().generated_dir
    assert p is not None  # always set by model_post_init
    return p
```

**Consumer migration pattern**:

```python
# Before (scattered os.environ.get, hardcoded strings)
from mde.hooks._common import repo_root
dest = repo_root() / ".generated" / "remember"

# After (typed, centralized, testable)
from mde.lib.paths import get_paths
paths = get_paths()
dest = paths.dir_remember

# In tests (no monkeypatching needed)
paths = MdePaths(project_dir=tmp_path)
assert paths.dir_remember == tmp_path / ".generated" / "remember"

# Override just generated_dir (cascades to children)
paths = MdePaths(project_dir=tmp_path, generated_dir=tmp_path / "custom-gen")
assert paths.dir_remember == tmp_path / "custom-gen" / "remember"
```

**Design rules**:
- All `os.environ.get("MDE_*")` lookups happen inside `MdePaths.__init__` (via BaseSettings) — nowhere else
- Consumers receive `MdePaths` or call `get_paths()` — never read env vars directly
- New subdirectories are added by: (1) adding a field to `MdePaths`, (2) adding to `_child_defaults`, (3) adding env var to chezmoi template
- `pydantic-settings` is already a runtime dependency — no new deps needed

### Phase 3: Consolidate duplicate repo_root()

**File**: `src/mde/hooks/_common.py`

Replace the duplicate `repo_root()` definition with an import:

```python
# Before (duplicate implementation — no caching, subprocess on every call)
def repo_root() -> Path:
    ...

# After (single source of truth — inherits @lru_cache from paths.py)
from mde.lib.paths import repo_root
```

Update `__all__` to re-export it.

**Cache behavior note**: `paths.py`'s `repo_root()` uses `@lru_cache(maxsize=1)`, so `git rev-parse` runs at most once per process. The `_common.py` duplicate was uncached — after this change, all callers share the cache. This is a net positive (eliminates redundant subprocess calls) but means the result is frozen for the process lifetime.

**Also update**: `src/mde/hooks/_remember_local.py` has an inline `_remember_dir()` that computes `repo_root() / ".generated" / "remember"` — this must be replaced with `remember_dir()` from `paths.py`, not just a string-replace of `".generated"`.

### Phase 4: Redirect persist_transcripts

**File**: `src/mde/hooks/persist_transcripts.py` (or equivalent)

Change destination from `docs/research/trail/deep-reviews/agent-transcripts/` to `transcripts_dir()` from `paths.py`. File a GitHub Issue for future transcript parsing/self-learning integration.

### Phase 5: Update all consumers

Replace hardcoded `.generated` references with `paths.py` imports:

- `src/mde/debate/invoke.py` — uses `Path.cwd()/.generated/debate` and `.generated/gemini`; replace with `generated_dir() / "debate"` and `generated_dir() / "gemini"`
- `src/mde/dream/extract.py` — use `learnings_dir()`, `dream_dir()`
- `src/mde/dream/state.py` — use `dream_dir()`
- `src/mde/hooks/context_snapshot.py` — writes `.generated/context-snapshot.json`; move to `context_dir() / "context-snapshot.json"` (context_dir is a directory for future multi-snapshot support)
- `src/mde/hooks/post_compact.py` — writes `.generated/compact-events.jsonl`; use `generated_dir() / "compact-events.jsonl"` (single file, no dedicated env var needed)
- `src/mde/hooks/_remember_local.py` — has inline `_remember_dir()`; replace entire function with import of `remember_dir()` from paths.py
- `src/mde/hooks/remember_precompact.py` — use `remember_dir()`
- `src/mde/hooks/save_memory_on_clear.py` — use `remember_dir()`
- `.mise.toml` tasks (schema:fetch-upstream) — use `$MDE_DIR_SCHEMAS`
- Agent definitions — reference `.claude/rules/generated-paths.md`

**Validator integration** (`src/mde/validate/__init__.py`):
- Add `paths_only: bool = False` parameter to `run_validators()` and `validate_all()`
- Add `--paths` flag to CLI (consistent with `--plugins`, `--brew`, etc.)
- Insert `result.merge(validate_paths())` in the full-mode block after `validate_structural()`

**Quality gate integration** (`src/mde/quality.py`):
- New lint checks run via `subprocess.run` — `jscpd` paths must be absolute (use `str(repo_root / "src/mde/")`) to work correctly in worktree contexts where CWD may differ

### Phase 6: Create reference doc

**File**: `.claude/rules/generated-paths.md`

Lists every env var, default value, purpose, and consumers. Agent defs and policy rules reference this instead of hardcoding paths.

### Phase 7: Delete stale transcripts

Delete 287 files from `docs/research/trail/deep-reviews/agent-transcripts/`.

## Validation Design

### New tools to install (mise global config)

```toml
[tools]
"pipx:vulture" = "latest"         # Runtime dead code detection
"pipx:import-linter" = "latest"   # Circular import detection
# jscpd already installed via npm
```

### Quality gate additions (`quality.py`)

Add to `_LINT_CHECKS`:

```python
("jscpd", ["jscpd", "src/mde/", "--min-lines", "6", "--min-tokens", "50",
           "--format", "python", "--threshold", "0", "--reporters", "console"],
 "Duplication check"),
("vulture", ["uv", "run", "vulture", "src/mde/", "--min-confidence", "80"],
 "Dead code (runtime)"),
("import-linter", ["uv", "run", "lint-imports"],
 "Circular import check"),
```

### Explicit complexity thresholds (`pyproject.toml`)

```toml
[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-branches = 12
max-returns = 6
max-statements = 50

[tool.importlinter]
root_packages = ["mde"]

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

### Unit tests (`tests/mde/test_paths.py`)

Tests construct `MdePaths` directly (no monkeypatching env vars needed):

```python
from pathlib import Path
from mde.lib.paths import MdePaths

# ── Cascading defaults ──

def test_cascade_from_project_dir(tmp_path: Path) -> None:
    """All paths derive from project_dir when nothing else is set."""
    paths = MdePaths(project_dir=tmp_path)
    assert paths.generated_dir == tmp_path / ".generated"
    assert paths.dir_remember == tmp_path / ".generated" / "remember"
    assert paths.dir_learnings == tmp_path / ".generated" / "learnings"
    assert paths.dir_transcripts == tmp_path / ".generated" / "transcripts"
    assert paths.dir_schemas == tmp_path / ".generated" / "schemas"
    assert paths.dir_reports == tmp_path / ".generated" / "reports"
    assert paths.dir_context == tmp_path / ".generated" / "context"
    assert paths.dir_dream == tmp_path / ".generated" / "dream"

def test_override_generated_dir_cascades(tmp_path: Path) -> None:
    """Overriding generated_dir cascades to all child dirs."""
    custom_gen = tmp_path / "custom-gen"
    paths = MdePaths(project_dir=tmp_path, generated_dir=custom_gen)
    assert paths.dir_remember == custom_gen / "remember"
    assert paths.dir_dream == custom_gen / "dream"

def test_override_individual_child(tmp_path: Path) -> None:
    """Individual child dirs can be overridden without affecting siblings."""
    paths = MdePaths(project_dir=tmp_path, dir_remember=tmp_path / "my-remember")
    assert paths.dir_remember == tmp_path / "my-remember"
    assert paths.dir_learnings == tmp_path / ".generated" / "learnings"  # unaffected

# ── Env var loading ──

def test_env_var_loading(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """MDE_* env vars populate the model."""
    monkeypatch.setenv("MDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("MDE_GENERATED_DIR", str(tmp_path / "gen"))
    paths = MdePaths()
    assert paths.project_dir == tmp_path
    assert paths.generated_dir == tmp_path / "gen"
    assert paths.dir_remember == tmp_path / "gen" / "remember"

def test_fallback_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env vars, project_dir detected via git."""
    for key in list(os.environ):
        if key.startswith("MDE_"):
            monkeypatch.delenv(key, raising=False)
    paths = MdePaths()
    assert paths.project_dir is not None
    assert paths.generated_dir == paths.project_dir / ".generated"

# ── Type safety ──

def test_all_fields_are_path(tmp_path: Path) -> None:
    """Every path field returns a pathlib.Path instance."""
    paths = MdePaths(project_dir=tmp_path)
    for name in ("project_dir", "generated_dir", "dir_remember", "dir_learnings",
                 "dir_transcripts", "dir_schemas", "dir_reports", "dir_context", "dir_dream"):
        assert isinstance(getattr(paths, name), Path), f"{name} is not a Path"

# ── Backward compatibility ──

def test_no_duplicate_repo_root() -> None:
    """_common.py must import repo_root from paths.py, not redefine it."""
    from mde.hooks._common import repo_root as common_rr
    from mde.lib.paths import repo_root as paths_rr
    assert common_rr is paths_rr

def test_repo_root_alias() -> None:
    """repo_root() returns same value as get_paths().project_dir."""
    from mde.lib.paths import get_paths, repo_root
    assert repo_root() == get_paths().project_dir

# ── Consumer integration ──

def test_persist_transcripts_uses_transcripts_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """persist_transcripts hook writes to get_paths().dir_transcripts, not hardcoded path."""
```

### Validator (`src/mde/validate/paths.py`)

```python
def validate_paths(root: Path | None = None) -> ValidationResult:
    """Validate centralized path management is correctly configured."""

    # Check 1: paths.env-var-missing (WARNING)
    # MDE_GENERATED_DIR should be in env when mise is active

    # Check 2: paths.dir-missing (WARNING)
    # env var values should point to existing directories

    # Check 3: paths.remember-symlink (ERROR)
    # .remember must be symlink to $MDE_DIR_REMEMBER

    # Check 4: paths.mise-global-missing (ERROR)
    # ~/.config/mise/config.toml must contain MDE_PROJECT_DIR

    # Check 5: paths.chezmoi-template-missing (ERROR)
    # home/dot_config/mise/config.toml.tmpl must contain MDE_PROJECT_DIR

    # Check 6: paths.hardcoded-ref (WARNING)
    # No .py file (except paths.py) should contain literal ".generated"

    # Check 7: paths.reference-doc-missing (ERROR)
    # .claude/rules/generated-paths.md must exist and list all env vars

    # Check 8: paths.composition-violation (ERROR)
    # In chezmoi template: only MDE_PROJECT_DIR may use {{ .chezmoi.* }}
    # All other MDE_DIR_* vars must compose from $MDE_PROJECT_DIR or $MDE_GENERATED_DIR
    # Detects: hardcoded paths, direct chezmoi template usage in child vars

    # Check 9: paths.env-shell-expand-missing (ERROR)
    # Global mise config must have env_shell_expand = true for $VAR composition to work
```

### Validator tests (`tests/mde/test_validate_paths.py`)

```python
def test_validate_paths_all_correct(tmp_path, monkeypatch):
def test_validate_paths_missing_env_var(tmp_path, monkeypatch):
def test_validate_paths_broken_symlink(tmp_path):
def test_validate_paths_hardcoded_ref(tmp_path):
def test_validate_paths_missing_reference_doc(tmp_path):
def test_validate_paths_mise_global_missing(tmp_path):
def test_validate_paths_chezmoi_template_missing(tmp_path):
def test_validate_paths_composition_violation(tmp_path):
    """ERROR if child MDE vars use chezmoi template instead of $MDE_GENERATED_DIR."""
def test_validate_paths_env_shell_expand_missing(tmp_path):
    """ERROR if global mise config missing env_shell_expand = true."""
```

### Complete quality gate (post-implementation)

| # | Check | Tool | What it catches |
|---|---|---|---|
| 1 | ruff-check | ruff | Lint rules (ALL enabled), dead code (F401/F841/ERA/ARG) |
| 2 | ruff-format | ruff | Code formatting |
| 3 | ty | ty | Type inference errors |
| 4 | pyright | pyright | Strict type checking |
| 5 | jscpd | jscpd | Code duplication (clone detection) |
| 6 | vulture | vulture | Runtime dead code (unused functions/classes) |
| 7 | import-linter | lint-imports | Circular import detection |
| 8 | pytest | pytest | Unit + validator tests |
| 9 | mde-validate | in-process | Runtime config checks (paths, plugins, etc.) |

## Suppression Policy

### No-suppression-without-justification rule

No linter, static analyzer, or sanitizer finding may be suppressed (via `ignore`, `noqa`, `type: ignore`, `per-file-ignores`, `--exclude`, or any equivalent mechanism) unless **both** conditions are met:

1. **Research gate**: The agent/developer must document in the PR description:
   - What the finding says
   - What code/docs were reviewed to find a solution
   - Why the finding cannot be resolved (with specific technical justification)
   - Links to upstream issues if the tool has a false positive

2. **Human approval gate**: A human must explicitly approve the suppression in the PR review. The suppression comment must include:
   - The rule ID being suppressed
   - A one-line justification referencing the research
   - The human approver (e.g., `# noqa: PLR0913 — approved by @ray-manaloto: kwargs pass-through`)

### Existing suppressions

All current `ignore` entries in `pyproject.toml` have inline comments explaining the rationale. These are grandfathered but subject to periodic review — the `validate_paths` hardcoded-reference scanner serves as the model for future drift-detection validators.

### Enforcement

- Pre-commit hook (`hk.pkl`) runs the full quality gate — no `--no-verify` allowed
- CI runs `uv run mde-py quality --strict` — warnings are errors
- The `guard-main-commit` hook prevents direct commits to main

## Rollback

- `chezmoi apply` is atomic per file — if the template has a syntax error, `~/.config/mise/config.toml` is unchanged
- To manually undo: remove `MDE_*` lines from `~/.config/mise/config.toml` and open a new shell
- Run `chezmoi verify` before and after to confirm no unintended changes
- Python code fallbacks mean `paths.py` works without env vars — removing them doesn't break functionality, just loses the centralization benefit
- If `import-linter` or `vulture` fail on existing code during initial integration, fix the findings (not suppress) per suppression policy; if truly unfixable, use the research + human approval gates

## Follow-up Issues

1. **Transcript parsing for self-learning** (new GitHub Issue): Parse agent transcripts in `.generated/transcripts/` for self-improvement patterns; integrate with dream pipeline's signal sources
2. **Periodic suppression audit**: Review all `ignore`/`noqa` entries quarterly; remove any that can now be resolved

## Files Changed

| File | Change |
|---|---|
| `home/dot_config/mise/config.toml.tmpl` | Add MDE_* env vars to `[env]` |
| `home/dot_config/mise/config.toml.tmpl` | Add vulture, import-linter to `[tools]` |
| `src/mde/lib/paths.py` | Add env-var-aware path functions |
| `src/mde/hooks/_common.py` | Import repo_root from paths.py |
| `src/mde/hooks/persist_transcripts.py` | Redirect to transcripts_dir() |
| `src/mde/debate/invoke.py` | Use generated_dir() for debate/gemini paths |
| `src/mde/dream/extract.py` | Use paths.py functions |
| `src/mde/dream/state.py` | Use paths.py functions |
| `src/mde/hooks/context_snapshot.py` | Use paths.py functions |
| `src/mde/hooks/post_compact.py` | Use paths.py functions |
| `src/mde/hooks/_remember_local.py` | Use paths.py functions |
| `src/mde/hooks/remember_precompact.py` | Use paths.py functions |
| `src/mde/hooks/save_memory_on_clear.py` | Use paths.py functions |
| `.mise.toml` | Update schema:fetch-upstream task |
| `src/mde/quality.py` | Add jscpd, vulture, import-linter checks |
| `src/mde/validate/paths.py` | New validator |
| `src/mde/validate/__init__.py` | Register validate_paths |
| `pyproject.toml` | Add mccabe/pylint thresholds, importlinter config |
| `.claude/rules/generated-paths.md` | New reference doc |
| `.claude/rules/no-warning-suppression.md` | Add research + human gates |
| `tests/mde/test_paths.py` | New unit tests |
| `tests/mde/test_validate_paths.py` | New validator tests |
| Agent defs (multiple) | Reference generated-paths.md |
| `CLAUDE.md` / `AGENTS.md` | Update .generated references |
| `docs/research/trail/deep-reviews/agent-transcripts/` | Delete 287 stale files |
