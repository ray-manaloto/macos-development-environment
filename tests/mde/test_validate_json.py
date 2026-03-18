"""Tests for JSON validation."""

from __future__ import annotations

from pathlib import Path

from mde.validate.json_validator import validate_json_files


class TestJsonValidation:
    """Tests for JSON validation."""

    def test_valid_json(self, tmp_path: Path) -> None:
        """Valid JSON should produce no errors."""
        configs = tmp_path / "configs"
        configs.mkdir()
        json_file = configs / "test.json"
        json_file.write_text('{"key": "value"}\n')
        result = validate_json_files(root=tmp_path)
        assert result.passed is True

    def test_invalid_json(self, tmp_path: Path) -> None:
        """Invalid JSON should produce findings."""
        configs = tmp_path / "configs"
        configs.mkdir()
        json_file = configs / "bad.json"
        json_file.write_text("{bad json}\n")
        result = validate_json_files(root=tmp_path)
        assert result.passed is False
