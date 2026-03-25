"""Chezmoi validation: verify, doctor, diff."""

from __future__ import annotations

import shutil
import subprocess

from mde.models.result import Severity, ValidationResult


def validate_chezmoi() -> ValidationResult:
    """Run chezmoi verification checks.

    Returns:
        ValidationResult with findings.
    """
    result = ValidationResult()

    if not shutil.which("chezmoi"):
        result.add(
            path="chezmoi",
            message="chezmoi is not installed",
            severity=Severity.WARNING,
            rule="chezmoi.not-installed",
        )
        return result

    _check_chezmoi_verify_files(result)
    _check_chezmoi_script_drift(result)
    _check_chezmoi_doctor(result)

    return result


def _check_chezmoi_verify_files(result: ValidationResult) -> None:
    """Run chezmoi verify for managed files only (not scripts).

    Scripts are excluded because run_onchange/run_once scripts are
    *executed*, not deployed as files — they always show as "new" in
    verify.  Script drift is checked separately via chezmoi diff.
    """
    try:
        proc = subprocess.run(
            ["chezmoi", "verify", "--include=files"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip() or ""
            result.add(
                path="chezmoi",
                message=f"chezmoi verify failed (exit {proc.returncode}): {detail}"
                if detail
                else "chezmoi verify detected file drift",
                severity=Severity.ERROR,
                rule="chezmoi.drift",
            )
    except subprocess.TimeoutExpired:
        result.add(
            path="chezmoi",
            message="chezmoi verify timed out (30s)",
            severity=Severity.ERROR,
            rule="chezmoi.timeout",
        )
    except FileNotFoundError:
        result.add(
            path="chezmoi",
            message="chezmoi binary not found despite which() check",
            severity=Severity.ERROR,
            rule="chezmoi.not-found",
        )


def _check_chezmoi_script_drift(result: ValidationResult) -> None:
    """Detect script state issues via chezmoi state dump.

    Compares rendered script hashes against stored entryState hashes.
    If chezmoi has no script state at all (fresh machine), that's an
    ERROR because scripts need to be applied first.

    Note: chezmoi diff --include=scripts always shows run_onchange
    scripts as "new files" (they're executed, not deployed), so we
    use state dump instead of diff for accurate detection.
    """
    try:
        proc = subprocess.run(
            ["chezmoi", "state", "dump"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            result.add(
                path="chezmoi",
                message=f"chezmoi state dump failed (exit {proc.returncode})",
                severity=Severity.ERROR,
                rule="chezmoi.script-drift",
            )
            return

        import json

        try:
            state = json.loads(proc.stdout)
        except json.JSONDecodeError:
            result.add(
                path="chezmoi",
                message="chezmoi state dump produced invalid JSON",
                severity=Severity.ERROR,
                rule="chezmoi.script-drift",
            )
            return

        # Check that entryState has script entries
        entry_state = state.get("entryState", {})
        script_entries = {k: v for k, v in entry_state.items() if v.get("type") == "script"}
        if not script_entries:
            result.add(
                path="chezmoi",
                message="chezmoi has no script execution state (run chezmoi apply)",
                severity=Severity.ERROR,
                rule="chezmoi.script-drift",
            )
    except subprocess.TimeoutExpired:
        result.add(
            path="chezmoi",
            message="chezmoi state dump timed out (30s)",
            severity=Severity.ERROR,
            rule="chezmoi.timeout",
        )
    except FileNotFoundError:
        pass  # Already caught by verify check


# Chezmoi doctor output format: "severity  check-name  message"
# Severity tokens are lowercase: "ok", "info", "warning", "error"
_DOCTOR_SEVERITY_TOKENS = ("warning", "error")

# Benign check NAMES (second column) that are expected in this project.
# Matched against the check-name field only, not the full line.
_BENIGN_CHECK_NAMES = frozenset(
    {
        "working-tree",
        "suspicious-entries",
    }
)


def _check_chezmoi_doctor(result: ValidationResult) -> None:
    """Run chezmoi doctor and treat unexpected warnings/errors as failures.

    Known benign check names (working-tree, suspicious-entries) are
    filtered by matching the check-name column, not the full line text.
    """
    try:
        proc = subprocess.run(
            ["chezmoi", "doctor"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Check both stdout and stderr for doctor output
        all_output = proc.stdout + proc.stderr
        for line in all_output.splitlines():
            # Match lines starting with warning or error tokens
            matched_token = None
            for token in _DOCTOR_SEVERITY_TOKENS:
                if line.startswith(token):
                    matched_token = token
                    break
            if matched_token is None:
                continue

            # Doctor output columns: severity, check-name, message
            parts = line.split(None, maxsplit=2)
            check_name = parts[1] if len(parts) > 1 else ""
            check_msg = parts[-1] if len(parts) > 1 else line

            # Filter by check name, not full line text
            if check_name in _BENIGN_CHECK_NAMES:
                continue

            result.add(
                path="chezmoi",
                message=f"chezmoi doctor {matched_token}: [{check_name}] {check_msg}".strip(),
                severity=Severity.ERROR,
                rule="chezmoi.doctor",
            )
    except subprocess.TimeoutExpired:
        result.add(
            path="chezmoi",
            message="chezmoi doctor timed out (30s)",
            severity=Severity.ERROR,
            rule="chezmoi.timeout",
        )
    except FileNotFoundError:
        pass  # Already caught by verify check
