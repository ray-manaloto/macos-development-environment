"""Tests that claude-code is installed via mise and version-current."""

from __future__ import annotations

import shutil
import subprocess

import pytest

_MISE_TOOL = "npm:@anthropic-ai/claude-code"


def test_claude_code_installed() -> None:
    """claude-code is mise-managed and resolves a version.

    If this fails, run: mise install "npm:@anthropic-ai/claude-code@latest"
    The mise config MUST use the npm: backend (not the registry shortname
    or aqua:) because the aqua mirror lags behind GitHub/npm releases.
    """
    if not shutil.which("mise"):
        pytest.skip("mise not available")
    result = subprocess.run(
        ["mise", "current", _MISE_TOOL],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0 and "trust" in result.stderr.lower():
        pytest.skip(f"mise config not trusted: {result.stderr.strip()}")
    if result.returncode != 0:
        pytest.skip(f"mise current failed: {result.stderr.strip()}")
    if not result.stdout.strip():
        pytest.skip(f"{_MISE_TOOL} not installed (no version set)")


def test_claude_code_version_is_current() -> None:
    """Installed version matches GitHub latest release.

    We check against GitHub releases (the authoritative source) because
    the aqua registry mirrors releases with a lag. The npm: backend
    in mise reads from the npm registry, which is always current.

    If this fails, run: mise upgrade "npm:@anthropic-ai/claude-code"
    """
    if not shutil.which("gh"):
        pytest.skip("gh CLI not available")

    if not shutil.which("mise"):
        pytest.skip("mise not available")
    installed = subprocess.run(
        ["mise", "current", _MISE_TOOL],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if installed.returncode != 0 or not installed.stdout.strip():
        pytest.skip("claude-code not installed via mise")

    latest = subprocess.run(
        [
            "gh",
            "release",
            "view",
            "--repo",
            "anthropics/claude-code",
            "--json",
            "tagName",
            "-q",
            ".tagName",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if latest.returncode != 0:
        pytest.skip(f"gh release view failed: {latest.stderr.strip()}")

    installed_ver = installed.stdout.strip()
    latest_ver = latest.stdout.strip().lstrip("v")

    assert installed_ver == latest_ver, (
        f"claude-code {installed_ver} behind GitHub latest {latest_ver}. "
        f'Run: mise upgrade "{_MISE_TOOL}"'
    )
