"""Hook: per-team quality gate validation.

Reads ``{"team_type": "<type>"}`` from stdin and runs the appropriate
quality checks.  Prints structured JSON results to stdout and exits
with code 0 on success, 1 on failure.
"""

from __future__ import annotations

import json
import subprocess
import sys
from enum import Enum
from typing import Any


class TeamType(str, Enum):
    """Supported team types for quality gate dispatch."""

    PYTHON_DEV = "python-dev"
    RESEARCH = "research"
    DOTFILES = "dotfiles"
    INFRASTRUCTURE = "infrastructure"


def _run_cmd(cmd: list[str]) -> tuple[bool, str]:
    """Run *cmd* and return ``(passed, combined_output)``."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, f"command not found: {cmd[0]}"
    else:
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output


def _check(name: str, cmd: list[str]) -> dict[str, Any]:
    """Run a single named check and return a result dict."""
    passed, output = _run_cmd(cmd)
    return {"name": name, "passed": passed, "output": output}


# -- Per-team gate functions --------------------------------------------------


def gate_python_dev() -> list[dict[str, Any]]:
    """Run ruff, ty, and pytest checks for python-dev teams."""
    return [
        _check("ruff", ["uv", "run", "ruff", "check"]),
        _check("ty", ["uv", "run", "ty", "check"]),
        _check("pytest", ["uv", "run", "pytest", "--tb=short", "-q"]),
    ]


def gate_research(findings_path: str = "docs/research/trail/findings") -> list[dict[str, Any]]:
    """Verify research output files exist."""
    from pathlib import Path

    output_dir = Path(findings_path)
    if output_dir.is_dir() and any(output_dir.iterdir()):
        return [
            {
                "name": "research-output",
                "passed": True,
                "output": "findings directory has content",
            },
        ]
    return [
        {
            "name": "research-output",
            "passed": False,
            "output": "no research output files found",
        },
    ]


def gate_dotfiles() -> list[dict[str, Any]]:
    """Run ``mde-py validate --all`` for dotfiles teams."""
    return [
        _check("validate", ["uv", "run", "mde-py", "validate", "--all"]),
    ]


def gate_infrastructure() -> list[dict[str, Any]]:
    """Check brew packages and mise compatibility for infrastructure teams."""
    from pathlib import Path

    checks: list[dict[str, Any]] = []

    brewfile = Path("Brewfile")
    if brewfile.exists():
        checks.append(
            _check(
                "brew-bundle-check",
                ["brew", "bundle", "check", "--file", str(brewfile)],
            ),
        )
    else:
        checks.append(
            {
                "name": "brew-bundle-check",
                "passed": True,
                "output": "no Brewfile present, skipping",
            },
        )

    # mise doctor for general health
    checks.append(_check("mise-doctor", ["mise", "doctor"]))
    return checks


_GATE_DISPATCH: dict[str, Any] = {
    TeamType.PYTHON_DEV.value: gate_python_dev,
    TeamType.RESEARCH.value: gate_research,
    TeamType.DOTFILES.value: gate_dotfiles,
    TeamType.INFRASTRUCTURE.value: gate_infrastructure,
}


def run_team_quality_gate(team_type: str) -> dict[str, Any]:
    """Run the quality gate for *team_type* and return structured results."""
    gate_fn = _GATE_DISPATCH.get(team_type)
    if gate_fn is None:
        valid = ", ".join(sorted(_GATE_DISPATCH))
        return {
            "team_type": team_type,
            "passed": False,
            "checks": [],
            "error": f"unknown team_type: {team_type!r} (valid: {valid})",
        }

    checks = gate_fn()
    passed = all(c["passed"] for c in checks)
    return {"team_type": team_type, "passed": passed, "checks": checks}


def team_quality_gate_hook() -> int:
    """Entry point: read JSON from stdin, run per-team quality gate."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    team_type = data.get("team_type", "")
    if not team_type:
        return 0

    result = run_team_quality_gate(team_type)
    json.dump(result, sys.stdout)
    return 0 if result["passed"] else 1
