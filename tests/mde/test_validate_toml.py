"""Tests for TOML validation."""

from __future__ import annotations

from pathlib import Path

from mde.validate.toml import validate_toml_files


class TestTomlValidation:
    """Tests for TOML validation."""

    def test_valid_toml(self, tmp_path: Path) -> None:
        """Valid TOML should produce no errors."""
        toml_file = tmp_path / ".mise.toml"
        toml_file.write_text('[tools]\npython = "3.12"\n')
        result = validate_toml_files(root=tmp_path)
        assert result.passed is True

    def test_invalid_toml_syntax(self, tmp_path: Path) -> None:
        """Invalid TOML should produce a syntax error finding."""
        toml_file = tmp_path / ".mise.toml"
        toml_file.write_text("[invalid\n")
        result = validate_toml_files(root=tmp_path)
        assert result.passed is False
        assert any("syntax" in f.rule for f in result.findings)

    def test_missing_include(self, tmp_path: Path) -> None:
        """Missing include paths should be flagged."""
        toml_file = tmp_path / ".mise.toml"
        toml_file.write_text('includes = ["nonexistent.toml"]\n')
        result = validate_toml_files(root=tmp_path)
        assert any("include" in f.rule for f in result.findings)
