"""Secrets management modules."""

from __future__ import annotations


def dispatch_secrets(action: str) -> int:
    """Dispatch secrets subcommand.

    Args:
        action: The secrets action to perform.

    Returns:
        Exit code.
    """
    if action == "refresh":
        from mde.secrets.sops import refresh_secrets

        return refresh_secrets()
    if action == "smoke":
        from mde.secrets.smoke import run_smoke_test

        return run_smoke_test()
    if action == "export":
        from mde.secrets.export_to_doppler import export_fnox_to_doppler

        return export_fnox_to_doppler()
    return 1
