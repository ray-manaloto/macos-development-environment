"""Secrets CRUD manager: Doppler-first writes + fnox age sync propagation.

Exit codes:
    0 = success
    1 = Doppler write/delete failed (nothing changed locally)
    2 = Doppler OK but local sync/verify failed (cache may be stale)
    3 = invalid input (e.g. bad key name)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

from mde.log import logger
from mde.secrets.doppler import doppler_delete_secret, doppler_list_secrets, doppler_set_secrets

__all__ = [
    "add_secret",
    "bootstrap_config",
    "doctor",
    "remove_secret",
    "update_secret",
]

_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_DEFAULT_PROJECT = "dotfiles"
_DEFAULT_CONFIG = "dev_personal"
_AGE_KEY_PATH = Path.home() / ".config" / "mise" / "age.txt"
_FNOX_CONFIG_PATH = Path.home() / ".config" / "fnox" / "config.toml"
_MAX_SYNC_ATTEMPTS = 2
_AGE_FILE_MODE = 0o600
_INVALID_KEY_MSG = "invalid secret key name"


def _validate_key(key: str) -> None:
    """Raise ValueError if key does not match ``^[A-Z][A-Z0-9_]*$``."""
    if not _KEY_RE.match(key):
        msg = f"{_INVALID_KEY_MSG}: {key!r}"
        raise ValueError(msg)


def _read_secret_value(key: str, value_arg: str | None) -> str:
    """Resolve secret value from explicit arg, stdin, env var, or prompt."""
    if value_arg is not None:
        return value_arg
    if not sys.stdin.isatty():
        # Strip a single trailing newline but preserve internal whitespace.
        return sys.stdin.read().removesuffix("\n")
    env_value = os.environ.get("MDE_SECRET_VALUE")
    if env_value is not None:
        return env_value
    import getpass

    return getpass.getpass(f"Value for {key}: ")


def _sanitize_log(text: str) -> str:
    """Escape ``<``/``>`` so loguru's colorizer does not treat them as tags."""
    return text.replace("<", r"\<").replace(">", r"\>")


def _shell_quote(value: str) -> str:
    """Single-quote escape a value for safe ``export`` emission."""
    return "'" + value.replace("'", "'\\''") + "'"


