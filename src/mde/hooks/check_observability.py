"""SessionStart hook: verify the full observability pipeline is healthy.

Checks three layers:
1. Infrastructure: OTEL collector, Grafana, Loki, Tempo health endpoints
2. Source configs: Claude Code, Codex, Gemini OTLP configuration
3. Data arrival: recent telemetry from all expected services in Loki

This is advisory — the session proceeds regardless, but warnings surface
gaps that would otherwise cause silent telemetry loss.
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
# Tuple: (name, url, requires_post). The OTLP endpoint needs POST with empty JSON.
_SERVICES: list[tuple[str, str, bool]] = [
    ("otlp-http", "http://localhost:4318/v1/traces", True),
    ("grafana", "http://localhost:3000/api/health", False),
    ("loki", "http://localhost:3100/ready", False),
    ("tempo", "http://localhost:3200/ready", False),
]

_STARTUP_CMD = (
    "GRAFANA_PASSWORD=$(fnox get GRAFANA_PASSWORD) "
    "docker compose -f docker/observability/compose.yaml up -d"
)


def _check_endpoint(url: str, *, post: bool = False) -> bool:
    """Return True if the health endpoint responds with HTTP 200."""
    try:
        if post:
            data = b"{}"
            req = urllib.request.Request(  # noqa: S310
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        else:
            req = urllib.request.Request(url, method="GET")  # noqa: S310
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:  # noqa: S310
            return resp.status == _HTTP_OK  # type: ignore[no-any-return]
    except Exception:  # noqa: BLE001
        return False


def check_services() -> dict[str, bool]:
    """Check all observability services and return a name→healthy mapping."""
    return {name: _check_endpoint(url, post=post) for name, url, post in _SERVICES}


_EXPECTED_SERVICES = ["claude-code", "codex-app-server", "codex_exec", "gemini-cli", "mde"]

_LOKI_LABELS_URL = "http://localhost:3100/loki/api/v1/label/service_name/values"


def _check_loki_data_arrival() -> list[str]:
    """Query Loki for service_name labels and return missing expected services."""
    try:
        with urllib.request.urlopen(_LOKI_LABELS_URL, timeout=_TIMEOUT_SECONDS) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
        found = set(data.get("data", []) or [])
        return [svc for svc in _EXPECTED_SERVICES if svc not in found]
    except Exception:  # noqa: BLE001
        return []  # Loki unreachable — infrastructure check already covers this


def check_observability() -> int:
    """Entry point: check infrastructure health and telemetry data arrival."""
    warnings: list[str] = []

    # Layer 1: Infrastructure health
    results = check_services()
    down = [name for name, healthy in results.items() if not healthy]
    if down:
        down_list = ", ".join(down)
        warnings.append(
            f"Services DOWN: {down_list}. "
            "Telemetry will be silently lost.\n"
            f"Start the stack: {_STARTUP_CMD}"
        )

    # Layer 2: Data arrival (only if Loki is up)
    if results.get("loki", False):
        missing = _check_loki_data_arrival()
        if missing:
            warnings.append(
                f"No recent Loki data from: {', '.join(missing)}. "
                "These sources may not be sending telemetry. "
                "Run: uv run mde-py telemetry verify"
            )

    if warnings:
        full_warning = "WARNING: " + " | ".join(warnings)
        json.dump({"systemMessage": full_warning}, sys.stdout)

    logger.bind(
        hook="check_observability",
        services={name: str(healthy) for name, healthy in results.items()},
        all_healthy=str(len(down) == 0),
        missing_data_sources=",".join(_check_loki_data_arrival()) if results.get("loki") else "",
    ).info("hook_completed")
    return 0
