"""Prune stale globals migrated to mise."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from mde.lib.mise_tools import fetch_mise_owned_packages

# Stale mise backends superseded by native installers or different backends.
_MISE_STALE_BACKENDS = [
    "aqua-anthropics-claude-code",
]

# Fallback lists used when `mise ls --json` is unavailable.
_UV_STALE_TOOLS = [
    "langchain-cli",
    "langgraph-cli",
    "langsmith-fetch",
    "aider-chat",
    "open-interpreter",
    "crewai",
    "skypilot",
]

_BUN_STALE_PACKAGES = [
    "@anthropic-ai/claude-code",
    "@openai/codex",
    "@google/gemini-cli",
    "openwork",
    "create-agent-chat-app",
    "@modelcontextprotocol/inspector",
]


def run_prune() -> int:
    """Prune stale uv/bun globals and orphan mise versions.

    Returns:
        Exit code.
    """
    _prune_stale_mise_backends()
    _prune_uv_tools()
    _prune_bun_globals()
    _prune_mise_orphans()
    return 0


def _prune_stale_mise_backends() -> None:
    """Remove mise install dirs for backends replaced by native installers."""
    installs = Path.home() / ".local" / "share" / "mise" / "installs"
    if not installs.is_dir():
        return
    removed = False
    for backend in _MISE_STALE_BACKENDS:
        target = installs / backend
        if target.is_dir():
            if not removed:
                print("==> Pruning stale mise backends replaced by native installers")
                removed = True
            print(f"  Removing {backend}")
            shutil.rmtree(target)


def _prune_uv_tools() -> None:
    if not shutil.which("uv"):
        return
    print("==> Pruning stale uv tools migrated to mise")

    _npm, pipx_tools = fetch_mise_owned_packages()
    stale = pipx_tools or set(_UV_STALE_TOOLS)

    proc = subprocess.run(
        ["uv", "tool", "list"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    installed = {
        line.split()[0]
        for line in proc.stdout.splitlines()
        if line.strip() and not line.startswith("-")
    }
    for tool in stale:
        if tool in installed:
            print(f"  Removing uv tool: {tool}")
            subprocess.run(
                ["uv", "tool", "uninstall", tool],
                capture_output=True,
                timeout=10,
            )


def _prune_bun_globals() -> None:
    if not shutil.which("bun"):
        return
    print("==> Pruning stale bun globals migrated to mise")

    npm_pkgs, _pipx = fetch_mise_owned_packages()
    stale = npm_pkgs or set(_BUN_STALE_PACKAGES)

    proc = subprocess.run(
        ["bun", "pm", "ls", "-g"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    for pkg in stale:
        if pkg in proc.stdout:
            print(f"  Removing bun global: {pkg}")
            subprocess.run(
                ["bun", "remove", "-g", pkg],
                capture_output=True,
                timeout=10,
            )


def _prune_mise_orphans() -> None:
    if not shutil.which("mise"):
        return
    print("==> Pruning orphan mise versions")
    subprocess.run(
        ["mise", "prune", "--yes"],
        capture_output=True,
        timeout=60,
    )
