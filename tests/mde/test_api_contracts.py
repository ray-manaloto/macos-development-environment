"""Tests that mde API enforces typed return values -- no silent swallowing."""

from __future__ import annotations

from mde.models.result import Severity, ValidationResult


class TestFindingSeverity:
    """Tests for the Severity enum."""

    def test_severity_is_enum(self) -> None:
        """Severity must be a proper enum with expected members."""
        assert hasattr(Severity, "ERROR")
        assert hasattr(Severity, "WARNING")
        assert hasattr(Severity, "INFO")

    def test_severity_values(self) -> None:
        """Severity enum values must be lowercase strings."""
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"


class TestValidationResultConvenience:
    """Tests for convenience methods on ValidationResult."""

    def test_add_error_convenience(self) -> None:
        """add_error must create an ERROR-severity finding."""
        result = ValidationResult()
        result.add_error("test.toml", "something broke")
        assert len(result.findings) == 1
        assert result.findings[0].severity == Severity.ERROR
        assert result.passed is False

    def test_add_warning_convenience(self) -> None:
        """add_warning must create a WARNING-severity finding."""
        result = ValidationResult()
        result.add_warning("test.toml", "minor issue")
        assert len(result.findings) == 1
        assert result.findings[0].severity == Severity.WARNING
        assert result.passed is True  # warnings don't fail

    def test_has_warnings_property(self) -> None:
        """has_warnings must be True when warnings exist."""
        result = ValidationResult()
        assert result.has_warnings is False
        result.add_warning("test.toml", "warning msg")
        assert result.has_warnings is True

    def test_add_info_convenience(self) -> None:
        """add_info must create an INFO-severity finding."""
        result = ValidationResult()
        result.add_info("test.toml", "fyi")
        assert len(result.findings) == 1
        assert result.findings[0].severity == Severity.INFO
        assert result.passed is True


class TestCheckStatus:
    """Tests for CheckStatus enum."""

    def test_check_status_exists(self) -> None:
        """CheckStatus enum must exist with expected members."""
        from mde.models.status import CheckStatus

        assert hasattr(CheckStatus, "PASS")
        assert hasattr(CheckStatus, "WARN")
        assert hasattr(CheckStatus, "FAIL")

    def test_check_status_values(self) -> None:
        """CheckStatus enum values must be lowercase strings."""
        from mde.models.status import CheckStatus

        assert CheckStatus.PASS.value == "pass"
        assert CheckStatus.WARN.value == "warn"
        assert CheckStatus.FAIL.value == "fail"


class TestCliDispatch:
    """Tests for CLI handler return contracts."""

    def test_no_args_returns_zero(self) -> None:
        """No arguments should print help and return 0."""
        from mde.cli import run

        assert run([]) == 0

    def test_unknown_command_exits(self) -> None:
        """Unknown commands should cause argparse to exit."""
        import pytest

        from mde.cli import run

        with pytest.raises(SystemExit):
            run(["nonexistent"])
