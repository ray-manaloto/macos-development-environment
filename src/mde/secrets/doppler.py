"""Doppler CLI wrapper for secrets management."""

from __future__ import annotations

import json
import shutil
import subprocess

from mde.log import logger

_PROJECT = "dotfiles"
_CONFIG = "dev"


def is_doppler_available() -> bool:
    """Return True if the doppler CLI binary is available on PATH."""
    return shutil.which("doppler") is not None


def doppler_list_secrets(*, project: str = _PROJECT, config: str = _CONFIG) -> dict[str, str]:
    """Download all secrets from Doppler as a dict.

    Returns an empty dict on failure and logs the error.
    """
    result = subprocess.run(
        [
            "doppler",
            "secrets",
            "download",
            "--project",
            project,
            "--config",
            config,
            "--no-file",
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        logger.bind(stderr=result.stderr).error("doppler_list_failed")
        return {}
    return json.loads(result.stdout)


def doppler_get_secret(key: str, *, project: str = _PROJECT, config: str = _CONFIG) -> str | None:
    """Fetch a single secret value from Doppler. Returns None on failure."""
    result = subprocess.run(
        [
            "doppler",
            "secrets",
            "get",
            key,
            "--project",
            project,
            "--config",
            config,
            "--plain",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def doppler_set_secrets(
    secrets: dict[str, str],
    *,
    project: str = _PROJECT,
    config: str = _CONFIG,
) -> int:
    """Upload key/value pairs to Doppler. Returns the CLI exit code."""
    if not secrets:
        return 0
    pairs = [f"{k}={v}" for k, v in secrets.items()]
    result = subprocess.run(
        [
            "doppler",
            "secrets",
            "set",
            *pairs,
            "--project",
            project,
            "--config",
            config,
            "--silent",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        logger.bind(stderr=result.stderr).error("doppler_set_failed")
    return result.returncode
