"""Maintenance update lifecycle."""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def run_update() -> int:
    """Run the maintenance update lifecycle.

    Each step is a (label, callable, fatal) triple.  Fatal steps
    increment the failure counter; non-fatal steps only emit a warning.
    After all steps, ``validate_all`` runs as a final verification.

    Step ordering rationale (see Issue: missing tools after update):
    1. brew update/upgrade  -- OS-level packages first
    2. mise self-update     -- ensure mise itself is current
    3. mise upgrade         -- upgrade tools to new versions (uninstalls old)
    4. mise lock --global   -- refresh global lockfile so "latest" resolves
                               to the newly upgraded versions, NOT stale pins
    5. mise prune           -- remove orphan old versions BEFORE install
    6. mise install         -- install any missing tools (uses fresh lockfile)
    7. mise reshim          -- regenerate shims for new versions
    8. chezmoi apply        -- sync dotfiles

    Returns:
        Exit code.
    """
    steps: list[tuple[str, Callable[[], int], bool]] = [
        ("brew update && brew upgrade", _run_brew_update, True),
        ("mise self-update", _run_mise_self_update, False),
        ("mise upgrade", _run_mise_upgrade, True),
        ("mise lock --global", _run_mise_lock, False),
        ("mise prune", _run_mise_prune, False),
        ("mise install", _run_mise_install, True),
        ("mise reshim", _run_mise_reshim, False),
        ("chezmoi apply", _run_chezmoi_apply, False),
    ]
    failures = 0
    for label, func, fatal in steps:
        print(f"==> {label}")
        if func() != 0:
            if fatal:
                print(f"  FAIL: {label}")
                failures += 1
            else:
                print(f"  WARN: {label} had issues (non-fatal)")

    # Post-cycle health check: verify no tools went missing
    print("==> mise doctor (post-cycle health check)")
    doctor_ok = _run_mise_doctor()
    if doctor_ok != 0:
        print("  FAIL: mise doctor reported issues after update cycle")
        failures += 1

    # Final verification
    print("==> verify (validate_all)")
    from mde.validate import validate_all

    validate_all(fix=False)

    return 1 if failures > 0 else 0


def _run_brew_update() -> int:
    """Run brew update then brew upgrade.

    brew update failure is fatal (tap index must refresh).
    brew upgrade failure is non-fatal --- individual package
    failures (casks needing sudo, removed formulae, transient
    network errors) should not block the rest of the lifecycle.
    """
    if not shutil.which("brew"):
        return 0
    proc = subprocess.run(["brew", "update"], timeout=120)
    if proc.returncode != 0:
        return 1
    proc = subprocess.run(["brew", "upgrade"], timeout=300)
    if proc.returncode != 0:
        print(f"  brew upgrade exited {proc.returncode} (non-fatal)")
    return 0


def _run_mise_self_update() -> int:
    if not shutil.which("mise"):
        return 0
    try:
        proc = subprocess.run(["mise", "self-update", "--yes"], timeout=120)
    except (subprocess.TimeoutExpired, OSError):
        return 1
    else:
        return proc.returncode


def _run_mise_upgrade() -> int:
    if not shutil.which("mise"):
        return 1
    proc = subprocess.run(["mise", "upgrade", "--yes"], timeout=600)
    return proc.returncode


def _run_mise_lock() -> int:
    """Refresh both project and global lockfiles for this platform only.

    The --global flag is critical: without it, only the project-level
    lockfile is updated. The global lockfile at ~/.config/mise/mise.lock
    pins specific versions for "latest" resolution. If it is stale after
    ``mise upgrade``, ``mise install`` will reinstall OLD versions that
    ``mise prune`` then removes -- wasting time and risking missing tools.

    The --platform flag limits lock to the current machine's platform,
    avoiding unnecessary checksum resolution for linux/windows platforms
    that this macOS machine will never use.

    Logs failures for each lock command and returns the first non-zero
    exit code encountered so the caller can surface the failure.
    """
    if not shutil.which("mise"):
        return 0
    platform = _detect_platform()
    commands = [
        ["mise", "lock", "--platform", platform],
        ["mise", "lock", "--global", "--platform", platform],
    ]
    return_code = 0
    for command in commands:
        command_label = " ".join(command)
        try:
            proc = subprocess.run(command, timeout=120)
        except (subprocess.TimeoutExpired, OSError) as exc:
            print(f"  {command_label} failed: {exc}")
            if return_code == 0:
                return_code = 1
            continue
        if proc.returncode != 0:
            print(f"  {command_label} exited {proc.returncode}")
            if return_code == 0:
                return_code = proc.returncode
    return return_code


def _detect_platform() -> str:
    """Detect the current platform in mise's format (e.g., macos-arm64)."""
    import platform as _platform

    system = _platform.system().lower()
    machine = _platform.machine().lower()

    os_map = {"darwin": "macos", "linux": "linux", "windows": "windows"}
    arch_map = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64", "amd64": "x64"}

    os_name = os_map.get(system, system)
    arch_name = arch_map.get(machine, machine)
    return f"{os_name}-{arch_name}"


def _run_mise_reshim() -> int:
    if not shutil.which("mise"):
        return 0
    try:
        proc = subprocess.run(["mise", "reshim"], timeout=60)
    except (subprocess.TimeoutExpired, OSError):
        return 1
    else:
        return proc.returncode


def _run_mise_install() -> int:
    if not shutil.which("mise"):
        return 1
    proc = subprocess.run(["mise", "install", "--yes"], timeout=300)
    return proc.returncode


def _run_mise_prune() -> int:
    if not shutil.which("mise"):
        return 0
    proc = subprocess.run(["mise", "prune", "--yes"], timeout=60)
    return proc.returncode


def _run_mise_doctor() -> int:
    """Run mise doctor to verify tool health after the update cycle."""
    if not shutil.which("mise"):
        return 1
    proc = subprocess.run(["mise", "doctor"], timeout=60)
    return proc.returncode


def _run_chezmoi_apply() -> int:
    if not shutil.which("chezmoi"):
        return 0
    try:
        proc = subprocess.run(["chezmoi", "apply", "--force"], timeout=120)
    except (subprocess.TimeoutExpired, OSError):
        return 1
    else:
        return proc.returncode
