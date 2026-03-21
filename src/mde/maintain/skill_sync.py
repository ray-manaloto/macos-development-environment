"""Bidirectional skill sync engine for .agents/skills/ and .claude/skills/.

Scans both skill directories and creates missing relative symlinks so that
skills authored in one location are accessible from the other.  The
`.agents/skills/` directory is treated as canonical per Vercel skills CLI
convention.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class SkillEntry(BaseModel):
    """A single discovered skill directory."""

    name: str = Field(description="Skill directory name")
    path: Path = Field(description="Absolute path to the skill directory")
    source: Literal["agents", "claude"] = Field(
        description="Which tree the canonical copy lives in"
    )


class SyncDiscovery(BaseModel):
    """Result of scanning both skill directories for sync status."""

    agents_only: list[SkillEntry] = Field(
        default_factory=list,
        description="Skills only in .agents/skills/ (no .claude/skills/ link)",
    )
    claude_only: list[SkillEntry] = Field(
        default_factory=list,
        description="Skills only in .claude/skills/ (no .agents/skills/ link)",
    )
    synced: list[SkillEntry] = Field(
        default_factory=list,
        description="Skills present in both directories",
    )


def _is_skill_dir(path: Path) -> bool:
    """Check whether *path* is a valid skill directory (contains SKILL.md)."""
    return path.is_dir() and (path / "SKILL.md").exists()


def _list_skills(base: Path) -> dict[str, Path]:
    """Return ``{name: path}`` for every skill directory under *base*."""
    if not base.is_dir():
        return {}
    return {entry.name: entry for entry in sorted(base.iterdir()) if _is_skill_dir(entry)}


def discover_unsynced_skills(root: Path) -> SyncDiscovery:
    """Scan ``.agents/skills/`` and ``.claude/skills/`` under *root*.

    Returns a `SyncDiscovery` describing which skills are synced and which
    exist in only one of the two directories.
    """
    agents_dir = root / ".agents" / "skills"
    claude_dir = root / ".claude" / "skills"

    agents_skills = _list_skills(agents_dir)
    claude_skills = _list_skills(claude_dir)

    discovery = SyncDiscovery()

    all_names = sorted({*agents_skills, *claude_skills})
    for name in all_names:
        in_agents = name in agents_skills
        in_claude = name in claude_skills

        if in_agents and in_claude:
            discovery.synced.append(
                SkillEntry(name=name, path=agents_skills[name], source="agents")
            )
        elif in_agents:
            discovery.agents_only.append(
                SkillEntry(name=name, path=agents_skills[name], source="agents")
            )
        else:
            discovery.claude_only.append(
                SkillEntry(name=name, path=claude_skills[name], source="claude")
            )

    return discovery


def sync_skills(root: Path, *, dry_run: bool = False) -> list[str]:
    """Create missing symlinks so both directories mirror each other.

    Args:
        root: Project root containing ``.agents/`` and ``.claude/``.
        dry_run: When ``True``, report planned actions without creating links.

    Returns:
        Human-readable list of actions taken (or planned in dry-run mode).
    """
    agents_dir = root / ".agents" / "skills"
    claude_dir = root / ".claude" / "skills"

    discovery = discover_unsynced_skills(root)
    actions: list[str] = []

    for entry in discovery.agents_only:
        link = claude_dir / entry.name
        rel_target = os.path.relpath(entry.path, link.parent)
        verb = "would create" if dry_run else "created"
        # Remove stale non-symlink files that block symlink creation
        if not dry_run and link.exists() and not link.is_symlink():
            link.unlink() if link.is_file() else None
            actions.append(f"removed stale file {link}")
        actions.append(f"{verb} symlink {link} -> {rel_target}")
        if not dry_run:
            link.symlink_to(rel_target)

    for entry in discovery.claude_only:
        link = agents_dir / entry.name
        rel_target = os.path.relpath(entry.path, link.parent)
        verb = "would create" if dry_run else "created"
        # Remove stale non-symlink files that block symlink creation
        if not dry_run and link.exists() and not link.is_symlink():
            link.unlink() if link.is_file() else None
            actions.append(f"removed stale file {link}")
        actions.append(f"{verb} symlink {link} -> {rel_target}")
        if not dry_run:
            link.symlink_to(rel_target)

    return actions
