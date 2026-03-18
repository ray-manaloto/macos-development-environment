"""Tests for mde.models."""

from __future__ import annotations

from mde.models.result import Finding, Severity, ValidationResult


class TestValidationResult:
    """Tests for the ValidationResult model."""

    def test_empty_result_passes(self) -> None:
        """An empty result should pass."""
        result = ValidationResult()
        assert result.passed is True
        assert result.error_count == 0
        assert result.warning_count == 0

    def test_add_error_fails_result(self) -> None:
        """Adding an error should mark result as failed."""
        result = ValidationResult()
        result.add(path="test.toml", message="bad syntax")
        assert result.passed is False
        assert result.error_count == 1

    def test_add_warning_keeps_passing(self) -> None:
        """Adding a warning should not fail the result."""
        result = ValidationResult()
        result.add(
            path="test.toml",
            message="minor issue",
            severity=Severity.WARNING,
        )
        assert result.passed is True
        assert result.warning_count == 1

    def test_merge_results(self) -> None:
        """Merging should combine findings and file counts."""
        r1 = ValidationResult(files_checked=3)
        r1.add(path="a.toml", message="err")
        r2 = ValidationResult(files_checked=2)
        r1.merge(r2)
        assert r1.files_checked == 5
        assert r1.error_count == 1

    def test_finding_defaults(self) -> None:
        """Finding should have sensible defaults."""
        f = Finding(path="x.yaml", message="test")
        assert f.severity == Severity.ERROR
        assert f.rule == ""
        assert f.line is None
        assert f.fixable is False
