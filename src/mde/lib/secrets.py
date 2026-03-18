"""Secrets loading utilities (migrated from lib/mde-secrets.sh)."""

from __future__ import annotations

import os
import shutil
import subprocess


def load_secrets() -> dict[str, str]:
    """Load secrets from fnox into environment variables.

    Returns:
        Dict of loaded secret key-value pairs.
    """
    loaded: dict[str, str] = {}
    if not shutil.which("fnox"):
        return loaded

    try:
        proc = subprocess.run(
            ["fnox", "env"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if "=" in line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    if key:
                        os.environ[key] = value
                        loaded[key] = value
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return loaded
