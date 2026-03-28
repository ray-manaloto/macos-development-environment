"""Tests for hk configuration validation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from mde.models.result import Severity
from mde.validate.hk import validate_hk


class TestValidateHk:
    """Tests for validate_hk()."""

    def test_missing_hk_pkl(self, tmp_path: Path) -> None:
        """Missing hk.pkl produces a warning."""
        result = validate_hk(root=tmp_path)
        assert len(result.findings) == 1
        assert result.findings[0].severity == Severity.WARNING
        assert result.findings[0].rule == "hk.missing-config"
        assert result.passed  # warnings don't fail

    def test_hk_not_installed(self, tmp_path: Path) -> None:
        """Hk binary missing produces an error."""
        (tmp_path / "hk.pkl").write_text("amends hk")
        with patch("mde.validate.hk.shutil.which", return_value=None):
            result = validate_hk(root=tmp_path)
        assert len(result.findings) == 1
        assert result.findings[0].severity == Severity.ERROR
        assert result.findings[0].rule == "hk.not-installed"
        assert not result.passed

    def test_valid_config(self, tmp_path: Path) -> None:
        """Passing hk validate produces no findings."""
        (tmp_path / "hk.pkl").write_text("amends hk")
        with (
            patch("mde.validate.hk.shutil.which", return_value="/usr/local/bin/hk"),
            patch("mde.validate.hk.subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "hk.pkl is valid\n"
            result = validate_hk(root=tmp_path)
        assert len(result.findings) == 0
        assert result.passed
        assert result.files_checked == 1

    def test_invalid_config(self, tmp_path: Path) -> None:
        """Failing hk validate produces an error with output."""
        (tmp_path / "hk.pkl").write_text("invalid pkl")
        error_msg = "Failed to load configuration: syntax error"
        with (
            patch("mde.validate.hk.shutil.which", return_value="/usr/local/bin/hk"),
            patch("mde.validate.hk.subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 101
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = error_msg
            result = validate_hk(root=tmp_path)
        assert len(result.findings) == 1
        assert result.findings[0].severity == Severity.ERROR
        assert result.findings[0].rule == "hk.validate"
        assert error_msg in result.findings[0].message
        assert not result.passed

    def test_nonzero_exit_no_output(self, tmp_path: Path) -> None:
        """Non-zero exit with empty output still reports the exit code."""
        (tmp_path / "hk.pkl").write_text("amends hk")
        with (
            patch("mde.validate.hk.shutil.which", return_value="/usr/local/bin/hk"),
            patch("mde.validate.hk.subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""
            result = validate_hk(root=tmp_path)
        assert len(result.findings) == 1
        assert "exited with code 1" in result.findings[0].message

    def test_timeout(self, tmp_path: Path) -> None:
        """Timeout produces an error."""
        (tmp_path / "hk.pkl").write_text("amends hk")
        import subprocess

        with (
            patch("mde.validate.hk.shutil.which", return_value="/usr/local/bin/hk"),
            patch(
                "mde.validate.hk.subprocess.run",
                side_effect=subprocess.TimeoutExpired("hk", 30),
            ),
        ):
            result = validate_hk(root=tmp_path)
        assert len(result.findings) == 1
        assert result.findings[0].rule == "hk.timeout"
        assert not result.passed

    def test_binary_vanished(self, tmp_path: Path) -> None:
        """FileNotFoundError after which() check produces an error."""
        (tmp_path / "hk.pkl").write_text("amends hk")
        with (
            patch("mde.validate.hk.shutil.which", return_value="/usr/local/bin/hk"),
            patch(
                "mde.validate.hk.subprocess.run",
                side_effect=FileNotFoundError("hk"),
            ),
        ):
            result = validate_hk(root=tmp_path)
        assert len(result.findings) == 1
        assert result.findings[0].rule == "hk.not-found"


@pytest.mark.integration
class TestValidateHkIntegration:
    """Integration tests that run the real hk binary."""

    def test_real_hk_validate(self) -> None:
        """Real hk validate passes on the project config."""
        result = validate_hk()
        assert result.passed
        assert result.files_checked == 1
