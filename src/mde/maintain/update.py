"""Maintenance update lifecycle."""

from __future__ import annotations

import contextlib
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
    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        subprocess.run(["mise", "self-update", "--yes"], timeout=120)
    return 0


def _run_mise_upgrade() -> int:
    if not shutil.which("mise"):
        return 1
    proc = subprocess.run(["mise", "upgrade", "--yes"], timeout=600)
    return proc.returncode


def _run_mise_lock() -> int:
    """Refresh both project and global lockfiles.

    The --global flag is critical: without it, only the project-level
    lockfile is updated. The global lockfile at ~/.config/mise/mise.lock
    pins specific versions for "latest" resolution. If it is stale after
    ``mise upgrade``, ``mise install`` will reinstall OLD versions that
    ``mise prune`` then removes -- wasting time and risking missing tools.
    """
    if not shutil.which("mise"):
        return 0
    # Update project lockfile
    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        subprocess.run(["mise", "lock"], timeout=120)
    # Update global lockfile (the critical fix)
    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        subprocess.run(["mise", "lock", "--global"], timeout=120)
    return 0


def _run_mise_reshim() -> int:
    if not shutil.which("mise"):
        return 0
    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        subprocess.run(["mise", "reshim"], timeout=60)
    return 0


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
    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        subprocess.run(["chezmoi", "apply", "--force"], timeout=120)
    return 0
