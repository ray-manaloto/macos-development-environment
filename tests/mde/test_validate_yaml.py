"""Tests for YAML validation."""

from __future__ import annotations

from pathlib import Path

from mde.validate.yaml_validator import validate_yaml_files


class TestYamlValidation:
    """Tests for YAML validation."""

    def test_valid_yaml(self, tmp_path: Path) -> None:
        """Valid YAML should produce no errors."""
        configs = tmp_path / "configs"
        configs.mkdir()
        yaml_file = configs / "test.yaml"
        yaml_file.write_text("key: value\n")
        result = validate_yaml_files(root=tmp_path)
        assert result.passed is True

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        """Invalid YAML should produce findings."""
        configs = tmp_path / "configs"
        configs.mkdir()
        yaml_file = configs / "bad.yaml"
        yaml_file.write_text("key: [unclosed\n")
        result = validate_yaml_files(root=tmp_path)
        assert result.passed is False
