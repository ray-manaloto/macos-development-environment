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

    Returns:
        Exit code.
    """
    steps: list[tuple[str, Callable[[], int], bool]] = [
        ("brew update && brew upgrade", _run_brew_update, True),
        ("mise self-update", _run_mise_self_update, False),
        ("mise upgrade", _run_mise_upgrade, True),
        ("mise lock", _run_mise_lock, False),
        ("mise reshim", _run_mise_reshim, False),
        ("mise install", _run_mise_install, True),
        ("mise prune", _run_mise_prune, False),
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

    # Final verification
    print("==> verify (validate_all)")
    from mde.validate import validate_all

    validate_all(fix=False)

    return 1 if failures > 0 else 0


def _run_brew_update() -> int:
    """Run brew update then brew upgrade.

    brew update failure is fatal (tap index must refresh).
    brew upgrade failure is non-fatal — individual package
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
    if not shutil.which("mise"):
        return 0
    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        subprocess.run(["mise", "lock"], timeout=60)
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


def _run_chezmoi_apply() -> int:
    if not shutil.which("chezmoi"):
        return 0
    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        subprocess.run(["chezmoi", "apply", "--force"], timeout=120)
    return 0
