"""Auto-fix: clear corrupted caches."""

from __future__ import annotations

from mde.lib.cache import clear_mise_cache, clear_uv_cache


def fix_corrupted_caches() -> int:
    """Clear caches that may be corrupted.

    Returns:
        Number of caches cleared.
    """
    cleared = 0
    try:
        clear_mise_cache()
        cleared += 1
    except OSError as exc:
        print(f"  WARN: Could not clear mise cache: {exc}")
    try:
        clear_uv_cache()
        cleared += 1
    except OSError as exc:
        print(f"  WARN: Could not clear uv cache: {exc}")
    return cleared
