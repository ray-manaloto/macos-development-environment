"""Global tool deduplication validation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from mde.models.result import ValidationResult

# Packages known to be in mise config — bun globals of these are duplicates
MISE_OWNED_NPM = {
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

MISE_OWNED_PIPX = {"skillport", "specify-cli", "deepagents-cli"}

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
    for pkg_name in MISE_OWNED_NPM:
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
        for tool in MISE_OWNED_PIPX:
            if tool in installed:
                result.add_warning(
                    "uv-tools",
                    f"uv tool '{tool}' duplicates mise-owned tool",
                    rule="dedup.uv-tool",
                )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
