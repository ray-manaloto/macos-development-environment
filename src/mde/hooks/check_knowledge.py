"""PostToolUse hook: detect stale knowledge surface references.

When src/mde/hooks/ or src/mde/ files are modified, checks auto-memory
and agent definitions for stale counts (hooks, tests, subcommands).
Prints warnings to stderr so the model knows to update knowledge surfaces.
Always exits 0 (advisory, never blocks).
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "name": "check-knowledge",
    "help": "PostToolUse knowledge staleness detector",
    "entry": "check_knowledge",
}

import json
import re
import sys
from pathlib import Path

from mde.hooks._common import hook_span, parse_hook_stdin, repo_root
from mde.log import logger

# Paths that trigger a knowledge check when modified
_TRIGGER_PATHS = ("src/mde/hooks/", "src/mde/cli.py", ".claude/settings.json", ".mcp.json")

# Auto-memory directory (outside repo)
_MEMORY_DIR = Path.home() / ".claude" / "projects"


def _count_hooks() -> int:
    """Count auto-discovered hook modules (non-private, non-init)."""
    hooks_dir = repo_root() / "src" / "mde" / "hooks"
    return sum(
        1 for f in hooks_dir.glob("*.py") if not f.name.startswith("_") and f.name != "__init__.py"
    )


def _find_memory_dir() -> Path | None:
    """Find the auto-memory directory for this project."""
    root = repo_root()
    slug = str(root).replace("/", "-")
    candidate = _MEMORY_DIR / slug / "memory"
    if candidate.is_dir():
        return candidate
    return None


def _check_stale_counts(memory_dir: Path) -> list[str]:
    """Check memory files for stale numeric counts.

    Only checks files that describe THIS project's hook modules
    (pattern: "N hooks via __hook_meta__" or "N hooks auto-discovered").
    Ignores plugin hook counts and Claude Code event counts.
    """
    warnings: list[str] = []
    actual_hooks = _count_hooks()

    # Only match patterns that clearly refer to our auto-discovered hooks
    hook_pattern = re.compile(r"(\d+)\s+hooks?\s+(?:via\s+__hook_meta__|auto-discovered)")

    for md_file in memory_dir.glob("*.md"):
        try:
            text = md_file.read_text()
        except OSError:
            continue

        for match in hook_pattern.finditer(text):
            count = int(match.group(1))
            if count != actual_hooks:
                warnings.append(
                    f"{md_file.name}: says '{count} hooks' but actual is {actual_hooks}"
                )

    return warnings


def _check_stale_agents() -> list[str]:
    """Check agent definitions for stale auto-discovered hook counts."""
    warnings: list[str] = []
    agents_dir = repo_root() / ".claude" / "agents"
    if not agents_dir.is_dir():
        return warnings

    actual_hooks = _count_hooks()
    hook_pattern = re.compile(r"(\d+)\s+hooks?\s+(?:via\s+__hook_meta__|auto-discovered)")

    for agent_file in agents_dir.glob("*.md"):
        try:
            text = agent_file.read_text()
        except OSError:
            continue

        for match in hook_pattern.finditer(text):
            count = int(match.group(1))
            if count != actual_hooks:
                msg = (
                    f".claude/agents/{agent_file.name}:"
                    f" says '{count} hooks' but actual is {actual_hooks}"
                )
                warnings.append(msg)

    return warnings


def check_knowledge() -> int:
    """Check knowledge surfaces for stale references after file modifications."""
    try:
        data = parse_hook_stdin()
    except (json.JSONDecodeError, ValueError):
        return 0

    with hook_span("check_knowledge", "PostToolUse", data) as span:
        tool_input = data.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            return 0

        file_path = tool_input.get("file_path", "")
        if not file_path or not any(trigger in file_path for trigger in _TRIGGER_PATHS):
            span.set_attribute("hook.skipped", True)  # noqa: FBT003
            return 0

        span.set_attribute("hook.skipped", False)  # noqa: FBT003
        span.set_attribute("hook.file_path", file_path)

        all_warnings: list[str] = []

        # Check auto-memory
        memory_dir = _find_memory_dir()
        if memory_dir:
            all_warnings.extend(_check_stale_counts(memory_dir))

        # Check agent definitions
        all_warnings.extend(_check_stale_agents())

        if all_warnings:
            print(  # noqa: T201
                "Knowledge staleness detected — update these surfaces:",
                file=sys.stderr,
            )
            for w in all_warnings:
                print(f"  - {w}", file=sys.stderr)  # noqa: T201
            span.set_attribute("hook.stale_count", len(all_warnings))
            logger.bind(hook="check_knowledge", stale=len(all_warnings)).info("staleness_detected")

        return 0
