"""Create and set up git worktrees for Claude Code subagents.

Replaces Claude Code's default git worktree behavior. Creates the worktree,
trusts mise config, syncs uv venv, recreates .remember symlink, and copies
.worktreeinclude files. Prints the absolute worktree path to stdout.

Triggered by: claude --worktree OR subagent isolation: "worktree"
"""

from __future__ import annotations

import fnmatch
import json
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

_GIT_ENV = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"} | {
    "GIT_TERMINAL_PROMPT": "0"
}


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
    rc, _stderr = _run_cmd(
        ["git", "worktree", "add", str(worktree_path), "-b", branch_name, "HEAD"],
        cwd=cwd,
    )

    if rc != 0:
        # Branch may already exist -- try checking it out without -b
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

    # 2. Sync Python venv (only if this is a Python project -- check repo root)
    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
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
    data = json.load(sys.stdin)
    name = data.get("name", "unnamed")
    session_id = data.get("session_id", "00000000")
    cwd = Path(data.get("cwd", str(Path.cwd())))

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

    # Print the path -- this is the ONLY thing that goes to stdout
    print(worktree_path)
    return 0
