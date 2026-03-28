"""Tests for chezmoi validation (script drift hash check, doctor zero-suppression)."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from mde.models.result import Severity, ValidationResult
from mde.validate.chezmoi import _check_chezmoi_doctor, _check_chezmoi_script_drift


def _mock_proc(*, returncode: int = 0, stdout: str = "", stderr: str = "") -> Any:
    """Create a mock CompletedProcess."""
    return type(
        "CompletedProcess",
        (),
        {
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
        },
    )()


class TestScriptDriftHashComparison:
    """Finding #6: script drift must compare hashes, not just check existence."""

    def test_no_script_state_is_error(self) -> None:
        """Empty entryState should be flagged as missing script state."""
        state_dump = '{"entryState": {}}'
        result = ValidationResult()
        with patch(
            "mde.validate.chezmoi.subprocess.run",
            return_value=_mock_proc(stdout=state_dump),
        ):
            _check_chezmoi_script_drift(result)
        errors = [f for f in result.findings if f.rule == "chezmoi.script-drift"]
        assert len(errors) == 1
        assert "no script execution state" in errors[0].message

    def test_drift_detected_via_diff(self) -> None:
        """When chezmoi diff --include=scripts returns output, drift is reported."""
        state_dump = '{"entryState": {"script1": {"type": "script"}}}'

        def mock_run(cmd: list[str], **_kwargs: Any) -> Any:
            if "state" in cmd:
                return _mock_proc(stdout=state_dump)
            if "source-path" in cmd:
                return _mock_proc(stdout="/home/user/.local/share/chezmoi")
            if "diff" in cmd:
                return _mock_proc(
                    stdout="diff --git a/script1 b/script1\n--- a/script1\n+++ b/script1\n"
                )
            return _mock_proc()

        result = ValidationResult()
        with patch("mde.validate.chezmoi.subprocess.run", side_effect=mock_run):
            _check_chezmoi_script_drift(result)

        errors = [f for f in result.findings if f.rule == "chezmoi.script-drift"]
        assert len(errors) == 1
        assert "drifted" in errors[0].message

    def test_clean_scripts_no_drift(self) -> None:
        """When diff is empty, no drift should be reported."""
        state_dump = '{"entryState": {"script1": {"type": "script"}}}'

        def mock_run(cmd: list[str], **_kwargs: Any) -> Any:
            if "state" in cmd:
                return _mock_proc(stdout=state_dump)
            if "source-path" in cmd:
                return _mock_proc(stdout="/home/user/.local/share/chezmoi")
            if "diff" in cmd:
                return _mock_proc(stdout="")
            return _mock_proc()

        result = ValidationResult()
        with patch("mde.validate.chezmoi.subprocess.run", side_effect=mock_run):
            _check_chezmoi_script_drift(result)

        errors = [f for f in result.findings if f.rule == "chezmoi.script-drift"]
        assert len(errors) == 0

    def test_state_dump_invalid_json_is_error(self) -> None:
        """Invalid JSON from state dump should be flagged."""
        result = ValidationResult()
        with patch(
            "mde.validate.chezmoi.subprocess.run",
            return_value=_mock_proc(stdout="not json"),
        ):
            _check_chezmoi_script_drift(result)
        errors = [f for f in result.findings if f.rule == "chezmoi.script-drift"]
        assert len(errors) == 1
        assert "invalid JSON" in errors[0].message


class TestChezmoiDoctorZeroSuppression:
    """Finding #9 (revised): zero suppression — all warnings surfaced at real severity."""

    def test_warning_surfaced_as_warning(self) -> None:
        """Chezmoi warnings must be reported as WARNING severity, not suppressed."""
        doctor_output = "warning  working-tree  ~/project is a git working tree (dirty)\n"
        result = ValidationResult()
        with patch(
            "mde.validate.chezmoi.subprocess.run",
            return_value=_mock_proc(stdout=doctor_output),
        ):
            _check_chezmoi_doctor(result)
        findings = [f for f in result.findings if f.rule == "chezmoi.doctor"]
        assert len(findings) == 1
        assert findings[0].severity == Severity.WARNING
        assert "working-tree" in findings[0].message

    def test_suspicious_entries_surfaced_as_warning(self) -> None:
        """Suspicious-entries must be reported as WARNING, never suppressed."""
        doctor_output = "warning  suspicious-entries  ~/project/.chezmoisource\n"
        result = ValidationResult()
        with patch(
            "mde.validate.chezmoi.subprocess.run",
            return_value=_mock_proc(stdout=doctor_output),
        ):
            _check_chezmoi_doctor(result)
        findings = [f for f in result.findings if f.rule == "chezmoi.doctor"]
        assert len(findings) == 1
        assert findings[0].severity == Severity.WARNING

    def test_error_surfaced_as_error(self) -> None:
        """Chezmoi errors must be reported as ERROR severity."""
        doctor_output = "error  config-file  config file not found\n"
        result = ValidationResult()
        with patch(
            "mde.validate.chezmoi.subprocess.run",
            return_value=_mock_proc(stdout=doctor_output),
        ):
            _check_chezmoi_doctor(result)
        findings = [f for f in result.findings if f.rule == "chezmoi.doctor"]
        assert len(findings) == 1
        assert findings[0].severity == Severity.ERROR

    def test_warnings_do_not_fail_gate(self) -> None:
        """WARNING findings should not set passed=False on the result."""
        doctor_output = (
            "warning  working-tree  ~/project is a git working tree (dirty)\n"
            "warning  suspicious-entries  ~/project/.chezmoisource\n"
        )
        result = ValidationResult()
        with patch(
            "mde.validate.chezmoi.subprocess.run",
            return_value=_mock_proc(stdout=doctor_output),
        ):
            _check_chezmoi_doctor(result)
        assert result.passed is True
        assert result.warning_count == 2

    def test_two_token_line_no_duplicate(self) -> None:
        """Two-token doctor line should not duplicate the check-name as message."""
        doctor_output = "warning  check-name\n"
        result = ValidationResult()
        with patch(
            "mde.validate.chezmoi.subprocess.run",
            return_value=_mock_proc(stdout=doctor_output),
        ):
            _check_chezmoi_doctor(result)
        findings = [f for f in result.findings if f.rule == "chezmoi.doctor"]
        assert len(findings) == 1
        # The message should NOT contain the check-name twice
        msg = findings[0].message
        assert msg.count("check-name") == 1

    def test_ok_and_info_lines_ignored(self) -> None:
        """Lines with ok/info severity should not produce findings."""
        doctor_output = "ok        version       v2.70.0\ninfo      diff-command  not set\n"
        result = ValidationResult()
        with patch(
            "mde.validate.chezmoi.subprocess.run",
            return_value=_mock_proc(stdout=doctor_output),
        ):
            _check_chezmoi_doctor(result)
        assert len(result.findings) == 0

    def test_multiple_warnings_all_surfaced(self) -> None:
        """Every warning must be surfaced — no filtering of any kind."""
        doctor_output = (
            "warning  working-tree       ~/project is dirty\n"
            "warning  suspicious-entries  ~/project/.chezmoisource\n"
            "warning  new-check          something unexpected\n"
        )
        result = ValidationResult()
        with patch(
            "mde.validate.chezmoi.subprocess.run",
            return_value=_mock_proc(stdout=doctor_output),
        ):
            _check_chezmoi_doctor(result)
        findings = [f for f in result.findings if f.rule == "chezmoi.doctor"]
        assert len(findings) == 3
        assert all(f.severity == Severity.WARNING for f in findings)
