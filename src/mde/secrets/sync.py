"""Sync secrets from Doppler to local fnox/Keychain."""

from __future__ import annotations

import subprocess

from mde.log import logger
from mde.secrets.doppler import doppler_list_secrets, is_doppler_available


def sync_doppler_to_fnox(*, project: str = "dotfiles", config: str = "dev") -> int:
    """Download secrets from Doppler and set them in fnox/Keychain.

    Returns:
        Exit code (0 = success).
    """
    if not is_doppler_available():
        logger.error("doppler_not_available")
        return 1

    secrets = doppler_list_secrets(project=project, config=config)
    if not secrets:
        logger.error("doppler_sync_no_secrets")
        return 1

    failed = 0
    for key, value in secrets.items():
        try:
            result = subprocess.run(
                ["fnox", "set", key, value, "--provider", "keychain", "--global"],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except subprocess.TimeoutExpired:
            logger.bind(key=key).error("fnox_set_timeout")
            failed += 1
            continue
        if result.returncode != 0:
            logger.bind(key=key, stderr=result.stderr).error("fnox_set_failed")
            failed += 1

    if failed:
        logger.bind(failed=failed, total=len(secrets)).warning("doppler_sync_partial")
        return 1

    logger.bind(count=len(secrets)).info("doppler_sync_complete")
    return 0
