"""Tests for mise validation, including lockfile platform checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from mde.validate.mise import LockfileParseError, _find_foreign_platforms


class TestLockfilePlatformValidator:
    """Tests for _find_foreign_platforms and fail-open fix."""

    def test_valid_lockfile_no_foreign(self, tmp_path: Path) -> None:
        lock = tmp_path / "mise.lock"
        lock.write_text('[tools.node]\n"platforms.macos-arm64" = "22.0.0"\n')
        result = _find_foreign_platforms(lock, "macos-arm64")
        assert result == set()

    def test_valid_lockfile_with_foreign(self, tmp_path: Path) -> None:
        lock = tmp_path / "mise.lock"
        lock.write_text(
            '[tools.node]\n"platforms.macos-arm64" = "22.0.0"\n"platforms.linux-x64" = "22.0.0"\n'
        )
        result = _find_foreign_platforms(lock, "macos-arm64")
        assert result == {"linux-x64"}

    def test_corrupted_toml_raises_error(self, tmp_path: Path) -> None:
        lock = tmp_path / "mise.lock"
        lock.write_text("this is not valid toml [[[")
        with pytest.raises(LockfileParseError, match="corrupted"):
            _find_foreign_platforms(lock, "macos-arm64")

    def test_unreadable_file_raises_error(self, tmp_path: Path) -> None:
        lock = tmp_path / "mise.lock"
        # File doesn't exist
        with pytest.raises(LockfileParseError, match="cannot read"):
            _find_foreign_platforms(lock, "macos-arm64")

    def test_empty_toml_returns_empty(self, tmp_path: Path) -> None:
        lock = tmp_path / "mise.lock"
        lock.write_text("")
        result = _find_foreign_platforms(lock, "macos-arm64")
        assert result == set()

    def test_no_tools_section_returns_empty(self, tmp_path: Path) -> None:
        lock = tmp_path / "mise.lock"
        lock.write_text("[settings]\nfoo = true\n")
        result = _find_foreign_platforms(lock, "macos-arm64")
        assert result == set()


class TestLockfilePlatformValidation:
    """Tests for _check_mise_lockfile_platforms handling parse errors."""

    def test_corrupt_lockfile_reported_as_error(self, tmp_path: Path) -> None:
        from mde.models.result import ValidationResult
        from mde.validate.mise import _check_mise_lockfile_platforms

        lock = tmp_path / "mise.lock"
        lock.write_text("corrupt [[[")

        result = ValidationResult()
        _check_mise_lockfile_platforms(tmp_path, result)
        errors = [f for f in result.findings if f.rule == "mise.lockfile-corrupt"]
        assert len(errors) == 1
        assert "corrupted" in errors[0].message
