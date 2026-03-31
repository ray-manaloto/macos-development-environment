# WorktreeCreate Setup Hook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use ultrapowers:subagent-driven-development (recommended) or ultrapowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Claude Code's default git worktree creation with an enhanced hook that automatically runs `mise trust`, `uv sync --frozen`, recreates `.remember` symlink, and copies `.worktreeinclude` files — fixing all known worktree issues for subagents and `--worktree` sessions.

**Architecture:** A single Python hook module (`src/mde/hooks/worktree_create.py`) following the `__hook_meta__` auto-discovery pattern. The hook reads `name` and `session_id` from stdin JSON, creates the git worktree, runs environment setup, and prints the absolute path to stdout. All subprocess output is redirected to stderr/DEVNULL to protect stdout purity.

**Tech Stack:** Python 3.12, `subprocess` (stdout isolation), `fnmatch` (pattern matching), `shutil` (file copying), git worktrees, mise, uv

**Spec:** `docs/ultrapowers/specs/2026-03-30-worktree-setup-hook-design.md`
**Research:** `docs/research/trail/deep-reviews/worktree-hook-research-brief.md`

**Skills:** @ultrapowers-dev:python-best-practices, @ultrapowers-dev:testing-tdd, @plugin-dev:hook-development, @astral:ruff, @astral:ty, @astral:uv

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `src/mde/hooks/worktree_create.py` | Create | Hook module: create worktree + setup environment |
| `tests/mde/test_hook_worktree_create.py` | Create | 19 unit tests + 2 integration tests |
| `.claude/settings.json` | Modify | Add `WorktreeCreate` hook entry |
| `.worktreeinclude` | Create | Patterns for files to copy into worktrees |
| `.gitignore` | Modify | Add `.claude/worktrees/` |
| `pyproject.toml` | Modify | Add T201 per-file-ignore |
| `.claude/rules/worktree-pr-workflow.md` | Modify | Reference the new hook |

---

## Task 1: Create feature branch + scaffold

**Files:**
- Modify: `.gitignore`
- Modify: `pyproject.toml`
- Create: `.worktreeinclude`

- [ ] **Step 1: Create feature branch**

```bash
git checkout -b feat/worktree-setup-hook
```

- [ ] **Step 2: Verify `.claude/worktrees/` is in `.gitignore`**

Check if `.claude/worktrees/` is already present:
```bash
grep -q 'claude/worktrees' .gitignore && echo "Already present" || echo ".claude/worktrees/" >> .gitignore
```
Note: This line likely already exists. Only add if missing.

- [ ] **Step 3: Add T201 per-file-ignore to `pyproject.toml`**

In `[tool.ruff.lint.per-file-ignores]`, add:
```toml
"src/mde/hooks/worktree_create.py" = ["T201"]
```

This is needed because the hook MUST print the worktree path to stdout — that's how Claude Code reads the result.

- [ ] **Step 4: Create `.worktreeinclude`**

```
# Files to copy into new worktrees (gitignore syntax)
# These are gitignored files that subagents may need
.env
.env.local
```

- [ ] **Step 5: Run quality gate**

```bash
uv run mde-py quality
```
Expected: All checks pass.

- [ ] **Step 6: Commit**

```bash
git add .gitignore pyproject.toml .worktreeinclude
git commit -m "feat: scaffold worktree-setup-hook (gitignore, T201, worktreeinclude)"
```

---

## Task 2: Write failing tests — core creation (TDD red)

**Files:**
- Create: `tests/mde/test_hook_worktree_create.py`

- [ ] **Step 1: Write test file with 7 core tests**

