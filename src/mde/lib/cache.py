"""Cache policy utilities (migrated from lib/mde-cache-policy.sh)."""

from __future__ import annotations

import shutil
from pathlib import Path


def clear_mise_cache() -> None:
    """Clear the mise cache directory."""
    cache_dir = Path.home() / ".local" / "share" / "mise" / "cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print(f"Cleared mise cache: {cache_dir}")


def clear_uv_cache() -> None:
    """Clear the uv cache directory."""
    cache_dir = Path.home() / ".cache" / "uv"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print(f"Cleared uv cache: {cache_dir}")
