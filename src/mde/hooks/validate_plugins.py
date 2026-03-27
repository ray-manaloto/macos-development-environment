"""PostToolUse hook: validate rsm-subagents plugins after edits.

Runs `uv run mde-py validate --plugins` when any file in rsm-subagents/
is modified via Edit or Write tools.
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "name": "validate-plugins",  # override: validate_plugins.py → validate-plugins
    "help": "PostToolUse rsm-subagents validator",
    "entry": "validate_plugins_hook",
}

import json
import subprocess
import sys

from mde.hooks._common import hook_span, parse_hook_stdin
from mde.log import logger

_RSM_SUBAGENTS_PATH = "rsm-subagents/"


def validate_plugins_hook() -> int:
    """Entry point: run plugin validation if an rsm-subagents file was modified."""
    try:
        data = parse_hook_stdin()
    except (json.JSONDecodeError, ValueError) as exc:
        logger.bind(hook="validate_plugins", error=str(exc)).warning("hook_stdin_parse_failed")
        return 0

    with hook_span("validate_plugins", "PostToolUse", data) as span:
        tool_input = data.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            tool_input = {}

        file_path = tool_input.get("file_path", "")
        if not file_path or _RSM_SUBAGENTS_PATH not in file_path:
            span.set_attribute("hook.skipped", True)  # noqa: FBT003
            return 0

        span.set_attribute("hook.skipped", False)  # noqa: FBT003
        span.set_attribute("hook.file_path", file_path)

        logger.bind(
            hook="validate_plugins",
            file_path=file_path,
        ).info("rsm_subagents_modified_running_validation")

        try:
            proc = subprocess.run(
                ["uv", "run", "mde-py", "validate", "--plugins"],
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.bind(hook="validate_plugins", error=str(exc)).warning(
                "validation_command_failed"
            )
            return 0

        if proc.returncode != 0:
            sys.stderr.write(proc.stderr)
            logger.bind(
                hook="validate_plugins",
                exit_code=proc.returncode,
            ).warning("plugin_validation_failed")
            return 1

        logger.bind(hook="validate_plugins").info("plugin_validation_passed")
        return 0