```python
"""Tests for WorktreeCreate hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


def _make_stdin(name: str = "test-wt", session_id: str = "abc12345def", cwd: str | None = None) -> str:
    """Create a JSON string mimicking WorktreeCreate stdin."""
    return json.dumps({
        "session_id": session_id,
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": cwd or "/tmp/repo",
        "hook_event_name": "WorktreeCreate",
        "name": name,
    })


class TestWorktreeCreation:
    """Core worktree creation behavior."""

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_creates_worktree_at_expected_path(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Worktree created at <cwd>/.claude/worktrees/<name>."""
        from mde.hooks.worktree_create import _create_worktree

        cwd = tmp_path / "repo"
        cwd.mkdir()
        expected_path = cwd / ".claude" / "worktrees" / "feat-auth"

        mock_run.return_value = (0, "")
        result = _create_worktree(name="feat-auth", session_id="abc12345", cwd=cwd)

        assert result == expected_path
        # Verify git worktree add was called
        git_call = mock_run.call_args_list[0]
        assert "git" in git_call.args[0][0]
        assert "worktree" in git_call.args[0]
        assert str(expected_path) in git_call.args[0]

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_branch_name_includes_session_id(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Branch name is worktree-<name>-<session_id[:8]> for uniqueness."""
        from mde.hooks.worktree_create import _create_worktree

        cwd = tmp_path / "repo"
        cwd.mkdir()
        mock_run.return_value = (0, "")

        _create_worktree(name="feat-auth", session_id="abc12345def", cwd=cwd)

        git_call = mock_run.call_args_list[0]
        cmd = git_call.args[0]
        # Branch should contain session_id prefix
        assert any("worktree-feat-auth-abc12345" in str(arg) for arg in cmd)

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_branches_from_head_not_origin(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Worktree bases from HEAD (current branch), not origin/HEAD."""
        from mde.hooks.worktree_create import _create_worktree

        cwd = tmp_path / "repo"
        cwd.mkdir()
        mock_run.return_value = (0, "")

        _create_worktree(name="test", session_id="abc12345", cwd=cwd)

        git_call = mock_run.call_args_list[0]
        cmd = git_call.args[0]
        assert "HEAD" in cmd
        assert "origin/HEAD" not in " ".join(cmd)

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_git_failure_returns_none(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Returns None when git worktree add fails."""
        from mde.hooks.worktree_create import _create_worktree

        mock_run.return_value = (128, "fatal: already exists")

        result = _create_worktree(name="bad", session_id="abc12345", cwd=tmp_path)
        assert result is None

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_existing_path_returns_none(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Returns None when worktree path already exists."""
        from mde.hooks.worktree_create import _create_worktree

        wt_path = tmp_path / ".claude" / "worktrees" / "existing"
        wt_path.mkdir(parents=True)

        result = _create_worktree(name="existing", session_id="abc12345", cwd=tmp_path)
        assert result is None
        mock_run.assert_not_called()


class TestEnvironmentSetup:
    """mise trust and uv sync behavior."""

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_trusts_mise_config(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """mise trust called on worktree path after creation."""
        from mde.hooks.worktree_create import _setup_environment

        mock_run.return_value = (0, "")
        _setup_environment(worktree_path=tmp_path, repo_root=tmp_path.parent)

        mise_calls = [c for c in mock_run.call_args_list if "mise" in str(c)]
        assert len(mise_calls) >= 1
        assert "trust" in str(mise_calls[0])

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_uv_sync_removes_virtual_env(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """uv sync runs with VIRTUAL_ENV removed from env dict."""
        from mde.hooks.worktree_create import _setup_environment

        # Create pyproject.toml so uv sync is attempted
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        mock_run.return_value = (0, "")

        _setup_environment(worktree_path=tmp_path, repo_root=tmp_path.parent)

        uv_calls = [c for c in mock_run.call_args_list if "uv" in str(c)]
        assert len(uv_calls) >= 1
        # Check env kwarg does NOT contain VIRTUAL_ENV
        env_arg = uv_calls[0].kwargs.get("env", {})
        assert "VIRTUAL_ENV" not in env_arg
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/mde/test_hook_worktree_create.py -v
```
Expected: ImportError — `mde.hooks.worktree_create` doesn't exist yet.

- [ ] **Step 3: Commit failing tests**

```bash
git add tests/mde/test_hook_worktree_create.py
git commit -m "test: add WorktreeCreate hook core tests (red phase)"
```

---

## Task 3: Implement core hook module (TDD green)

**Files:**
- Create: `src/mde/hooks/worktree_create.py`

- [ ] **Step 1: Create the hook module**

