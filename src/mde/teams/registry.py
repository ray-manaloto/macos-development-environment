"""Team config discovery and validation."""

from __future__ import annotations

from pathlib import Path


def find_team_config(
    name: str,
    root: Path | None = None,
) -> Path | None:
    """Find the config file for a named team.

    Args:
        name: Team name to find.
        root: Project root. Defaults to cwd.

    Returns:
        Path to the team config, or None if not found.
    """
    root = root or Path.cwd()
    teams_dir = root / "configs" / "agent-teams"

    candidates = [
        teams_dir / f"{name}.yaml",
        teams_dir / f"{name}.yml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def list_teams(root: Path | None = None) -> list[str]:
    """List available team names.

    Args:
        root: Project root. Defaults to cwd.

    Returns:
        List of team name strings.
    """
    root = root or Path.cwd()
    teams_dir = root / "configs" / "agent-teams"
    if not teams_dir.exists():
        return []
    return sorted(p.stem for p in teams_dir.glob("*.yaml"))
