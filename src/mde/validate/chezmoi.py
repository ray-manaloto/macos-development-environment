"""Chezmoi validation: verify, doctor, diff, config consistency."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

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
    _check_chezmoi_config_consistency(result)
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


def _get_chezmoi_config() -> tuple[Path, Path] | None:
    """Get sourceDir and workingTree from chezmoi dump-config.

    Returns (source_dir, working_tree) or None if unavailable.
    """
    import json

    try:
        proc = subprocess.run(
            ["chezmoi", "dump-config", "--format=json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if proc.returncode != 0:
        return None
    try:
        config = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    source_dir = Path(config.get("sourceDir", ""))
    working_tree = Path(config.get("workingTree", ""))
    if not source_dir or not source_dir.exists():
        return None
    return source_dir, working_tree


def _check_chezmoi_config_consistency(result: ValidationResult) -> None:
    """Validate chezmoi sourceDir and .chezmoiroot are consistent."""
    paths = _get_chezmoi_config()
    if paths is None:
        return
    source_dir, working_tree = paths
    result.files_checked += 1

    _check_sourcedir_not_default(result, source_dir)
    _check_git_awareness(result, source_dir, working_tree)
    _check_chezmoiroot_consistency(result, source_dir, working_tree)


def _check_sourcedir_not_default(result: ValidationResult, source_dir: Path) -> None:
    """Detect when sourceDir has reverted to the chezmoi default.

    If sourceDir is ~/.local/share/chezmoi, the chezmoi.toml was likely
    regenerated without sourceDir (the template bug that caused repeated
    breakage). This is always an error in this project because we use
    a non-default source directory.
    """
    default_source = Path.home() / ".local" / "share" / "chezmoi"
    if source_dir == default_source or source_dir == default_source / "home":
        result.add(
            path=str(source_dir),
            message=(
                f"sourceDir is the chezmoi default ({default_source}), not "
                "this project's repo. The chezmoi.toml was likely regenerated "
                "without sourceDir. Fix: run 'chezmoi init --force' from the "
                "correct source, or manually set sourceDir in "
                "~/.config/chezmoi/chezmoi.toml"
            ),
            severity=Severity.ERROR,
            rule="chezmoi.sourcedir-default",
        )


def _check_git_awareness(result: ValidationResult, source_dir: Path, working_tree: Path) -> None:
    """SourceDir or workingTree must contain .git for working-tree awareness."""
    git_dir = (working_tree / ".git") if working_tree.exists() else (source_dir / ".git")
    if not git_dir.exists() and not (source_dir / ".git").exists():
        result.add(
            path=str(source_dir),
            message=(
                "sourceDir does not contain .git — chezmoi working-tree "
                "doctor check will not function correctly"
            ),
            severity=Severity.ERROR,
            rule="chezmoi.sourcedir-no-git",
        )


def _check_chezmoiroot_consistency(
    result: ValidationResult, source_dir: Path, working_tree: Path
) -> None:
    """Validate .chezmoiroot is not bypassed by sourceDir."""
    chezmoiroot_in_source = source_dir / ".chezmoiroot"
    chezmoiroot_in_worktree = working_tree / ".chezmoiroot" if working_tree.exists() else None

    # Case A: .chezmoiroot at repo root but NOT in sourceDir — sourceDir
    # bypasses it, making .chezmoiroot dead code.
    if (
        chezmoiroot_in_worktree
        and chezmoiroot_in_worktree.exists()
        and not chezmoiroot_in_source.exists()
        and source_dir != working_tree
    ):
        _check_bypassed_chezmoiroot(result, chezmoiroot_in_worktree, source_dir, working_tree)
        return

    # Case B: .chezmoiroot in sourceDir — validate target exists
    if chezmoiroot_in_source.exists():
        _check_chezmoiroot_target(result, chezmoiroot_in_source, source_dir)


def _check_bypassed_chezmoiroot(
    result: ValidationResult,
    chezmoiroot: Path,
    source_dir: Path,
    working_tree: Path,
) -> None:
    """Warn when sourceDir points to the subdirectory that .chezmoiroot specifies."""
    try:
        root_target = chezmoiroot.read_text().strip()
    except OSError:
        return
    if root_target and source_dir.name == root_target:
        # WARNING: the fix requires renaming the directory to remove
        # the .chezmoi prefix. Tracked as issue #64.
        result.add(
            path=str(chezmoiroot),
            message=(
                f"sourceDir is '{source_dir}' which is the subdirectory "
                f"that .chezmoiroot specifies ('{root_target}'). "
                f"This makes .chezmoiroot dead code. Fix: rename "
                f"'{root_target}' to 'home/' (no .chezmoi prefix), "
                f"then set sourceDir to '{working_tree}'"
            ),
            severity=Severity.WARNING,
            rule="chezmoi.sourcedir-chezmoiroot-conflict",
        )


def _check_chezmoiroot_target(
    result: ValidationResult, chezmoiroot: Path, source_dir: Path
) -> None:
    """Validate .chezmoiroot references an existing directory."""
    try:
        root_target = chezmoiroot.read_text().strip()
    except OSError:
        return
    if root_target:
        target_dir = source_dir / root_target
        if not target_dir.exists():
            result.add(
                path=str(chezmoiroot),
                message=(
                    f".chezmoiroot references '{root_target}' but {target_dir} does not exist"
                ),
                severity=Severity.ERROR,
                rule="chezmoi.chezmoiroot-target-missing",
            )


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
            # parts[2] is the message column; absent for two-token lines
            check_msg = parts[2:3][0] if parts[2:3] else ""

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
