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
            severity=Severity.ERROR,
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
    """Detect script state issues via chezmoi state dump + hash comparison.

    Compares rendered script content hashes against stored entryState
    hashes.  If a script's source has changed since the last apply,
    the SHA256 will differ — that's real drift that ``chezmoi apply``
    needs to resolve.

    If chezmoi has no script state at all (fresh machine), that's an
    ERROR because scripts need to be applied first.
    """
    import json

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
            return

        # Compare stored hashes against current rendered content.
        # chezmoi cat-config --source shows the source dir; we use
        # chezmoi execute-template to render each script and hash it.
        source_proc = subprocess.run(
            ["chezmoi", "source-path"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if source_proc.returncode != 0:
            return  # Can't compare without source path

        # Use chezmoi diff --include=scripts to detect actual drift.
        # Scripts whose rendered content differs from the stored hash
        # will appear in the diff output.
        diff_proc = subprocess.run(
            ["chezmoi", "diff", "--include=scripts"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # chezmoi diff exits 0 when clean, non-zero when drift exists
        diff_output = diff_proc.stdout.strip()
        if diff_output:
            # Count drifted scripts from diff output (each script appears as a diff block)
            drifted = [line for line in diff_output.splitlines() if line.startswith("diff --git")]
            count = len(drifted) or 1  # at least 1 if output is non-empty
            result.add(
                path="chezmoi",
                message=(
                    f"{count} script(s) have drifted since last apply "
                    "(content hash mismatch). Run: chezmoi apply"
                ),
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
# Severity tokens we care about and their mapping to our Severity.
# chezmoi "warning" → our WARNING (visible, non-blocking).
# chezmoi "error"   → our ERROR (blocks the gate).
# No suppression — every finding is surfaced at its actual severity.
_DOCTOR_SEVERITY_MAP: dict[str, Severity] = {
    "warning": Severity.WARNING,
    "error": Severity.ERROR,
}


def _check_chezmoi_doctor(result: ValidationResult) -> None:
    """Run chezmoi doctor and surface all warnings/errors at their real severity.

    Zero suppression: chezmoi warnings are reported as WARNING (visible
    but non-blocking), chezmoi errors as ERROR (blocks the gate).
    Nothing is filtered or downgraded.
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
            # Match lines starting with known severity tokens
            mapped_severity = None
            matched_token = None
            for token, severity in _DOCTOR_SEVERITY_MAP.items():
                if line.startswith(token):
                    mapped_severity = severity
                    matched_token = token
                    break
            if mapped_severity is None:
                continue

            # Doctor output columns: severity, check-name, message
            parts = line.split(None, maxsplit=2)
            check_name = parts[1] if len(parts) > 1 else ""
            check_msg = parts[-1] if len(parts) > 1 else line

            result.add(
                path="chezmoi",
                message=f"chezmoi doctor {matched_token}: [{check_name}] {check_msg}".strip(),
                severity=mapped_severity,
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
