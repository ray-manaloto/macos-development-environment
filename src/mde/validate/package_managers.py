"""Global tool deduplication validation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from mde.lib.mise_tools import fetch_mise_owned_packages
from mde.models.result import ValidationResult

# Fallback sets used when `mise ls --json` is unavailable.
_FALLBACK_NPM = {
    "@claude-flow/cli",
    "@langchain/langgraph-cli",
    "@langchain/langgraph-ui",
    "@langchain/langgraph-checkpoint-validation",
    "pyright",
    "typescript",
    "typescript-language-server",
    "create-langchain-integration",
    "create-langgraph",
    "agent-browser",
    "opencode",
}

_FALLBACK_PIPX = {"skillport", "specify-cli", "deepagents-cli"}

_SCOPED_PKG_PARTS = 2


def validate_package_managers() -> ValidationResult:
    """Check for global package manager tools that duplicate mise-owned tools."""
    result = ValidationResult()
    _check_bun_duplicates(result)
    _check_uv_duplicates(result)
    return result


def _check_bun_duplicates(result: ValidationResult) -> None:
    bun_global_dir = Path.home() / ".bun" / "install" / "global" / "node_modules"
    if not bun_global_dir.exists():
        return
    result.files_checked += 1

    npm_pkgs, _pipx = fetch_mise_owned_packages()
    owned = npm_pkgs or _FALLBACK_NPM

    for pkg_name in owned:
        parts = pkg_name.split("/")
        if len(parts) == _SCOPED_PKG_PARTS:
            pkg_path = bun_global_dir / parts[0] / parts[1]
        else:
            pkg_path = bun_global_dir / pkg_name
        if pkg_path.exists():
            result.add_warning(
                str(pkg_path),
                f"Bun global '{pkg_name}' duplicates mise-owned tool",
                rule="dedup.bun-global",
            )


def _check_uv_duplicates(result: ValidationResult) -> None:
    if not shutil.which("uv"):
        return
    try:
        proc = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            return
        result.files_checked += 1
        installed = set()
        for line in proc.stdout.splitlines():
            # uv tool list format: "toolname v1.2.3"
            parts = line.strip().split()
            if parts:
                installed.add(parts[0])

        _npm, pipx_tools = fetch_mise_owned_packages()
        owned = pipx_tools or _FALLBACK_PIPX

        for tool in owned:
            if tool in installed:
                result.add_warning(
                    "uv-tools",
                    f"uv tool '{tool}' duplicates mise-owned tool",
                    rule="dedup.uv-tool",
                )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