```python
"""Create and set up git worktrees for Claude Code subagents.

Replaces Claude Code's default git worktree behavior. Creates the worktree,
trusts mise config, syncs uv venv, recreates .remember symlink, and copies
.worktreeinclude files. Prints the absolute worktree path to stdout.

Triggered by: claude --worktree OR subagent isolation: "worktree"
"""

from __future__ import annotations

import fnmatch
import os
import shutil
import subprocess
import sys
from pathlib import Path

from mde.log import logger

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "WorktreeCreate: git worktree + mise trust + uv sync",
    "entry": "worktree_create",
}

_GIT_ENV = {
    k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"
} | {"GIT_TERMINAL_PROMPT": "0"}


def _run_cmd(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> tuple[int, str]:
    """Run a command with stdout suppressed (goes to DEVNULL).

    Returns (returncode, stderr_text). ALL stdout is suppressed to protect
    the hook's stdout channel which is reserved for the worktree path.
    """
    result = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
        cwd=cwd,
        env=env or _GIT_ENV,
    )
    return result.returncode, result.stderr


def _create_worktree(
    *,
    name: str,
    session_id: str,
    cwd: Path,
) -> Path | None:
    """Create a git worktree. Returns the path or None on failure."""
    worktree_path = cwd / ".claude" / "worktrees" / name
    branch_name = f"worktree-{name}-{session_id[:8]}"

    if worktree_path.exists():
        print(
            f"ERROR: worktree path already exists: {worktree_path}",
            file=sys.stderr,
        )
        return None

    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    # Try creating with new branch from HEAD
    rc, stderr = _run_cmd(
        ["git", "worktree", "add", str(worktree_path), "-b", branch_name, "HEAD"],
        cwd=cwd,
    )

    if rc != 0:
        # Branch may already exist — try checking it out without -b
        rc2, stderr2 = _run_cmd(
            ["git", "worktree", "add", str(worktree_path), branch_name],
            cwd=cwd,
        )
        if rc2 != 0:
            print(f"ERROR: git worktree add failed: {stderr2}", file=sys.stderr)
            return None

    logger.bind(hook="worktree_create", path=str(worktree_path), branch=branch_name).info(
        "worktree_created"
    )
    return worktree_path


def _setup_environment(*, worktree_path: Path, repo_root: Path) -> bool:
    """Run post-creation setup. Returns True if critical steps succeeded."""
    # 1. Trust mise config
    rc, stderr = _run_cmd(["mise", "trust", str(worktree_path)], cwd=worktree_path)
    if rc != 0:
        print(f"WARNING: mise trust failed: {stderr}", file=sys.stderr)

    # 2. Sync Python venv (only if this is a Python project — check repo root)
    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)  # Remove, not empty string
        env["GIT_TERMINAL_PROMPT"] = "0"
        rc, stderr = _run_cmd(
            ["uv", "sync", "--frozen"],
            cwd=worktree_path,
            env=env,
        )
        if rc != 0:
            print(f"ERROR: uv sync --frozen failed: {stderr}", file=sys.stderr)
            return False  # Fatal for Python projects

    # 3. Recreate .remember symlink
    remember_src = repo_root / ".remember"
    if remember_src.is_symlink():
        remember_target = remember_src.resolve()
        remember_dst = worktree_path / ".remember"
        try:
            remember_dst.symlink_to(remember_target)
        except OSError as exc:
            print(f"WARNING: .remember symlink failed: {exc}", file=sys.stderr)

    # 4. Copy .worktreeinclude files
    _copy_worktreeinclude(repo_root=repo_root, worktree_path=worktree_path)

    return True


def _copy_worktreeinclude(*, repo_root: Path, worktree_path: Path) -> None:
    """Copy files matching .worktreeinclude patterns from repo root to worktree."""
    include_file = repo_root / ".worktreeinclude"
    if not include_file.exists():
        return

    patterns: list[str] = []
    for line in include_file.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.append(stripped)

    if not patterns:
        return

    for item in repo_root.iterdir():
        rel_name = item.name
        if any(fnmatch.fnmatch(rel_name, pat) for pat in patterns):
            dst = worktree_path / rel_name
            try:
                if item.is_file():
                    shutil.copy2(item, dst)
                elif item.is_dir():
                    shutil.copytree(item, dst, dirs_exist_ok=True)
                logger.bind(file=rel_name).debug("worktreeinclude_copied")
            except OSError as exc:
                print(f"WARNING: copy {rel_name} failed: {exc}", file=sys.stderr)


def worktree_create() -> int:
    """Entry point for the WorktreeCreate hook.

    Reads JSON from stdin, creates worktree, runs setup, prints path to stdout.
    Returns 0 on success, 1 on failure.
    """
    import json

    data = json.load(sys.stdin)
    name = data.get("name", "unnamed")
    session_id = data.get("session_id", "00000000")
    cwd = Path(data.get("cwd", os.getcwd()))

    # Create the worktree
    worktree_path = _create_worktree(name=name, session_id=session_id, cwd=cwd)
    if worktree_path is None:
        return 1

    # Run environment setup
    ok = _setup_environment(worktree_path=worktree_path, repo_root=cwd)
    if not ok:
        # Cleanup failed worktree
        _run_cmd(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=cwd)
        return 1

    # Print the path — this is the ONLY thing that goes to stdout
    print(worktree_path)
    return 0
```

