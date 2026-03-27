"""Export fnox keychain secrets to Doppler (one-time migration)."""

from __future__ import annotations

import subprocess

from mde.log import logger
from mde.secrets.doppler import doppler_set_secrets, is_doppler_available


def export_fnox_to_doppler() -> int:
    """Read all fnox keychain secrets and bulk-upload them to Doppler.

    Only entries with ``provider (keychain)`` are exported; age-encrypted
    and other provider types are skipped.

    Returns:
        0 on success, 1 on failure.
    """
    if not is_doppler_available():
        logger.error("doppler_not_available")
        return 1

    list_result = subprocess.run(
        ["fnox", "list"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if list_result.returncode != 0:
        logger.bind(stderr=list_result.stderr).error("fnox_list_failed")
        return 1

    keychain_keys: list[str] = []
    for line in list_result.stdout.splitlines():
        if "provider (keychain)" in line:
            key = line.split()[0]
            keychain_keys.append(key)

    logger.bind(count=len(keychain_keys)).info("fnox_keychain_keys_found")

    secrets: dict[str, str] = {}
    for key in keychain_keys:
        get_result = subprocess.run(
            ["fnox", "get", key],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if get_result.returncode != 0:
            logger.bind(key=key, stderr=get_result.stderr).warning("fnox_get_failed_skipping")
            continue
        secrets[key] = get_result.stdout.strip()

    logger.bind(count=len(secrets)).info("exporting_secrets_to_doppler")
    return doppler_set_secrets(secrets)