def _fnox_sync_once() -> tuple[bool, str]:
    """Run ``fnox sync`` once. Returns (success, stderr_or_reason)."""
    cmd = ["fnox", "sync", "--provider", "age", "--global", "--force"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired as exc:
        return False, f"timeout after {exc.timeout}s"
    return result.returncode == 0, result.stderr


def _fnox_sync_with_retry() -> bool:
    """Run ``fnox sync`` with one bounded retry. Returns True on success."""
    last_stderr = ""
    for attempt in range(1, _MAX_SYNC_ATTEMPTS + 1):
        ok, stderr = _fnox_sync_once()
        if ok:
            return True
        last_stderr = stderr
        logger.bind(attempt=attempt, stderr=_sanitize_log(stderr)).warning("fnox_sync_retry")
        if attempt < _MAX_SYNC_ATTEMPTS:
            time.sleep(2)
    logger.bind(stderr=_sanitize_log(last_stderr)).error("fnox_sync_failed")
    return False


def _run_fnox_sync_age(
    *,
    verify_key: str | None = None,
    verify_value: str | None = None,
) -> int:
    """Run ``fnox sync --provider age --global --force`` with bounded retry.

    Retries once after a 2-second sleep on non-zero exit. After a successful
    sync, if ``verify_key`` is provided, re-reads the value via ``fnox get``
    and compares to ``verify_value``. Returns 0 on success, 2 on any failure
    or drift.
    """
    if not _fnox_sync_with_retry():
        return 2

    if verify_key is not None:
        try:
            verify = subprocess.run(
                ["fnox", "get", verify_key],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except subprocess.TimeoutExpired:
            logger.bind(key=verify_key).error("fnox_verify_timeout")
            return 2
        if verify.returncode != 0:
            logger.bind(key=verify_key, stderr=_sanitize_log(verify.stderr)).error(
                "fnox_verify_failed"
            )
            return 2
        if not verify.stdout.strip():
            logger.bind(key=verify_key).error("fnox_verify_missing")
            return 2
        got = verify.stdout.rstrip("\n")
        if verify_value is not None and got != verify_value:
            logger.bind(key=verify_key).error("fnox_verify_drift")
            return 2
    return 0


def add_secret(
    key: str,
    value: str | None = None,
    *,
    project: str = _DEFAULT_PROJECT,
    config: str = _DEFAULT_CONFIG,
) -> int:
    """Upsert a secret: write to Doppler, sync via fnox, emit export line."""
    try:
        _validate_key(key)
    except ValueError as exc:
        logger.bind(key=key).error("secrets_invalid_key")
        print(f"error: {exc}", file=sys.stderr)
        return 3
    try:
        resolved = _read_secret_value(key, value)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    doppler_rc = doppler_set_secrets({key: resolved}, project=project, config=config)
    if doppler_rc != 0:
        logger.bind(key=key).error("secrets_add_doppler_failed")
        return 1

    # Regenerate declarations so the new key has a fnox entry pointing at
    # the Doppler provider. Without this, fnox sync has nothing to encrypt
    # for a brand-new key.
    if bootstrap_config(project=project, config=config) != 0:
        return 2

    sync_rc = _run_fnox_sync_age(verify_key=key, verify_value=resolved)
    if sync_rc != 0:
        return sync_rc

    print(f"export {key}={_shell_quote(resolved)}")
    return 0


def update_secret(
    key: str,
    value: str | None = None,
    *,
    project: str = _DEFAULT_PROJECT,
    config: str = _DEFAULT_CONFIG,
) -> int:
    """Alias for :func:`add_secret` (upsert semantics)."""
    return add_secret(key, value, project=project, config=config)


def remove_secret(
    key: str,
    *,
    project: str = _DEFAULT_PROJECT,
    config: str = _DEFAULT_CONFIG,
) -> int:
    """Delete a secret from Doppler, sync, and emit an ``unset`` line."""
    try:
        _validate_key(key)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    doppler_rc = doppler_delete_secret(key, project=project, config=config)
    if doppler_rc != 0:
        logger.bind(key=key).error("secrets_remove_doppler_failed")
        return 1

    # Regenerate declarations so the removed key is dropped from the global
    # config, then sync re-encrypts the remaining keys.
    if bootstrap_config(project=project, config=config) != 0:
        return 2

    sync_rc = _run_fnox_sync_age()
    if sync_rc != 0:
        return sync_rc

    print(f"unset {key}")
    return 0


def _read_existing_config() -> dict[str, object]:
    """Load ``~/.config/fnox/config.toml`` as a dict (empty if missing)."""
    if not _FNOX_CONFIG_PATH.exists():
        return {}
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - py<3.11 fallback
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]
    with _FNOX_CONFIG_PATH.open("rb") as fh:
        return tomllib.load(fh)


def _derive_age_recipient(age_key_file: Path) -> str | None:
    """Return the age public recipient for the given private key file."""
    try:
        result = subprocess.run(
            ["age-keygen", "-y", str(age_key_file)],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def bootstrap_config(
    *,
    project: str = _DEFAULT_PROJECT,
    config: str = _DEFAULT_CONFIG,
) -> int:
    """Idempotently write ``~/.config/fnox/config.toml`` with providers + declarations.

    Reads the age public key from ``~/.config/mise/age.txt`` (see H3 amendment)
    and preserves any existing ``DOPPLER_TOKEN`` keychain entry.
    """
    if not _AGE_KEY_PATH.exists():
        logger.bind(path=str(_AGE_KEY_PATH)).error("bootstrap_age_key_missing")
        return 1
    recipient = _derive_age_recipient(_AGE_KEY_PATH)
    if not recipient:
        logger.error("bootstrap_age_recipient_unavailable")
        return 1

    existing = _read_existing_config()
    existing_secrets = existing.get("secrets") if existing else None
    preserved_doppler_token: dict[str, object] | None = None
    if isinstance(existing_secrets, dict):
        dt = existing_secrets.get("DOPPLER_TOKEN")  # type: ignore[call-overload]
        if isinstance(dt, dict):
            preserved_doppler_token = dt

    provider_name = f"doppler_{project}_{config}"
    lines: list[str] = [
        "# Managed by `mde-py secrets bootstrap-config`. Do not edit by hand.",
        "",
        "[providers.keychain]",
        'type = "keychain"',
        'service = "mde-fnox"',
        "",
        "[providers.age]",
        'type = "age"',
        f'recipients = ["{recipient}"]',
        "",
        f"[providers.{provider_name}]",
        'type = "doppler"',
        f'project = "{project}"',
        f'config = "{config}"',
        "",
        "[secrets]",
    ]
    if preserved_doppler_token is not None:
        provider = preserved_doppler_token.get("provider", "keychain")
        lines.append(f'DOPPLER_TOKEN = {{ provider = "{provider}", value = "DOPPLER_TOKEN" }}')
    else:
        lines.append('DOPPLER_TOKEN = { provider = "keychain", value = "DOPPLER_TOKEN" }')

    # Enumerate Doppler secrets and emit declarations for each (excluding
    # DOPPLER_TOKEN itself + AGE_PRIVATE_KEY which is bootstrap-only + Doppler
    # meta keys that are auto-injected).
    # FAIL CLOSED on empty results: doppler_list_secrets returns {} on both
    # "project genuinely empty" and "CLI failure / invalid JSON". A truncated
    # config would wipe our declaration set on the next sync (codex H2).
    remote = doppler_list_secrets(project=project, config=config)
    if not remote:
        logger.error("bootstrap_doppler_list_empty_or_failed")
        return 1
    skip = {
        "DOPPLER_TOKEN",
        "AGE_PRIVATE_KEY",
        "DOPPLER_PROJECT",
        "DOPPLER_CONFIG",
        "DOPPLER_ENVIRONMENT",
    }
    for key in sorted(remote):
        if key in skip:
            continue
        lines.append(f'{key} = {{ provider = "{provider_name}", value = "{key}" }}')
    lines.append("")

    _FNOX_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _FNOX_CONFIG_PATH.write_text("\n".join(lines))
    logger.bind(path=str(_FNOX_CONFIG_PATH)).info("bootstrap_config_written")
    return 0


def _check_age_file() -> list[str]:
    """Return problems with the local age key file."""
    if not _AGE_KEY_PATH.exists():
        return [f"missing age key file: {_AGE_KEY_PATH}"]
    mode = _AGE_KEY_PATH.stat().st_mode & 0o777
    if mode != _AGE_FILE_MODE:
        return [f"age key file mode is {mode:o}, expected 600"]
    return []


def _check_doppler_token() -> list[str]:
    """Return problems retrieving DOPPLER_TOKEN via fnox.

    ``fnox get`` returns exit 0 with an empty stdout when a secret is missing
    (printing "Secret not found" on stderr), so we must also check that the
    value is non-empty.
    """
    try:
        rc = subprocess.run(
            ["fnox", "get", "DOPPLER_TOKEN"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return [f"fnox get DOPPLER_TOKEN error: {exc}"]
    if rc.returncode != 0:
        return ["fnox get DOPPLER_TOKEN failed"]
    if not rc.stdout.strip():
        return [
            "DOPPLER_TOKEN missing from fnox (not in `mde-fnox` keychain). "
            "Bootstrap with: fnox set DOPPLER_TOKEN TOKEN_VALUE "
            "--provider keychain --global"
        ]
    return []


def _check_age_parity() -> list[str]:
    """Return problems comparing local age key to Doppler AGE_PRIVATE_KEY."""
    if not _AGE_KEY_PATH.exists():
        return []
    try:
        rc = subprocess.run(
            [
                "doppler",
                "secrets",
                "get",
                "AGE_PRIVATE_KEY",
                "--plain",
                "--project",
                _DEFAULT_PROJECT,
                "--config",
                _DEFAULT_CONFIG,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return [f"doppler get AGE_PRIVATE_KEY error: {exc}"]
    if rc.returncode != 0:
        return ["doppler get AGE_PRIVATE_KEY failed"]
    if rc.stdout.rstrip("\n") != _AGE_KEY_PATH.read_text().rstrip("\n"):
        return ["AGE_PRIVATE_KEY drift between Doppler and local"]
    return []


def doctor() -> int:
    """Check that the secrets bootstrap chain is healthy.

    Verifies age key file, fnox DOPPLER_TOKEN retrieval, and Doppler/local
    AGE_PRIVATE_KEY parity. Returns 0 if healthy, 1 otherwise.
    """
    problems = _check_age_file() + _check_doppler_token() + _check_age_parity()
    if problems:
        for p in problems:
            logger.bind(problem=p).error("secrets_doctor_problem")
            print(f"doctor: {p}", file=sys.stderr)
        return 1
    logger.info("secrets_doctor_ok")
    return 0
