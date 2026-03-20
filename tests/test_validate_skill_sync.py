"""Tests for skill sync validator."""

from __future__ import annotations

import os
from pathlib import Path

from mde.validate.skill_sync import validate_skill_sync


def _make_skill(base: Path, name: str) -> Path:
    """Create a minimal skill directory with SKILL.md marker."""
    skill_dir = base / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"# {name}\n")
    return skill_dir


def test_unsynced_agents_skill_is_error(tmp_path: Path) -> None:
    """Skill in .agents/skills/ without .claude/skills/ symlink reports error."""
    agents_dir = tmp_path / ".agents" / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    agents_dir.mkdir(parents=True)
    claude_dir.mkdir(parents=True)

    _make_skill(agents_dir, "my-tool")

    result = validate_skill_sync(tmp_path)

    assert not result.passed
    assert result.error_count == 1
    finding = result.findings[0]
    assert finding.rule == "skill-sync.missing-claude"
    assert finding.fixable is True
    assert "my-tool" in finding.message


def test_synced_skills_pass(tmp_path: Path) -> None:
    """Skills with symlinks in both dirs pass validation."""
    agents_dir = tmp_path / ".agents" / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    agents_dir.mkdir(parents=True)
    claude_dir.mkdir(parents=True)

    canonical = _make_skill(agents_dir, "shared-skill")
    link = claude_dir / "shared-skill"
    rel_target = os.path.relpath(canonical, link.parent)
    link.symlink_to(rel_target)

    result = validate_skill_sync(tmp_path)

    assert result.passed
    assert result.error_count == 0


def test_no_skill_dirs_passes(tmp_path: Path) -> None:
    """Missing skill directories is not an error."""
    result = validate_skill_sync(tmp_path)

    assert result.passed
    assert result.error_count == 0
