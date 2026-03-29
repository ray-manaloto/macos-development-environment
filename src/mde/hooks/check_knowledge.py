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
_TRIGGER_PATHS = (
    "src/mde/hooks/",
    "src/mde/cli.py",
    "src/mde/",
    "tests/",
    ".claude/settings.json",
    ".mcp.json",
)

# Auto-memory directory (outside repo)
_MEMORY_DIR = Path.home() / ".claude" / "projects"

# Test counts fluctuate as tests are added/removed; only flag large drifts
_TEST_COUNT_TOLERANCE = 10

# Compiled patterns for count detection
_HOOK_PATTERN = re.compile(r"(\d+)\s+hooks?\s+(?:via\s+__hook_meta__|auto-discovered)")
_TEST_PATTERN = re.compile(r"(\d+)\s+(?:passing\s+)?tests?\b")
_SUBCMD_PATTERN = re.compile(r"(\d+)\s+(?:CLI\s+)?subcommands?\b")


def _count_hooks() -> int:
    """Count auto-discovered hook modules (non-private, non-init)."""
    hooks_dir = repo_root() / "src" / "mde" / "hooks"
    return sum(
        1 for f in hooks_dir.glob("*.py") if not f.name.startswith("_") and f.name != "__init__.py"
    )


def _count_tests() -> int | None:
    """Count pytest test items via --collect-only. Returns None on failure."""
    import subprocess

    try:
        proc = subprocess.run(
            ["uv", "run", "pytest", "tests/", "--co", "-q"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(repo_root()),
        )
        if proc.returncode == 0:
            for line in reversed(proc.stdout.splitlines()):
                m = re.match(r"(\d+)\s+tests?\s+collected", line.strip())
                if m:
                    return int(m.group(1))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logger.debug("pytest collection failed or timed out")
    return None


def _count_subcommands() -> int:
    """Count top-level CLI subcommands from the cli.py dispatcher."""
    cli_path = repo_root() / "src" / "mde" / "cli.py"
    try:
        text = cli_path.read_text()
    except OSError:
        return 0
    return len(re.findall(r"\.add_parser\(", text))


def _find_memory_dir() -> Path | None:
    """Find the auto-memory directory for this project."""
    root = repo_root()
    slug = str(root).replace("/", "-")
    candidate = _MEMORY_DIR / slug / "memory"
    if candidate.is_dir():
        return candidate
    return None


def _scan_text_for_staleness(
    text: str,
    label: str,
    actual_hooks: int,
    actual_tests: int | None,
    actual_subcmds: int,
) -> list[str]:
    """Check a single text body for stale counts. Returns warning strings."""
    warnings: list[str] = []

    for match in _HOOK_PATTERN.finditer(text):
        count = int(match.group(1))
        if count != actual_hooks:
            warnings.append(f"{label}: says '{count} hooks' but actual is {actual_hooks}")

    if actual_tests is not None:
        for match in _TEST_PATTERN.finditer(text):
            count = int(match.group(1))
            if abs(count - actual_tests) > _TEST_COUNT_TOLERANCE:
                warnings.append(f"{label}: says '{count} tests' but actual is {actual_tests}")

    if actual_subcmds > 0:
        for match in _SUBCMD_PATTERN.finditer(text):
            count = int(match.group(1))
            if count != actual_subcmds:
                warnings.append(
                    f"{label}: says '{count} subcommands' but actual is {actual_subcmds}"
                )

    return warnings


def _collect_actuals() -> tuple[int, int | None, int]:
    """Gather actual counts once for reuse across scan targets."""
    return _count_hooks(), _count_tests(), _count_subcommands()


def _check_stale_counts(memory_dir: Path) -> list[str]:
    """Check memory files for stale numeric counts."""
    warnings: list[str] = []
    actuals = _collect_actuals()

    for md_file in memory_dir.glob("*.md"):
        try:
            text = md_file.read_text()
        except OSError:
            continue
        warnings.extend(_scan_text_for_staleness(text, md_file.name, *actuals))

    return warnings


def _check_stale_agents() -> list[str]:
    """Check agent definitions for stale counts."""
    warnings: list[str] = []
    agents_dir = repo_root() / ".claude" / "agents"
    if not agents_dir.is_dir():
        return warnings

    actuals = _collect_actuals()

    for agent_file in agents_dir.glob("*.md"):
        try:
            text = agent_file.read_text()
        except OSError:
            continue
        label = f".claude/agents/{agent_file.name}"
        warnings.extend(_scan_text_for_staleness(text, label, *actuals))

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
