"""Agent policy enforcement (migrated from lib/mde-agent-policy.sh)."""

from __future__ import annotations

from pathlib import Path


def check_agent_policy(root: Path | None = None) -> bool:
    """Check that agent runtime policy files exist.

    Args:
        root: Project root. Defaults to cwd.

    Returns:
        True if all policy files exist.
    """
    root = root or Path.cwd()
    required_files = [
        root / "CLAUDE.md",
        root / "AGENTS.md",
    ]
    return all(f.exists() for f in required_files)
