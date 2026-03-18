"""Agent team runner."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_team(name: str, *, dry_run: bool = False) -> int:
    """Run a named agent team.

    Args:
        name: Team name to run.
        dry_run: If True, print what would be done without executing.

    Returns:
        Exit code.
    """
    from mde.teams.registry import find_team_config

    config_path = find_team_config(name)
    if config_path is None:
        print(f"ERROR: Team '{name}' not found")
        return 1

    if dry_run:
        print(f"Would run team '{name}' from {config_path}")
        return 0

    print(f"==> Running team '{name}' from {config_path}")
    # Delegate to the team's run script
    script = Path("scripts/teams") / f"run-{name}.sh"
    if script.exists():
        proc = subprocess.run(
            ["bash", str(script)],
            timeout=600,
        )
        return proc.returncode
    print(f"WARN: No run script found at {script}")
    return 1
