"""Query mise for dynamically managed tool sets."""

from __future__ import annotations

import json
import shutil
import subprocess


def fetch_mise_owned_packages() -> tuple[set[str], set[str]]:
    """Return (npm_packages, pipx_tools) managed by mise.

    Parses ``mise ls --json`` keys for ``npm:`` and ``pipx:`` prefixes.
    Falls back to empty sets if mise is unavailable or output is invalid.
    """
    if not shutil.which("mise"):
        return set(), set()
    try:
        proc = subprocess.run(
            ["mise", "ls", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            return set(), set()
        data: dict[str, object] = json.loads(proc.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return set(), set()

    npm_packages: set[str] = set()
    pipx_tools: set[str] = set()
    for key in data:
        if key.startswith("npm:"):
            npm_packages.add(key.removeprefix("npm:"))
        elif key.startswith("pipx:"):
            pipx_tools.add(key.removeprefix("pipx:"))
    return npm_packages, pipx_tools
