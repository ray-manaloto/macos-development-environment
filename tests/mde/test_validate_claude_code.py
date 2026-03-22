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
    result = subprocess.run(
        ["mise", "current", _MISE_TOOL],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0 and "trust" in result.stderr.lower():
        pytest.skip(f"mise config not trusted in this directory: {result.stderr.strip()}")
    assert result.returncode == 0, f"mise current {_MISE_TOOL} failed:\n{result.stderr}"
    assert result.stdout.strip(), "claude-code version is empty"


def test_claude_code_version_is_current() -> None:
    """Installed version matches GitHub latest release.

    We check against GitHub releases (the authoritative source) because
    the aqua registry mirrors releases with a lag. The npm: backend
    in mise reads from the npm registry, which is always current.

    If this fails, run: mise upgrade "npm:@anthropic-ai/claude-code"
    """
    if not shutil.which("gh"):
        pytest.skip("gh CLI not available")

    installed = subprocess.run(
        ["mise", "current", _MISE_TOOL],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if installed.returncode != 0:
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