- [ ] **Step 2: Run tests**

```bash
uv run pytest tests/mde/test_hook_worktree_create.py -v
```
Expected: All 7 tests pass.

- [ ] **Step 3: Run quality gate**

```bash
uv run mde-py quality
```
Expected: All checks pass.

- [ ] **Step 4: Commit**

```bash
git add src/mde/hooks/worktree_create.py
git commit -m "feat: implement WorktreeCreate hook (git worktree + mise trust + uv sync)"
```

---

## Task 4: Write remaining tests (TDD red → green)

**Files:**
- Modify: `tests/mde/test_hook_worktree_create.py`

- [ ] **Step 1: Add stdout purity, .remember, .worktreeinclude, and error handling tests**

Append to the test file:

```python
class TestStdoutPurity:
    """Stdout must contain ONLY the worktree path."""

    def test_stdout_contains_only_the_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """stdout is exactly one line containing only the absolute path."""
        from mde.hooks.worktree_create import worktree_create

        wt_path = tmp_path / ".claude" / "worktrees" / "test-wt"
        stdin_data = _make_stdin(name="test-wt", cwd=str(tmp_path))

        with (
            patch("mde.hooks.worktree_create._create_worktree", return_value=wt_path),
            patch("mde.hooks.worktree_create._setup_environment", return_value=True),
            patch("sys.stdin", __class__=type(sys.stdin), read=lambda self: stdin_data),
        ):
            monkeypatch.setattr("sys.stdin", __import__("io").StringIO(stdin_data))
            import io
            captured = io.StringIO()
            monkeypatch.setattr("sys.stdout", captured)

            result = worktree_create()

            assert result == 0
            output = captured.getvalue()
            assert output.strip() == str(wt_path)
            assert len(output.strip().splitlines()) == 1


class TestRememberSymlink:
    """Recreate .remember symlink in worktree."""

    def test_remember_symlink_recreated(self, tmp_path: Path) -> None:
        """If .remember is a symlink in repo root, it's recreated in worktree."""
        from mde.hooks.worktree_create import _setup_environment

        repo = tmp_path / "repo"
        repo.mkdir()
        wt = tmp_path / "worktree"
        wt.mkdir()

        # Create .remember symlink in repo
        target = repo / ".generated" / "remember"
        target.mkdir(parents=True)
        (repo / ".remember").symlink_to(target)
        (wt / "pyproject.toml").write_text("")  # Trigger uv sync path

        with patch("mde.hooks.worktree_create._run_cmd", return_value=(0, "")):
            _setup_environment(worktree_path=wt, repo_root=repo)

        assert (wt / ".remember").is_symlink()
        assert (wt / ".remember").resolve() == target.resolve()


class TestWorktreeInclude:
    """Copy .worktreeinclude-matched files."""

    def test_copies_matching_files(self, tmp_path: Path) -> None:
        """Files matching .worktreeinclude patterns are copied."""
        from mde.hooks.worktree_create import _copy_worktreeinclude

        repo = tmp_path / "repo"
        repo.mkdir()
        wt = tmp_path / "worktree"
        wt.mkdir()

        (repo / ".env").write_text("SECRET=val")
        (repo / ".env.local").write_text("LOCAL=val")
        (repo / "README.md").write_text("not copied")
        (repo / ".worktreeinclude").write_text(".env\n.env.local\n")

        _copy_worktreeinclude(repo_root=repo, worktree_path=wt)

        assert (wt / ".env").read_text() == "SECRET=val"
        assert (wt / ".env.local").read_text() == "LOCAL=val"
        assert not (wt / "README.md").exists()

    def test_missing_worktreeinclude_is_fine(self, tmp_path: Path) -> None:
        """No error when .worktreeinclude doesn't exist."""
        from mde.hooks.worktree_create import _copy_worktreeinclude

        _copy_worktreeinclude(repo_root=tmp_path, worktree_path=tmp_path / "wt")
        # No exception = pass


class TestErrorHandling:
    """Failure behavior."""

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_mise_failure_is_nonfatal(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Continues when mise trust fails."""
        from mde.hooks.worktree_create import _setup_environment

        # mise trust fails, uv sync succeeds
        mock_run.side_effect = [(1, "trust error"), (0, "")]
        result = _setup_environment(worktree_path=tmp_path, repo_root=tmp_path)
        assert result is True  # Non-fatal

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_uv_sync_fatal_for_python_project(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """uv sync failure is fatal when pyproject.toml exists in repo root.

        Note: spec's test_uv_failure_is_nonfatal was superseded by this test.
        The spec's error-handling section says uv failure IS fatal for Python projects.
        """
        from mde.hooks.worktree_create import _setup_environment

        (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
        mock_run.side_effect = [(0, ""), (1, "sync error")]  # mise ok, uv fails

        result = _setup_environment(worktree_path=tmp_path, repo_root=tmp_path)
        assert result is False  # Fatal

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_uv_sync_skipped_for_non_python(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """uv sync skipped when no pyproject.toml."""
        from mde.hooks.worktree_create import _setup_environment

        mock_run.return_value = (0, "")
        _setup_environment(worktree_path=tmp_path, repo_root=tmp_path)

        # Only mise trust called, no uv sync
        cmds = [str(c) for c in mock_run.call_args_list]
        assert any("mise" in c for c in cmds)
        assert not any("uv" in c for c in cmds)

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_git_failure_returns_nonzero(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Non-zero exit when git worktree add fails (both attempts)."""
        from mde.hooks.worktree_create import _create_worktree

        mock_run.return_value = (128, "fatal: error")
        result = _create_worktree(name="bad", session_id="abc12345", cwd=tmp_path)
        assert result is None

    def test_stderr_for_diagnostics(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """All non-path output goes to stderr, not stdout."""
        from mde.hooks.worktree_create import _setup_environment

        with patch("mde.hooks.worktree_create._run_cmd", return_value=(1, "some error")):
            _setup_environment(worktree_path=tmp_path, repo_root=tmp_path)

        captured = capsys.readouterr()
        assert captured.out == ""  # Nothing on stdout
        # Warnings go to stderr
        assert "WARNING" in captured.err or captured.err == ""

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_existing_branch_reused_without_force_reset(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """If -b fails (branch exists), fallback checks out existing branch without -B.

        Note: if the existing branch is stale (diverged from HEAD), the user is
        responsible — this is the intentional tradeoff to avoid data loss from -B reset.
        """
        from mde.hooks.worktree_create import _create_worktree

        # First attempt (-b) fails, second (checkout existing) succeeds
        mock_run.side_effect = [(128, "already exists"), (0, "")]
        result = _create_worktree(name="existing", session_id="abc12345", cwd=tmp_path)

        assert result is not None
        # Verify second call does NOT contain -b or -B
        second_call = mock_run.call_args_list[1]
        cmd = second_call.args[0]
        assert "-b" not in cmd
        assert "-B" not in cmd
```

