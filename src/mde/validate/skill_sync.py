"""Skill sync parity validation.

Checks bidirectional symlink parity between ``.agents/skills/`` and
``.claude/skills/``, reporting errors for any skill that exists in only
one of the two directories.
"""

from __future__ import annotations

from pathlib import Path

from mde.maintain.skill_sync import discover_unsynced_skills
from mde.models.result import ValidationResult


def validate_skill_sync(root: Path | None = None) -> ValidationResult:
    """Validate that all skills are synced between .agents/ and .claude/.

    Returns a :class:`ValidationResult` with errors for any skill that
    exists in only one directory.  Each error is marked ``fixable=True``
    because ``uv run mde-py skill sync`` can create the missing symlinks.
    """
    result = ValidationResult()
    root = root or Path.cwd()

    discovery = discover_unsynced_skills(root)

    for entry in discovery.agents_only:
        result.add_error(
            str(entry.path),
            f"Skill '{entry.name}' in .agents/skills/ has no .claude/skills/ symlink. "
            "Run: uv run mde-py skill sync",
            rule="skill-sync.missing-claude",
            fixable=True,
        )

    for entry in discovery.claude_only:
        result.add_error(
            str(entry.path),
            f"Skill '{entry.name}' in .claude/skills/ has no .agents/skills/ symlink. "
            "Run: uv run mde-py skill sync",
            rule="skill-sync.missing-agents",
            fixable=True,
        )

    return result
