"""Validate parity between Doppler and fnox secrets."""

from __future__ import annotations

import subprocess

from mde.log import logger
from mde.secrets.doppler import doppler_list_secrets, is_doppler_available

# Doppler auto-injects these meta keys; exclude from parity checks.
_DOPPLER_META = frozenset({"DOPPLER_CONFIG", "DOPPLER_ENVIRONMENT", "DOPPLER_PROJECT"})


def validate_secrets_parity(*, project: str = "dotfiles", config: str = "dev") -> int:
    """Compare Doppler secrets against fnox/Keychain entries.

    Returns:
        0 if all Doppler keys exist in fnox, 1 if mismatches found.
    """
    if not is_doppler_available():
        logger.error("doppler_not_available")
        return 1

    doppler_keys = set(doppler_list_secrets(project=project, config=config).keys()) - _DOPPLER_META
    if not doppler_keys:
        logger.error("validate_no_doppler_secrets")
        return 1

    # Get fnox keychain keys
    result = subprocess.run(
        ["fnox", "list"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        logger.bind(stderr=result.stderr).error("fnox_list_failed")
        return 1

    fnox_keys: set[str] = set()
    for line in result.stdout.strip().splitlines():
        if "provider (keychain)" in line:
            parts = line.split()
            if parts:
                fnox_keys.add(parts[0])

    only_doppler = doppler_keys - fnox_keys
    only_fnox = fnox_keys - doppler_keys

    if only_doppler:
        logger.bind(keys=sorted(only_doppler)).warning("secrets_only_in_doppler")
    if only_fnox:
        logger.bind(keys=sorted(only_fnox)).warning("secrets_only_in_fnox")

    if only_doppler or only_fnox:
        logger.bind(
            doppler_count=len(doppler_keys),
            fnox_count=len(fnox_keys),
            only_doppler=len(only_doppler),
            only_fnox=len(only_fnox),
        ).error("secrets_parity_failed")
        return 1

    logger.bind(count=len(doppler_keys)).info("secrets_parity_ok")
    return 0
