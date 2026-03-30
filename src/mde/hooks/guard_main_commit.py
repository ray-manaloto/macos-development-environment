"""PreToolUse hook: warn when git commit is run on the main branch.

Detects git commit commands in Bash tool calls and emits an advisory warning
if the current branch is main/master. This prevents accidental direct-to-main
commits that bypass the worktree PR workflow.
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "PreToolUse guard against committing on main (advisory)",
    "entry": "guard_main_commit",
}

import json
import os
import re
import subprocess
import sys
from typing import Any

from mde.hooks._common import hook_span, parse_hook_stdin
from mde.log import logger

_COMMIT_PATTERN = re.compile(r"\bgit\s+commit\b")

_SAFE_BRANCHES = {"main", "master"}

_WARN_MESSAGE = (
    "WARNING: You are about to commit directly to the main branch. "
    "Use the worktree PR workflow instead: "
    "git worktree add .claude/worktrees/<name> -b feat/<name>. "
    "See worktree-pr-workflow.md for the policy."
)


def _current_branch() -> str | None:
    """Return the current git branch name, or None if detached/unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            env={"GIT_TERMINAL_PROMPT": "0", "PATH": os.environ.get("PATH", "")},
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass  # git unavailable — treat as non-main branch
    return None


def check_main_commit(command: str) -> dict[str, Any] | None:
    """Return an advisory allow dict with systemMessage if committing on main, else None."""
    if not command:
        return None

    if not _COMMIT_PATTERN.search(command):
        return None

    branch = _current_branch()
    if branch not in _SAFE_BRANCHES:
        return None

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
        },
        "systemMessage": _WARN_MESSAGE,
    }


def guard_main_commit() -> int:
    """Entry point: read JSON from stdin, warn if committing on main."""
    try:
        data = parse_hook_stdin()
    except (json.JSONDecodeError, ValueError) as exc:
        logger.bind(hook="guard_main_commit", error=str(exc)).warning("hook_stdin_parse_failed")
        return 0

    with hook_span("guard_main_commit", "PreToolUse", data) as span:
        tool_input = data.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            tool_input = {}
        command = tool_input.get("command", "")
        if not command:
            span.set_attribute("hook.warned", False)  # noqa: FBT003
            logger.bind(hook="guard_main_commit", warned="False", reason="no_command").info(
                "hook_completed"
            )
            return 0

        result = check_main_commit(command)
        warned = result is not None
        span.set_attribute("hook.warned", warned)
        if result is not None:
            json.dump(result, sys.stdout)

        session_id = data.get("session_id", "")
        logger.bind(
            hook="guard_main_commit",
            warned=str(warned),
            command=command,
            session_id=session_id,
        ).info("hook_completed")
        return 0


__all__ = ["check_main_commit", "guard_main_commit"]
