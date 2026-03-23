"""Shared test fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def lgtm_stack_running() -> None:
    """Skip if full LGTM stack is not running.

    Probes Collector (13133), Tempo (3200), and Loki (3100).
    All three must be reachable for integration tests.
    """
    from urllib.request import urlopen

    endpoints = {
        "collector": "http://127.0.0.1:13133/health",
        "tempo": "http://127.0.0.1:3200/ready",
        "loki": "http://127.0.0.1:3100/ready",
    }
    for name, url in endpoints.items():
        try:
            resp = urlopen(url, timeout=2)  # noqa: S310
            if resp.status >= 500:
                pytest.skip(f"LGTM stack: {name} unhealthy")
        except Exception:  # noqa: BLE001
            pytest.skip(f"LGTM stack: {name} not reachable")
