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
import sys

from mde.hooks._common import hook_span, parse_hook_stdin
from mde.log import logger

_RSM_SUBAGENTS_PATH = "rsm-subagents/"


def validate_plugins_hook() -> int:
    """Entry point: run plugin validation if an rsm-subagents file was modified.

    Calls ``run_validators`` in-process to get both error and warning counts
    without shelling out to a subprocess.
    """
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

        from mde.validate import _print_findings, run_validators

        result = run_validators(plugins_only=True)
        _print_findings(result)

        span.set_attribute("hook.error_count", result.error_count)
        span.set_attribute("hook.warning_count", result.warning_count)

        if not result.passed:
            logger.bind(
                hook="validate_plugins",
                error_count=result.error_count,
            ).warning("plugin_validation_failed")
            return 1

        if result.warning_count > 0:
            sys.stderr.write(
                f"⚠ Plugin validation: {result.warning_count} warning(s) — fix before commit\n"
            )
            logger.bind(
                hook="validate_plugins",
                warning_count=result.warning_count,
            ).warning("plugin_validation_warnings")
            # Return 0: surface warnings but don't block the tool call.
            # Per no-warning-suppression.md: "WARNING → visible → gate passes → human decides"

        logger.bind(hook="validate_plugins").info("plugin_validation_passed")
        return 0
