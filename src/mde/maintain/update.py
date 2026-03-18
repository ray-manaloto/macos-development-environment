"""Maintenance update lifecycle."""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def run_update() -> int:
    """Run the maintenance update lifecycle.

    Delegates to mise and brew update, then validates configs.

    Returns:
        Exit code.
    """
    steps: list[tuple[str, Callable[[], int]]] = [
        ("brew update && brew upgrade", _run_brew_update),
        ("mise install", _run_mise_install),
        ("mise prune", _run_mise_prune),
    ]
    failures = 0
    for label, func in steps:
        print(f"==> {label}")
        if func() != 0:
            print(f"  WARN: {label} had issues")
            failures += 1
    return 1 if failures > 0 else 0


def _run_brew_update() -> int:
    if not shutil.which("brew"):
        return 0
    proc = subprocess.run(
        ["brew", "update"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        return 1
    proc = subprocess.run(
        ["brew", "upgrade"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    return proc.returncode


def _run_mise_install() -> int:
    if not shutil.which("mise"):
        return 1
    proc = subprocess.run(
        ["mise", "install", "--yes"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    return proc.returncode


def _run_mise_prune() -> int:
    if not shutil.which("mise"):
        return 0
    proc = subprocess.run(
        ["mise", "prune", "--yes"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return proc.returncode
