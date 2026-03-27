"""PostToolUse hook: remind to commit after chezmoi apply.

After a successful chezmoi apply/re-add/add, checks if the source directory
has uncommitted changes and prints a reminder.
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "PostToolUse chezmoi reminder",
    "entry": "remind_chezmoi_commit",
}

import json
import subprocess
import sys
from typing import Any

from mde.hooks._common import hook_span, parse_hook_stdin
from mde.log import logger


def _check_chezmoi_source_dirty() -> str | None:
    """Return a reminder message if chezmoi source has uncommitted changes."""
    try:
        proc = subprocess.run(
            ["chezmoi", "source-path"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        source_dir = proc.stdout.strip()
        if not source_dir:
            return None

        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=source_dir,
            timeout=5,
        )
        if proc.stdout.strip():
            return (
                "REMINDER: Chezmoi source has uncommitted changes. "
                "Run: chezmoi git -- add -A && chezmoi git -- commit -m 'Update dotfiles' "
                "&& chezmoi git -- push"
            )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        logger.bind(hook="remind_chezmoi_commit", error=str(exc)).debug(
            "chezmoi_source_check_failed"
        )
    return None


def check_chezmoi_command(command: str) -> dict[str, Any] | None:
    """Return a reminder output if command is a chezmoi apply/add operation."""
    first_line = command.split("\n", maxsplit=1)[0]

    # Only trigger for chezmoi apply/re-add/add (not dry-run)
    if not any(cmd in first_line for cmd in ("chezmoi apply", "chezmoi re-add", "chezmoi add")):
        return None

    if "--dry-run" in first_line:
        return None

    reminder = _check_chezmoi_source_dirty()
    if reminder:
        return {"hookSpecificOutput": {"message": reminder}}
    return None


def remind_chezmoi_commit() -> int:
    """Entry point: read JSON from stdin, remind if chezmoi source is dirty."""
    try:
        data = parse_hook_stdin()
    except (json.JSONDecodeError, ValueError) as exc:
        logger.bind(hook="remind_chezmoi_commit", error=str(exc)).warning("hook_stdin_parse_failed")
        return 0

    with hook_span("remind_chezmoi_commit", "PostToolUse", data) as span:
        tool_input = data.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            tool_input = {}
        command = tool_input.get("command", "")
        if not command:
            return 0

        result = check_chezmoi_command(command)
        reminded = result is not None
        span.set_attribute("hook.reminded", reminded)
        if result is not None:
            json.dump(result, sys.stdout)

        logger.bind(
            hook="remind_chezmoi_commit",
            reminded=str(reminded),
        ).info("hook_completed")
        return 0
