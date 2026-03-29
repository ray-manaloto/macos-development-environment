"""PreToolUse hook: block ad-hoc global installs."""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "PreToolUse install guard",
    "entry": "guard_install",
}

import json
import re
import sys
from typing import Any

from mde.hooks._common import hook_span, parse_hook_stdin
from mde.log import logger

_BLOCK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bnpm\s+install\s+(?:.*\s)?(-g|--global)\b"),
    re.compile(r"\bnpm\s+i\s+(?:.*\s)?(-g|--global)\b"),
    re.compile(r"\bbun\s+add\s+(?:.*\s)?(-g|--global)\b"),
    re.compile(r"\bbun\s+install\s+(?:.*\s)?(-g|--global)\b"),
    re.compile(r"\byarn\s+global\s+add\b"),
    re.compile(r"\bpip\s+install\b(?!.*(?:-e\s*\.|\.))"),
    re.compile(r"\bpip3\s+install\b"),
    re.compile(r"\bpipx\s+install\b"),
    re.compile(r"\buv\s+tool\s+install\b"),
    re.compile(r"\bcargo\s+install\b"),
    re.compile(r"\bgo\s+install\b"),
    re.compile(r"\bbrew\s+install\b"),
]

_ALLOW_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bmise\s+install\b"),
    re.compile(r"\bbrew\s+bundle\b"),
    re.compile(r"\bnpx\s+skills\b"),
    re.compile(r"\buv\s+pip\s+install\b"),
    re.compile(r"\buv\s+sync\b"),
    re.compile(r"\buv\s+add\b"),
]

_DENY_REASON = (
    "BLOCKED: Direct global install detected. "
    "This project uses mise as the tool authority. "
    "Add the tool to home/dot_config/mise/config.toml.tmpl instead. "
    "See .agents/skills/mise-tool-management/SKILL.md for backend selection."
)


def check_install_command(command: str) -> dict[str, Any] | None:
    """Return a deny decision dict if *command* is a blocked install, else None."""
    # Allow-list takes precedence
    for pattern in _ALLOW_PATTERNS:
        if pattern.search(command):
            return None

    for pattern in _BLOCK_PATTERNS:
        if pattern.search(command):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": _DENY_REASON,
                },
            }

    return None


def guard_install() -> int:
    """Entry point: read JSON from stdin, block if ad-hoc install detected."""
    try:
        data = parse_hook_stdin()
    except (json.JSONDecodeError, ValueError) as exc:
        logger.bind(hook="guard_install", error=str(exc)).warning("hook_stdin_parse_failed")
        return 0

    with hook_span("guard_install", "PreToolUse", data) as span:
        tool_input = data.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            tool_input = {}
        command = tool_input.get("command", "")
        if not command:
            span.set_attribute("hook.blocked", False)  # noqa: FBT003
            logger.bind(hook="guard_install", blocked="False", reason="no_command").info(
                "hook_completed"
            )
            return 0

        result = check_install_command(command)
        blocked = result is not None
        span.set_attribute("hook.blocked", blocked)
        if result is not None:
            json.dump(result, sys.stdout)

        session_id = data.get("session_id", "")
        logger.bind(
            hook="guard_install",
            blocked=str(blocked),
            command=command,
            session_id=session_id,
        ).info("hook_completed")
        return 0