- [ ] **Step 2: Run all tests**

```bash
uv run pytest tests/mde/test_hook_worktree_create.py -v
```
Expected: All pass (implementation from Task 3 covers these behaviors).

- [ ] **Step 3: Quality gate**

```bash
uv run mde-py quality
```

- [ ] **Step 4: Commit**

```bash
git add tests/mde/test_hook_worktree_create.py
git commit -m "test: add full test suite for WorktreeCreate hook (20 tests)"
```

---

## Task 5: Wire the hook in settings.json

**Files:**
- Modify: `.claude/settings.json`

- [ ] **Step 1: Add WorktreeCreate hook entry**

Add to the `"hooks"` object in `.claude/settings.json`:

```json
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
```

Note: No `matcher` field — WorktreeCreate hooks don't use matchers (per official docs).

- [ ] **Step 2: Verify JSON is valid**

```bash
python3 -c "import json; json.load(open('.claude/settings.json'))"
```
Expected: No error.

- [ ] **Step 3: Run full test suite**

```bash
uv run pytest tests/ -x -q -m "not integration"
```
Expected: All pass.

- [ ] **Step 4: Quality gate**

```bash
uv run mde-py quality
```

- [ ] **Step 5: Commit**

```bash
git add .claude/settings.json
git commit -m "feat: wire WorktreeCreate hook in settings.json"
```

