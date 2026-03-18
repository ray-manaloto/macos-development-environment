"""System health checks (doctor)."""

from __future__ import annotations

import shutil


def run_doctor() -> int:
    """Run system health checks.

    Checks for required tools and their versions.

    Returns:
        Exit code.
    """
    print("==> MDE Doctor")
    failures = 0

    required_tools = [
        "mise",
        "chezmoi",
        "brew",
        "git",
        "bash",
        "python3",
        "uv",
        "ruff",
    ]
    optional_tools = [
        "fnox",
        "sops",
        "age",
        "shellcheck",
        "sky",
    ]

    for tool in required_tools:
        if shutil.which(tool):
            print(f"  OK: {tool}")
        else:
            print(f"  FAIL: {tool} not found")
            failures += 1

    for tool in optional_tools:
        if shutil.which(tool):
            print(f"  OK: {tool}")
        else:
            print(f"  WARN: {tool} not found (optional)")

    return 1 if failures > 0 else 0
