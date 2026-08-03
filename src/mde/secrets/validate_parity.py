"""Validate parity between Doppler and fnox secret declarations.

The new architecture (see docs/secrets-workflow.md) does not mirror Doppler
secrets 1:1 into the macOS Keychain. Instead, global ``~/.config/fnox/config.toml``
declares each secret with ``provider = "doppler_<project>_<config>"`` and the
ciphertext is cached under a ``sync`` field via ``fnox sync --provider age``.

Parity is therefore defined as: every key in Doppler (minus bootstrap-only keys)
has a matching declaration in fnox whose source provider is the Doppler provider,
and no fnox declaration points at a Doppler key that no longer exists.
"""

from __future__ import annotations

import subprocess

from mde.log import logger
from mde.secrets.doppler import doppler_list_secrets, is_doppler_available

# Doppler auto-injects these meta keys; exclude from parity checks.
_DOPPLER_META = frozenset({"DOPPLER_CONFIG", "DOPPLER_ENVIRONMENT", "DOPPLER_PROJECT"})
# Bootstrap-only: AGE_PRIVATE_KEY is retrieved directly by the fresh-machine
# runbook, not declared as a fnox secret. DOPPLER_TOKEN is a keychain entry.
_BOOTSTRAP_ONLY = frozenset({"AGE_PRIVATE_KEY", "DOPPLER_TOKEN"})


def validate_secrets_parity(*, project: str = "dotfiles", config: str = "dev_personal") -> int:
    """Compare Doppler keys against fnox declarations sourced from Doppler.

    Returns:
        0 if every non-bootstrap Doppler key has a matching Doppler-sourced
        fnox declaration and vice versa, 1 if mismatches are found.
    """
    if not is_doppler_available():
        logger.error("doppler_not_available")
        return 1

    doppler_keys = (
        set(doppler_list_secrets(project=project, config=config).keys())
        - _DOPPLER_META
        - _BOOTSTRAP_ONLY
    )
    if not doppler_keys:
        logger.error("validate_no_doppler_secrets")
        return 1

    result = subprocess.run(
        ["fnox", "list", "--sources"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        logger.bind(stderr=result.stderr).error("fnox_list_failed")
        return 1

    # Collect fnox keys whose source provider starts with "doppler"
    # (i.e. declared with provider = "doppler_<project>_<config>").
    fnox_keys: set[str] = set()
    for line in result.stdout.splitlines():
        if "provider (doppler" in line:
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