---

## Task 6: Update documentation

**Files:**
- Modify: `.claude/rules/worktree-pr-workflow.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Update worktree-pr-workflow.md**

Add a section referencing the hook:

```markdown
## Automatic Worktree Setup (WorktreeCreate hook)

When Claude Code creates worktrees (via `--worktree` or `isolation: "worktree"`),
the `worktree_create` hook automatically:
1. Creates the git worktree branching from HEAD
2. Runs `mise trust` on the worktree path
3. Runs `uv sync --frozen` with VIRTUAL_ENV unset
4. Recreates the `.remember` symlink
5. Copies `.worktreeinclude` files

This replaces Claude Code's default behavior. To disable: remove the
`WorktreeCreate` entry from `.claude/settings.json`.
```

Remove the old "VIRTUAL_ENV warning is benign" note since it's now fixed.

- [ ] **Step 2: Update AGENTS.md hooks section**

Add `worktree-create (WorktreeCreate)` to the hooks list in the Architecture section.

- [ ] **Step 3: Quality gate**

```bash
uv run mde-py quality
```

- [ ] **Step 4: Commit**

```bash
git add .claude/rules/worktree-pr-workflow.md AGENTS.md
git commit -m "docs: document WorktreeCreate hook in rules and AGENTS.md"
```

---

## Task 7: Final verification + push

- [ ] **Step 1: Run full quality gate**

```bash
uv run mde-py quality
```
Expected: All checks pass.

- [ ] **Step 2: Run full test suite with verbose output**

```bash
uv run pytest tests/mde/test_hook_worktree_create.py -v
```
Expected: 20 tests pass.

- [ ] **Step 3: Run full validation**

```bash
uv run mde-py validate --all
```

- [ ] **Step 4: Verify hook is discovered**

```bash
uv run mde-py hooks --help 2>&1 | grep worktree-create
```
Expected: `worktree-create` appears in the hook list.

- [ ] **Step 5: Push**

```bash
git push -u origin feat/worktree-setup-hook
```

- [ ] **Step 6: Create PR**

```bash
gh pr create \
  --title "feat: add WorktreeCreate hook for automatic worktree setup" \
  --body "$(cat <<'EOF'
## Summary
- Replaces Claude Code's default git worktree creation with enhanced version
- Automatically runs `mise trust` + `uv sync --frozen` + `.remember` symlink + `.worktreeinclude` copy
- Fixes 3 known worktree issues: VIRTUAL_ENV mismatch, mise trust requirement, missing .venv
- Branches from HEAD (includes unpushed local commits) with session_id in branch name for uniqueness

## Spec
docs/ultrapowers/specs/2026-03-30-worktree-setup-hook-design.md

## Research
- Official Claude Code hooks docs (WorktreeCreate replaces default, 600s timeout)
- Gemini adversarial review (10 findings, all addressed)
- uv sync --frozen empirical testing (96ms warm, 400ms cold venv)

## Test plan
- [ ] 20 unit tests covering creation, setup, stdout purity, error handling
- [ ] Quality gate passes (all checks)
- [ ] Hook auto-discovered via `mde-py hooks --help`
- [ ] Manual test: `claude --worktree test-hook` creates worktree with .venv and trusted mise

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```
