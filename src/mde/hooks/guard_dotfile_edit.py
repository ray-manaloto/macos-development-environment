"""PreToolUse hook: block direct edits to chezmoi-managed dotfiles.

Enforces the source-first workflow: edits must go through chezmoi source,
not by directly modifying deployed files in ~/.
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "PreToolUse dotfile edit guard",
    "entry": "guard_dotfile_edit",
}

import json
import re
import sys
from typing import Any

from mde.hooks._common import hook_span, parse_hook_stdin
from mde.log import logger

_DOTFILE_EDIT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(vim|nvim|nano|hx|code)\s+~/\."),
    re.compile(r"\bsed\s+-i.*~/\."),
    re.compile(r"\bperl\s+-pi.*~/\."),
    re.compile(r"\btee\s+~/\."),
    re.compile(r"\becho\s+.*>>\s*~/\."),
    re.compile(r"\bcat\s+.*>\s*~/\."),
    re.compile(r"\bcp\s+.*~/\."),
    re.compile(r"\bmv\s+.*~/\."),
]

_CHEZMOI_COMMAND = re.compile(r"^chezmoi\s+(edit|cd|add|source-path)\b")
_CHEZMOI_SOURCE = re.compile(r"\.local/share/chezmoi")

_DENY_REASON = (
    "BLOCKED: Direct edit of deployed dotfile detected. "
    "This project enforces chezmoi source-first workflow. "
    "Use: chezmoi edit <filepath>, chezmoi add <filepath>, or chezmoi cd. "
    "See the chezmoi-workflows skill for guidance."
)


def check_dotfile_edit(command: str) -> dict[str, Any] | None:
    """Return a deny decision if command directly edits a managed dotfile."""
    # Use first line only to prevent multi-line bypass
    first_line = command.split("\n", maxsplit=1)[0]

    # Allow chezmoi commands
    if _CHEZMOI_COMMAND.search(first_line):
        return None

    # Allow edits to chezmoi source directory
    if _CHEZMOI_SOURCE.search(first_line):
        return None

    for pattern in _DOTFILE_EDIT_PATTERNS:
        if pattern.search(first_line):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": _DENY_REASON,
                },
            }

    return None


def guard_dotfile_edit() -> int:
    """Entry point: read JSON from stdin, block if direct dotfile edit detected."""
    try:
        data = parse_hook_stdin()
    except (json.JSONDecodeError, ValueError) as exc:
        logger.bind(hook="guard_dotfile_edit", error=str(exc)).warning("hook_stdin_parse_failed")
        return 0

    with hook_span("guard_dotfile_edit", "PreToolUse", data) as span:
        tool_input = data.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            tool_input = {}
        command = tool_input.get("command", "")
        if not command:
            span.set_attribute("hook.blocked", False)  # noqa: FBT003
            return 0

        result = check_dotfile_edit(command)
        blocked = result is not None
        span.set_attribute("hook.blocked", blocked)
        if result is not None:
            json.dump(result, sys.stdout)

        logger.bind(
            hook="guard_dotfile_edit",
            blocked=str(blocked),
            command=command,
        ).info("hook_completed")
        return 0
