"""SessionStart hook: verify the mde-observability Docker stack is running.

Checks Grafana, Loki, and Tempo health endpoints in the grafana/otel-lgtm
all-in-one container. Reports which services are down. This is advisory —
the session proceeds regardless.
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "SessionStart observability check",
    "entry": "check_observability",
}

import json
import sys
import urllib.request

from mde.log import logger

_HTTP_OK = 200
_TIMEOUT_SECONDS = 2

# All services in the mde-observability LGTM stack with their health endpoints.
# Uses grafana/otel-lgtm all-in-one image — all services share one container.
_SERVICES: list[tuple[str, str]] = [
    ("grafana", "http://localhost:3000/api/health"),
    ("loki", "http://localhost:3100/ready"),
    ("tempo", "http://localhost:3200/ready"),
]

_STARTUP_CMD = (
    "GRAFANA_PASSWORD=$(fnox get GRAFANA_PASSWORD) "
    "docker compose -f docker/observability/compose.yaml up -d"
)


def _check_endpoint(url: str) -> bool:
    """Return True if the health endpoint responds with HTTP 200."""
    try:
        req = urllib.request.Request(url, method="GET")  # noqa: S310
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:  # noqa: S310
            return resp.status == _HTTP_OK  # type: ignore[no-any-return]
    except Exception:  # noqa: BLE001
        return False


def check_services() -> dict[str, bool]:
    """Check all observability services and return a name→healthy mapping."""
    return {name: _check_endpoint(url) for name, url in _SERVICES}


def check_observability() -> int:
    """Entry point: check all observability services and warn about any that are down."""
    results = check_services()
    down = [name for name, healthy in results.items() if not healthy]

    if down:
        down_list = ", ".join(down)
        warning = (
            f"WARNING: mde-observability services DOWN: {down_list}. "
            "Telemetry from Claude Code, Codex, and Gemini will be silently lost.\n"
            f"Start the stack with: {_STARTUP_CMD}"
        )
        json.dump({"systemMessage": warning}, sys.stdout)

    logger.bind(
        hook="check_observability",
        services={name: str(healthy) for name, healthy in results.items()},
        all_healthy=str(len(down) == 0),
    ).info("hook_completed")
    return 0
