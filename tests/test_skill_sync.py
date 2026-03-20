"""Tests for bidirectional skill sync engine."""

from __future__ import annotations

import os
from pathlib import Path

from mde.maintain.skill_sync import (
    SyncDiscovery,
    discover_unsynced_skills,
    sync_skills,
)


def _make_skill(base: Path, name: str) -> Path:
    """Create a minimal skill directory with SKILL.md marker."""
    skill_dir = base / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"# {name}\n")
    return skill_dir


def test_discover_unsynced_agents_skill(tmp_path: Path) -> None:
    """Skill in .agents/skills/ without .claude/skills/ symlink is agents_only."""
    agents_dir = tmp_path / ".agents" / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    agents_dir.mkdir(parents=True)
    claude_dir.mkdir(parents=True)

    _make_skill(agents_dir, "my-tool")

    result = discover_unsynced_skills(tmp_path)

    assert isinstance(result, SyncDiscovery)
    assert len(result.agents_only) == 1
    assert result.agents_only[0].name == "my-tool"
    assert result.agents_only[0].source == "agents"
    assert len(result.claude_only) == 0
    assert len(result.synced) == 0


def test_discover_unsynced_claude_skill(tmp_path: Path) -> None:
    """Skill in .claude/skills/ without .agents/skills/ symlink is claude_only."""
    agents_dir = tmp_path / ".agents" / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    agents_dir.mkdir(parents=True)
    claude_dir.mkdir(parents=True)

    _make_skill(claude_dir, "review-pr")

    result = discover_unsynced_skills(tmp_path)

    assert len(result.claude_only) == 1
    assert result.claude_only[0].name == "review-pr"
    assert result.claude_only[0].source == "claude"
    assert len(result.agents_only) == 0
    assert len(result.synced) == 0


def test_synced_skill_detected(tmp_path: Path) -> None:
    """Skill present in both dirs (via symlink) is detected as synced."""
    agents_dir = tmp_path / ".agents" / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    agents_dir.mkdir(parents=True)
    claude_dir.mkdir(parents=True)

    canonical = _make_skill(agents_dir, "shared-skill")
    # Create a relative symlink in .claude/skills/ pointing to .agents/skills/shared-skill
    link = claude_dir / "shared-skill"
    rel_target = os.path.relpath(canonical, link.parent)
    link.symlink_to(rel_target)

    result = discover_unsynced_skills(tmp_path)

    assert len(result.synced) == 1
    assert result.synced[0].name == "shared-skill"
    assert len(result.agents_only) == 0
    assert len(result.claude_only) == 0


def test_sync_creates_symlink_for_agents_only(tmp_path: Path) -> None:
    """sync_skills creates a .claude/skills/ symlink for an agents-only skill."""
    agents_dir = tmp_path / ".agents" / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    agents_dir.mkdir(parents=True)
    claude_dir.mkdir(parents=True)

    _make_skill(agents_dir, "deploy")

    actions = sync_skills(tmp_path, dry_run=False)

    assert len(actions) == 1
    assert "deploy" in actions[0]

    link = claude_dir / "deploy"
    assert link.is_symlink()
    assert link.is_dir()
    # Symlink must be relative, not absolute
    assert not link.readlink().is_absolute()


def test_sync_creates_symlink_for_claude_only(tmp_path: Path) -> None:
    """sync_skills creates an .agents/skills/ symlink for a claude-only skill."""
    agents_dir = tmp_path / ".agents" / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    agents_dir.mkdir(parents=True)
    claude_dir.mkdir(parents=True)

    _make_skill(claude_dir, "lint-code")

    actions = sync_skills(tmp_path, dry_run=False)

    assert len(actions) == 1
    assert "lint-code" in actions[0]

    link = agents_dir / "lint-code"
    assert link.is_symlink()
    assert link.is_dir()
    assert not link.readlink().is_absolute()


def test_sync_dry_run_creates_no_symlinks(tmp_path: Path) -> None:
    """dry_run=True reports actions but does not create symlinks."""
    agents_dir = tmp_path / ".agents" / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    agents_dir.mkdir(parents=True)
    claude_dir.mkdir(parents=True)

    _make_skill(agents_dir, "build")
    _make_skill(claude_dir, "test")

    actions = sync_skills(tmp_path, dry_run=True)

    # Two actions reported (one for each unsynced skill)
    assert len(actions) == 2

    # But no symlinks were created
    assert not (claude_dir / "build").exists()
    assert not (agents_dir / "test").exists()
