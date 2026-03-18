"""Reference source management."""

from __future__ import annotations

import subprocess


def dispatch_refs(action: str, *, dry_run: bool = False) -> int:
    """Dispatch refs subcommand.

    Args:
        action: The refs action to perform.
        dry_run: If True, print what would be done.

    Returns:
        Exit code.
    """
    if action == "clone-frameworks":
        return _clone_frameworks(dry_run=dry_run)
    if action == "refresh":
        return _refresh_refs()
    if action == "verify":
        return _verify_refs()
    return 1


def _clone_frameworks(*, dry_run: bool = False) -> int:
    """Clone agent framework repos for offline research."""
    if dry_run:
        print("Would clone agent framework repos")
        return 0
    proc = subprocess.run(
        ["bash", "scripts/clone-agent-framework-repos.sh"],
        timeout=600,
        env={"GIT_TERMINAL_PROMPT": "0"},
    )
    return proc.returncode


def _refresh_refs() -> int:
    """Refresh reference bundle metadata."""
    proc = subprocess.run(
        ["bash", "scripts/mde-refs-refresh.sh"],
        timeout=60,
    )
    return proc.returncode


def _verify_refs() -> int:
    """Verify reference bundle metadata."""
    proc = subprocess.run(
        ["bash", "scripts/mde-refs-verify.sh"],
        timeout=30,
    )
    return proc.returncode
