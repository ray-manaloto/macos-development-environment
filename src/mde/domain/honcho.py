"""Honcho SDK client factory.

Provides a pre-configured Honcho client reading connection
parameters from environment variables with schema-validated defaults.

Note: The Honcho server runs in API-only mode (EMBED_MESSAGES=false,
deriver disabled). Methods requiring LLM processing (chat, search,
representation) will return errors. CRUD operations work normally.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from honcho import Honcho

from mde.domain.honcho_models import HonchoClientConfig


def get_config() -> HonchoClientConfig:
    """Build config from env vars with schema defaults."""
    raw_timeout = os.environ.get("HONCHO_TIMEOUT", "10")
    raw_retries = os.environ.get("HONCHO_MAX_RETRIES", "0")
    try:
        timeout = float(raw_timeout)
    except ValueError:
        msg = f"HONCHO_TIMEOUT must be a number, got: {raw_timeout!r}"
        raise ValueError(msg) from None
    try:
        max_retries = int(raw_retries)
    except ValueError:
        msg = f"HONCHO_MAX_RETRIES must be an integer, got: {raw_retries!r}"
        raise ValueError(msg) from None
    return HonchoClientConfig(
        base_url=os.environ.get("HONCHO_BASE_URL", "http://localhost:8000"),
        workspace_id=os.environ.get("HONCHO_WORKSPACE_ID", "mde"),
        api_key=os.environ.get("HONCHO_API_KEY"),
        timeout=timeout,
        max_retries=max_retries,
    )


def get_client(config: HonchoClientConfig | None = None) -> Honcho:
    """Return a configured Honcho SDK client."""
    from honcho import Honcho as _Honcho

    if config is None:
        config = get_config()
    return _Honcho(
        api_key=config.api_key,
        base_url=config.base_url,
        workspace_id=config.workspace_id,
        timeout=config.timeout,
        max_retries=config.max_retries,
    )


def test_connection(config: HonchoClientConfig | None = None) -> tuple[bool, str]:  # noqa: PLR0911, PT028
    """Test connectivity to the Honcho API.

    Returns (success, message) tuple. Uses the SDK's workspaces() list
    endpoint as a health probe (public API, no private method access).
    """
    try:
        from honcho import (
            AuthenticationError,
            NotFoundError,
            RateLimitError,
            ServerError,
        )
        from honcho import (
            ConnectionError as HonchoConnectionError,
        )
        from honcho import (
            TimeoutError as HonchoTimeoutError,
        )
    except ImportError:
        return False, "honcho-ai SDK not installed"

    try:
        client = get_client(config)
        # Use public SDK method as health probe — list workspaces is a
        # lightweight read that validates connectivity, auth, and API version.
        client.workspaces()
    except HonchoConnectionError as e:
        return False, f"Connection failed: {e}"
    except HonchoTimeoutError:
        return False, f"Timeout after {(config or get_config()).timeout}s"
    except AuthenticationError:
        return False, "Auth required but no API key configured"
    except NotFoundError:
        return False, "Server does not support API v3"
    except RateLimitError:
        return False, "Rate limited — server is reachable but rejecting requests"
    except ServerError as e:
        return False, f"Server error: {e}"
    except Exception as e:  # noqa: BLE001
        return False, f"Unexpected error: {e}"
    else:
        return True, "Connected"
