"""Tests for rsm-subagents plugin validation."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from mde.validate.plugins import validate_plugins

_PATCH_TARGET = "mde.validate.plugins._run_claude_validate"
_CLI_OK = (True, "Validation passed")


def _make_marketplace(tmp_path: Path, plugins: list[dict]) -> None:
    """Create a minimal marketplace structure."""
    mp_dir = tmp_path / "rsm-subagents"
    mp_dir.mkdir(exist_ok=True)
    cp_dir = mp_dir / ".claude-plugin"
    cp_dir.mkdir(exist_ok=True)
    manifest = {
        "name": "test-marketplace",
        "plugins": plugins,
    }
    (cp_dir / "marketplace.json").write_text(json.dumps(manifest))


def _make_plugin(
    tmp_path: Path,
    name: str,
    *,
    skills: list[str] | None = None,
    agents: list[str] | None = None,
    plugin_json_extra: dict | None = None,
) -> Path:
    """Create a minimal plugin with optional components."""
    plugin_dir = tmp_path / "rsm-subagents" / "plugins" / name
    cp_dir = plugin_dir / ".claude-plugin"
    cp_dir.mkdir(parents=True)
    pj: dict = {"name": name, "version": "0.1.0"}
    if plugin_json_extra:
        pj.update(plugin_json_extra)
    (cp_dir / "plugin.json").write_text(json.dumps(pj))

    if skills:
        for skill_name in skills:
            skill_dir = plugin_dir / "skills" / skill_name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {skill_name}\n"
                f"description: This skill should be used when testing {skill_name}.\n"
                "---\n\n# Test Skill\n"
            )

    if agents:
        agents_dir = plugin_dir / "agents"
        agents_dir.mkdir(parents=True)
        for agent_name in agents:
            (agents_dir / f"{agent_name}.md").write_text(
                f"---\nname: {agent_name}\n"
                "description: >\n  Use this agent when testing.\n\n"
                "  <example>\n  Context: Test.\n"
                '  user: "test"\n  assistant: "test"\n'
                "  <commentary>Test.</commentary>\n  </example>\n\n"
                "model: inherit\ncolor: blue\n---\n\nYou are a test agent.\n"
            )

    return plugin_dir


class TestPluginValidation:
    """Tests for plugin validation."""

    def test_valid_plugin_passes(self, tmp_path: Path) -> None:
        """A well-formed plugin should produce no errors."""
        _make_marketplace(
            tmp_path,
            [{"name": "test-plugin", "source": "./plugins/test-plugin"}],
        )
        _make_plugin(tmp_path, "test-plugin", skills=["test-skill"], agents=["test-agent"])
        with patch(_PATCH_TARGET, return_value=_CLI_OK):
            result = validate_plugins(root=tmp_path)
        assert result.passed is True
        assert result.error_count == 0

    def test_forbidden_key_fails(self, tmp_path: Path) -> None:
        """plugin.json with minVersion should produce an error."""
        _make_marketplace(
            tmp_path,
            [{"name": "bad-plugin", "source": "./plugins/bad-plugin"}],
        )
        _make_plugin(
            tmp_path,
            "bad-plugin",
            plugin_json_extra={"minVersion": "2.0.0"},
        )
        with patch(_PATCH_TARGET, return_value=_CLI_OK):
            result = validate_plugins(root=tmp_path)
        assert result.passed is False
        errors = [f for f in result.findings if f.rule == "plugin.forbidden-key"]
        assert len(errors) == 1

    def test_missing_skill_name_fails(self, tmp_path: Path) -> None:
        """Skill missing name field should produce an error."""
        _make_marketplace(
            tmp_path,
            [{"name": "bad-skill-plugin", "source": "./plugins/bad-skill-plugin"}],
        )
        plugin_dir = _make_plugin(tmp_path, "bad-skill-plugin")
        skill_dir = plugin_dir / "skills" / "no-name"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\ndescription: test\n---\n\n# Test\n")
        with patch(_PATCH_TARGET, return_value=_CLI_OK):
            result = validate_plugins(root=tmp_path)
        assert result.passed is False
        errors = [f for f in result.findings if f.rule == "plugin.skill-missing-name"]
        assert len(errors) == 1

    def test_third_person_warning(self, tmp_path: Path) -> None:
        """Skill description not using third person should warn."""
        _make_marketplace(
            tmp_path,
            [{"name": "style-plugin", "source": "./plugins/style-plugin"}],
        )
        plugin_dir = _make_plugin(tmp_path, "style-plugin")
        skill_dir = plugin_dir / "skills" / "bad-style"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: bad-style\ndescription: Edit config files.\n---\n\n# Test\n"
        )
        with patch(_PATCH_TARGET, return_value=_CLI_OK):
            result = validate_plugins(root=tmp_path)
        warnings = [f for f in result.findings if f.rule == "plugin.skill-third-person"]
        assert len(warnings) == 1

    def test_missing_reference_fails(self, tmp_path: Path) -> None:
        """Skill referencing a nonexistent file should produce an error."""
        _make_marketplace(
            tmp_path,
            [{"name": "ref-plugin", "source": "./plugins/ref-plugin"}],
        )
        plugin_dir = _make_plugin(tmp_path, "ref-plugin")
        skill_dir = plugin_dir / "skills" / "broken-ref"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: broken-ref\n"
            "description: This skill should be used when testing.\n---\n\n"
            "See `references/missing-file.md` for details.\n"
        )
        with patch(_PATCH_TARGET, return_value=_CLI_OK):
            result = validate_plugins(root=tmp_path)
        errors = [f for f in result.findings if f.rule == "plugin.missing-reference"]
        assert len(errors) == 1

    def test_no_marketplace_dir(self, tmp_path: Path) -> None:
        """Missing rsm-subagents directory should return clean result."""
        result = validate_plugins(root=tmp_path)
        assert result.passed is True
