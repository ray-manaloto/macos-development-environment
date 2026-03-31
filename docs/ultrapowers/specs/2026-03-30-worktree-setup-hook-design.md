# WorktreeCreate Setup Hook

**Date**: 2026-03-30
**Status**: Design
**Branch**: `feat/worktree-setup-hook`

## Problem

Git worktrees created by Claude Code (via `--worktree` flag or `isolation: "worktree"` in subagents) fail in three ways:

1. **VIRTUAL_ENV mismatch** — Shell inherits `VIRTUAL_ENV` from the parent session. The worktree has its own `.venv`. uv warns: `VIRTUAL_ENV=... does not match the project environment path .venv and will be ignored`. Violates zero-warning policy.
2. **mise trust required** — `.mise.toml` in the worktree is untrusted. All subprocess invocations via mise fail until `mise trust <worktree-path>` runs. Blocks all tool execution.
3. **uv sync needed** — The worktree has no `.venv` until `uv sync` runs. Subagents that try to execute `uv run ...` fail immediately.

These issues are documented in auto-memory (#1220, #1221, #1513) and `.claude/rules/worktree-pr-workflow.md`.

## Approach: WorktreeCreate hook replacing default behavior

Per official docs, configuring a `WorktreeCreate` hook **replaces** Claude Code's default `git worktree add` entirely. The hook must:
1. Create the git worktree itself
2. Run all environment setup
3. Print the absolute worktree path to stdout

This is the official extension point — designed for exactly this use case.

### Why not SessionStart detection (Approach C)?

SessionStart fires too late — the subagent's process has already started with the inherited `VIRTUAL_ENV`, and `uv run` commands will fail before SessionStart hooks execute. The setup must happen *before* the first command.

### Why not inline bash (Approach B)?

Violates no-shell-scripts policy, can't be tested, fragile quoting, no error handling or tracing.

### Relationship to ultrapowers `/using-git-worktrees` skill

These are complementary, not conflicting:
- **`/using-git-worktrees`** — Manual skill invoked by user. Runs `git worktree add` + setup. Used for planned feature branches.
- **`WorktreeCreate` hook** — Automatic system-level hook. Fires when Claude Code itself creates worktrees via `isolation: "worktree"` or `--worktree`. The skill never runs in this path.

The hook catches the automatic cases that the skill cannot address.

## Hook Specification (from official docs)

### WorktreeCreate

- **Trigger**: `claude --worktree` flag OR subagent `isolation: "worktree"`
- **Replaces default**: Yes — Claude Code does NOT run `git worktree add` when this hook is configured
- **Stdin JSON**:
  ```json
  {
    "session_id": "abc123",
    "transcript_path": "/Users/.../.claude/projects/.../session.jsonl",
    "cwd": "/Users/.../macos-development-environment",
    "hook_event_name": "WorktreeCreate",
    "name": "feature-auth"
  }
  ```
- **Required stdout**: Absolute path to the created worktree directory
- **Exit code**: 0 = success, non-zero = worktree creation fails
- **`.worktreeinclude` NOT processed**: Must be handled inside the hook

### WorktreeRemove

- **Not needed** for our git-based workflow — Claude Code handles `git worktree remove` automatically
- Only required for non-git VCS (SVN, Perforce)

## Implementation

### File: `src/mde/hooks/worktree_create.py`

```python
"""Create and set up git worktrees for Claude Code subagents.

Replaces Claude Code's default git worktree behavior. Creates the worktree,
trusts mise config, syncs uv venv, and copies .worktreeinclude files.
Always exits 0 on success (prints path to stdout) or non-zero on failure.

Triggered by: claude --worktree OR subagent isolation: "worktree"
"""

from __future__ import annotations

__hook_meta__ = {
    "help": "WorktreeCreate: git worktree + mise trust + uv sync",
    "entry": "worktree_create",
}
```

The `worktree_create()` function:

1. **Parse stdin** — Read JSON, extract `name` and `cwd`
2. **Determine worktree path** — `<cwd>/.claude/worktrees/<name>`
3. **Determine branch name** — `worktree-<name>-<session_id[:8]>` (session_id from stdin ensures uniqueness across parallel team worktree creations)
4. **Create git worktree** — `git worktree add <path> -b <branch_name> HEAD`
   - Base from `HEAD` (current branch tip), NOT `origin/HEAD` — subagents need the user's latest work including unpushed commits (debate finding: Gemini HIGH)
   - If branch already exists, use `git worktree add <path> <branch_name>` (checkout existing, NO `-B` force-reset — data loss risk)
   - If worktree path already exists, exit non-zero with descriptive error
5. **Trust mise config** — `mise trust <path>` (idempotent, safe to run always)
6. **Sync Python venv** — `uv sync --frozen` in the worktree directory with `VIRTUAL_ENV` **removed** from env dict
   - In Python: `env = os.environ.copy(); env.pop("VIRTUAL_ENV", None)` — do NOT set to empty string
   - `--frozen` skips dependency resolution (uses existing lockfile) — critical for hook timeout safety
   - This creates `.venv/` in the worktree
   - If `pyproject.toml` exists in repo root and `uv sync` fails → exit non-zero (Python project requires working venv)
   - If no `pyproject.toml` → skip uv sync entirely (not a Python project)
7. **Recreate .remember symlink** — If `.remember` is a symlink in the repo root, recreate it in the worktree pointing to the same target (`.generated/remember/`). Gitignored files like `.remember` are NOT copied by git worktree (debate finding: Gemini HIGH).
8. **Copy .worktreeinclude files** — Parse `.worktreeinclude` in repo root, copy matching files to worktree
9. **Print path to stdout** — The absolute worktree path, nothing else on stdout
10. **All diagnostic output goes to stderr** — stdout is reserved for the path
   - **Critical**: ALL subprocess calls must use `stdout=subprocess.DEVNULL` or `stdout=subprocess.PIPE` (forwarded to stderr). Any subprocess output leaking to stdout corrupts the path Claude Code reads.

### Error handling

- If `git worktree add` fails → exit non-zero (creation fails, Claude Code reports error)
- If `mise trust` fails → log warning to stderr, continue (non-critical)
- If `uv sync --frozen` fails AND `pyproject.toml` exists → exit non-zero (Python project requires venv)
- If `uv sync --frozen` fails AND no `pyproject.toml` → skip (not a Python project)
- If `.remember` symlink recreation fails → log warning to stderr, continue
- If `.worktreeinclude` parsing/copying fails → log warning to stderr, continue

### settings.json wiring

```json
{
  "hooks": {
    "WorktreeCreate": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "uv run mde-py hooks worktree-create"
          }
        ]
      }
    ]
  }
}
```

### .worktreeinclude handling

The built-in `.worktreeinclude` logic is disabled when a WorktreeCreate hook is configured. Our hook reimplements it:

1. Read `.worktreeinclude` from repo root (if exists)
2. Parse as gitignore-style patterns (one per line, `#` comments, `!` negation)
3. For each matching file in the repo root, copy to the worktree at the same relative path
4. Common entries: `.env`, `.env.local`, `.generated/` symlinks

Use `fnmatch` from stdlib for pattern matching (handles `*`, `?`, `[...]` patterns). This covers 90% of real `.worktreeinclude` files. If full gitignore semantics are ever needed (negations, `**` globbing, anchored paths), add `pathspec` as an explicit `[project.dependencies]` entry — do NOT rely on it as a transitive dep of ruff/black.

## Testing

### Unit tests: `tests/mde/test_hook_worktree_create.py`

```python
def test_creates_worktree_at_expected_path(tmp_path):
    """Worktree created at <cwd>/.claude/worktrees/<name>."""

def test_trusts_mise_config(tmp_path):
    """mise trust called on worktree path after creation."""

def test_uv_sync_unsets_virtual_env(tmp_path):
    """uv sync runs with VIRTUAL_ENV unset."""

def test_copies_worktreeinclude_files(tmp_path):
    """Files matching .worktreeinclude patterns copied to worktree."""

def test_prints_path_to_stdout(tmp_path, capsys):
    """Only the absolute path printed to stdout."""

def test_stderr_for_diagnostics(tmp_path, capsys):
    """All non-path output goes to stderr."""

def test_missing_worktreeinclude_is_fine(tmp_path):
    """No error when .worktreeinclude doesn't exist."""

def test_git_failure_returns_nonzero(tmp_path):
    """Non-zero exit when git worktree add fails."""

def test_mise_failure_is_nonfatal(tmp_path):
    """Continues when mise trust fails (logs warning)."""

def test_uv_failure_is_nonfatal(tmp_path):
    """Continues when uv sync fails (logs warning)."""

def test_stdout_contains_only_the_path(tmp_path, capsys):
    """stdout is exactly one line containing only the absolute path."""

def test_missing_origin_head_exits_nonzero(tmp_path):
    """Non-zero exit with clear error when origin/HEAD is unset."""

def test_existing_branch_reused_without_force_reset(tmp_path):
    """Existing worktree-<name> branch checked out, not force-reset with -B."""

def test_remember_symlink_recreated(tmp_path):
    """If .remember is a symlink in repo root, it's recreated in worktree."""

def test_branch_name_includes_session_id(tmp_path):
    """Branch name is worktree-<name>-<session_id[:8]> for uniqueness."""

def test_uv_sync_fatal_for_python_project(tmp_path):
    """Non-zero exit when uv sync fails and pyproject.toml exists."""

def test_uv_sync_skipped_for_non_python(tmp_path):
    """uv sync skipped entirely when no pyproject.toml."""

def test_branches_from_head_not_origin(tmp_path):
    """Worktree bases from HEAD (current branch), not origin/HEAD."""
```

Tests mock subprocess calls — these are unit tests, not integration tests.

### Integration test (marked `@pytest.mark.integration`)

```python
def test_full_worktree_lifecycle(tmp_path):
    """Create worktree, verify mise trusted, verify .venv exists, cleanup."""

def test_virtual_env_resolved_in_worktree(tmp_path):
    """uv run python reports worktree .venv path, not parent's."""
```

## Files Changed

| File | Change |
|------|--------|
| `src/mde/hooks/worktree_create.py` | New hook module |
| `.claude/settings.json` | Add WorktreeCreate hook wiring |
| `.worktreeinclude` | Create with `.env` and `.env.local` patterns |
| `.gitignore` | Add line `.claude/worktrees/` |
| `pyproject.toml` | Add T201 per-file-ignore for `src/mde/hooks/worktree_create.py` |
| `.claude/rules/worktree-pr-workflow.md` | Update to reference the hook |
| `tests/mde/test_hook_worktree_create.py` | New unit tests (13 tests) |
| `CLAUDE.md` or `AGENTS.md` | Document the hook |

## Rollback

- Remove `WorktreeCreate` entry from `.claude/settings.json` → Claude Code reverts to default `git worktree add` behavior
- The hook module stays in `src/mde/hooks/` but is inactive without the settings.json wiring
- No data migration needed — worktrees are transient

## Follow-up

1. **WorktreeRemove hook** — Not needed now (git-based), but could add for cleanup logging/archival later
2. **Agent teams worktree coordination** — Agent teams don't have built-in per-teammate worktree isolation. If teams become stable (currently experimental, v2.1.32+), consider a `TeamCreate` hook that provisions worktrees per teammate.
3. **Custom base branch** — Currently uses `HEAD` (user's current branch). Could add a config option to override the base ref for specific use cases.
