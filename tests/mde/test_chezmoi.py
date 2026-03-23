"""Tests that chezmoi-managed files are in sync."""

from __future__ import annotations

import shutil
import subprocess

import pytest


@pytest.mark.integration
def test_chezmoi_verify() -> None:
    """Verify chezmoi reports zero errors."""
    if not shutil.which("chezmoi"):
        pytest.skip("chezmoi not available")
    result = subprocess.run(
        ["chezmoi", "verify"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"chezmoi verify failed:\n{result.stderr}"


@pytest.mark.integration
def test_chezmoi_managed_aliases() -> None:
    """The aliases zsh file must be managed by chezmoi."""
    if not shutil.which("chezmoi"):
        pytest.skip("chezmoi not available")
    result = subprocess.run(
        ["chezmoi", "managed", "--include=files"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if not result.stdout.strip():
        pytest.skip("chezmoi has no managed files (source dir may be empty)")
    assert "aliases" in result.stdout.lower(), (
        f"aliases zsh not managed by chezmoi.\nManaged files:\n{result.stdout[:500]}"
    )
