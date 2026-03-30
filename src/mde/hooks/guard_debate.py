"""PreToolUse hook: warn when raw codex/gemini CLI is used instead of mde debate."""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "PreToolUse debate guard (advisory)",
    "entry": "guard_debate",
}

import json
import re
import sys
from typing import Any

from mde.hooks._common import hook_span, parse_hook_stdin
from mde.log import logger

_WARN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bcodex\s+exec\b"),
    re.compile(r"\bcodex\s+review\b"),
    re.compile(r"(?:^|\s|&&|\|\||\||;)gemini\b"),
]

_ALLOW_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\buv\s+run\s+mde-py\b"),
    re.compile(r"\bwhich\s+(?:codex|gemini)\b"),
    re.compile(r"\bcodex\s+--version\b"),
    re.compile(r"\bgemini\s+--version\b"),
    re.compile(r"\bcodex\s+login\b"),
]

_WARN_MESSAGE = (
    "WARNING: Direct codex/gemini CLI invocation detected. "
    "Use `uv run mde-py debate` instead. "
    "See feedback_use_mde_debate.md for rationale."
)


def check_debate_command(command: str) -> dict[str, Any] | None:
    """Return an advisory allow dict with systemMessage if raw CLI detected, else None."""
    if not command:
        return None

    # Allow-list takes precedence
    for pattern in _ALLOW_PATTERNS:
        if pattern.search(command):
            return None

    for pattern in _WARN_PATTERNS:
        if pattern.search(command):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                },
                "systemMessage": _WARN_MESSAGE,
            }

    return None


def guard_debate() -> int:
    """Entry point: read JSON from stdin, warn if raw codex/gemini CLI detected."""
    try:
        data = parse_hook_stdin()
    except (json.JSONDecodeError, ValueError) as exc:
        logger.bind(hook="guard_debate", error=str(exc)).warning("hook_stdin_parse_failed")
        return 0

    with hook_span("guard_debate", "PreToolUse", data) as span:
        tool_input = data.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            tool_input = {}
        command = tool_input.get("command", "")
        if not command:
            span.set_attribute("hook.warned", False)  # noqa: FBT003
            logger.bind(hook="guard_debate", warned="False", reason="no_command").info(
                "hook_completed"
            )
            return 0

        result = check_debate_command(command)
        warned = result is not None
        span.set_attribute("hook.warned", warned)
        if result is not None:
            json.dump(result, sys.stdout)

        session_id = data.get("session_id", "")
        logger.bind(
            hook="guard_debate",
            warned=str(warned),
            command=command,
            session_id=session_id,
        ).info("hook_completed")
        return 0


__all__ = ["check_debate_command", "guard_debate"]
