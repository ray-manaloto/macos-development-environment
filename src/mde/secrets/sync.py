"""Sync secrets from Doppler to the local fnox age-encrypted cache."""

from __future__ import annotations

import subprocess

from mde.log import logger
from mde.secrets.doppler import is_doppler_available


def sync_doppler_to_fnox(*, project: str = "dotfiles", config: str = "dev_personal") -> int:
    """Run ``fnox sync --provider age --global --force``.

    The ``project``/``config`` arguments are retained for API compatibility but
    are resolved by fnox from ``~/.config/fnox/config.toml`` at sync time.

    Returns:
        Exit code (0 = success, 1 = failure).
    """
    del project, config  # resolved by fnox config, kept for API stability
    if not is_doppler_available():
        logger.error("doppler_not_available")
        return 1

    try:
        result = subprocess.run(
            ["fnox", "sync", "--provider", "age", "--global", "--force"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        logger.error("fnox_sync_timeout")
        return 1
    if result.returncode != 0:
        logger.bind(stderr=result.stderr).error("fnox_sync_failed")
        return 1
    logger.info("doppler_sync_complete")
    return 0
