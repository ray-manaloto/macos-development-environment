"""Secrets management modules."""

from __future__ import annotations

__all__ = ["dispatch_secrets"]


def dispatch_secrets(
    action: str,
    *,
    key: str | None = None,
    value: str | None = None,
    project: str | None = None,
    config: str | None = None,
) -> int:
    """Dispatch a ``mde-py secrets`` subcommand.

    Args:
        action: One of ``sync``, ``validate``, ``add``, ``update``, ``rm``,
            ``bootstrap-config``, ``doctor``.
        key: Secret key (required for ``add``/``update``/``rm``).
        value: Explicit secret value (optional for ``add``/``update``).
        project: Doppler project override.
        config: Doppler config override.

    Returns:
        Exit code.
    """
    kwargs: dict[str, str] = {}
    if project is not None:
        kwargs["project"] = project
    if config is not None:
        kwargs["config"] = config
    return _dispatch(action, key, value, kwargs)


def _dispatch(
    action: str,
    key: str | None,
    value: str | None,
    kwargs: dict[str, str],
) -> int:
    """Internal dispatch helper (kept small to satisfy complexity limit)."""
    if action in {"add", "update", "rm"}:
        return _dispatch_crud(action, key, value, kwargs)
    if action == "sync":
        from mde.secrets.sync import sync_doppler_to_fnox

        return sync_doppler_to_fnox(**kwargs)
    if action == "validate":
        from mde.secrets.validate_parity import validate_secrets_parity

        return validate_secrets_parity(**kwargs)
    if action == "bootstrap-config":
        from mde.secrets.manage import bootstrap_config

        return bootstrap_config(**kwargs)
    if action == "doctor":
        from mde.secrets.manage import doctor

        return doctor()
    return 1


def _dispatch_crud(
    action: str,
    key: str | None,
    value: str | None,
    kwargs: dict[str, str],
) -> int:
    """Handle ``add``/``update``/``rm`` dispatch."""
    if not key:
        print(f"error: 'key' is required for {action}", flush=True)
        return 3
    if action in {"add", "update"}:
        from mde.secrets.manage import add_secret

        return add_secret(key, value, **kwargs)
    from mde.secrets.manage import remove_secret

    return remove_secret(key, **kwargs)
