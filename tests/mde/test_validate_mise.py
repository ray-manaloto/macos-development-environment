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


class TestMiseDoctorErrorKeyword:
    """Tests for finding #8: mise doctor parser must match 'error found:' headers."""

    def test_error_found_header_captured(self) -> None:
        """Mise doctor output with 'N error found:' must be parsed."""
        from unittest.mock import patch

        from mde.models.result import ValidationResult
        from mde.validate.mise import _check_mise_doctor

        doctor_output = "1 error found:\n\n1. tool node is not installed\n"
        mock_result = type(
            "CompletedProcess", (), {"returncode": 1, "stdout": doctor_output, "stderr": ""}
        )()

        result = ValidationResult()
        with patch("mde.validate.mise.subprocess.run", return_value=mock_result):
            _check_mise_doctor(result)

        errors = [f for f in result.findings if f.rule == "mise.doctor"]
        assert len(errors) >= 1
        assert any("tool node" in e.message for e in errors)

    def test_warning_and_problem_still_captured(self) -> None:
        """Existing warning/problem keywords still work after adding error."""
        from unittest.mock import patch

        from mde.models.result import ValidationResult
        from mde.validate.mise import _check_mise_doctor

        doctor_output = (
            "1 warning found:\n"
            "\n"
            "1. mise outdated for tool rust\n"
            "\n"
            "1 problem found:\n"
            "\n"
            "1. missing shims directory\n"
        )
        mock_result = type(
            "CompletedProcess", (), {"returncode": 1, "stdout": doctor_output, "stderr": ""}
        )()

        result = ValidationResult()
        with patch("mde.validate.mise.subprocess.run", return_value=mock_result):
            _check_mise_doctor(result)

        errors = [f for f in result.findings if f.rule == "mise.doctor"]
        assert len(errors) == 2

    def test_no_errors_found_skipped(self) -> None:
        """'No errors found' should not trigger a finding."""
        from unittest.mock import patch

        from mde.models.result import ValidationResult
        from mde.validate.mise import _check_mise_doctor

        doctor_output = "No errors found\nNo problems found\n"
        mock_result = type(
            "CompletedProcess", (), {"returncode": 0, "stdout": doctor_output, "stderr": ""}
        )()

        result = ValidationResult()
        with patch("mde.validate.mise.subprocess.run", return_value=mock_result):
            _check_mise_doctor(result)

        errors = [f for f in result.findings if f.rule == "mise.doctor"]
        assert len(errors) == 0
