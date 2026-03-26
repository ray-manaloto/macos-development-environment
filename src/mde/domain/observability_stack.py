"""Observability stack lifecycle management.

Manages the Docker Compose LGTM stack (OTEL Collector + Tempo + Loki + Grafana).

Architecture Decision: This module uses ``docker compose`` directly, NOT the
devcontainer CLI. The observability stack is **sidecar infrastructure** that
serves host-side AI agents (codex, gemini, claude CLIs send telemetry to
127.0.0.1:4318). It has an independent lifecycle from the dev environment.

The devcontainer spec's ``dockerComposeFile`` + ``runServices`` pattern requires
designating a compose service AS the dev container (via the ``service`` property).
That couples the entire compose stack lifecycle to ``devcontainer up/down``, which
would break host-side telemetry consumers and tie observability to dev env state.

See: docs/research/trail/findings/devcontainer-observability-migration.yaml
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

from mde.domain.docker_stacks import OBSERVABILITY_COMPOSE

if TYPE_CHECKING:
    from collections.abc import Callable

COMPOSE_FILE = OBSERVABILITY_COMPOSE


def stop_orphan_collectors() -> None:
    """Detect and stop legacy codex-otel-collector containers."""
    import subprocess

    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return

    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 1 and "codex-otel-collector" in parts[0]:
            print(f"  Stopping orphan collector: {parts[0]}", file=sys.stderr)
            try:
                subprocess.run(
                    ["docker", "stop", parts[0]],
                    capture_output=True,
                    timeout=30,
                )
            except subprocess.TimeoutExpired:
                print(
                    f"  WARNING: timed out stopping orphan: {parts[0]}",
                    file=sys.stderr,
                )


def stack_up() -> int:
    """Start the LGTM observability stack.

    Validates GRAFANA_PASSWORD is set, stops orphan collectors, then starts compose.
    """
    import subprocess

    password = os.environ.get("GRAFANA_PASSWORD", "").strip()
    if not password:
        print(
            "ERROR: GRAFANA_PASSWORD not set. "
            "Add it to macOS Keychain: "
            "security add-generic-password -s GRAFANA_PASSWORD -a mde -w '<password>'",
            file=sys.stderr,
        )
        return 1

    if not COMPOSE_FILE.is_file():
        print(f"ERROR: Compose file not found: {COMPOSE_FILE}", file=sys.stderr)
        return 1

    stop_orphan_collectors()

    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d", "--wait"],
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        print("TIMEOUT: observability stack_up did not complete in time", file=sys.stderr)
        return 1
    return result.returncode


def stack_down() -> int:
    """Stop the LGTM observability stack."""
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "down"],
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        print("TIMEOUT: observability stack_down did not complete in time", file=sys.stderr)
        return 1
    return result.returncode


def stack_status() -> int:
    """Show LGTM stack container status."""
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "ps", "--format", "table"],
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        print("TIMEOUT: observability stack_status did not complete in time", file=sys.stderr)
        return 1
    return result.returncode


def _probe_http(url: str, timeout: int = 5) -> tuple[bool, str]:
    """Probe a host-side HTTP endpoint. Returns (ok, detail)."""
    try:
        urllib.request.urlopen(url, timeout=timeout)  # noqa: S310
    except (urllib.error.URLError, OSError) as exc:
        return False, str(exc)
    return True, "ok"


# Host-side health check endpoints. All services publish ports to localhost,
# so we probe from the host — no need for docker compose exec.
# This is essential for the scratch-based collector (no shell/wget inside).
_HEALTH_CHECKS: list[tuple[str, str]] = [
    ("collector", "http://localhost:13133/health"),
    ("grafana", "http://localhost:3000/api/health"),
    ("loki", "http://localhost:3100/ready"),
    ("tempo", "http://localhost:3200/ready"),
]


def stack_verify() -> int:
    """Check health of all observability stack services.

    All checks use host-side HTTP probes against published ports.
    This approach works uniformly for all containers, including the
    scratch-based OTEL Collector which has no shell or wget inside.
    Returns 0 only if all services report healthy.
    """
    failures = 0

    for name, url in _HEALTH_CHECKS:
        ok, detail = _probe_http(url)
        if ok:
            print(f"  HEALTHY: {name}", file=sys.stderr)
        else:
            print(f"  UNHEALTHY: {name} — {detail}", file=sys.stderr)
            failures += 1

    return 1 if failures else 0


def add_subparsers(sub: argparse._SubParsersAction) -> None:
    """Register the 'observability' subcommand and its children."""
    obs_p = sub.add_parser("observability", help="LGTM observability stack management")
    obs_sub = obs_p.add_subparsers(dest="observability_action")
    obs_sub.add_parser("up", help="Start the observability stack")
    obs_sub.add_parser("down", help="Stop the observability stack")
    obs_sub.add_parser("status", help="Show stack container status")
    obs_sub.add_parser("verify", help="Check service health")


_ACTION_TABLE: dict[str, Callable[[], int]] = {
    "up": stack_up,
    "down": stack_down,
    "status": stack_status,
    "verify": stack_verify,
}


def dispatch(args: argparse.Namespace) -> int:
    """Route to the correct observability subcommand handler."""
    action = getattr(args, "observability_action", None)
    handler = _ACTION_TABLE.get(action)  # type: ignore[arg-type]  # action is str|None, get() accepts that
    if handler is None:
        print("Usage: mde-py observability {up,down,status,verify}", file=sys.stderr)
        return 1
    try:
        return handler()
    except FileNotFoundError:
        print(
            "ERROR: docker not found on PATH. Install Docker Desktop or add docker to PATH.",
            file=sys.stderr,
        )
        return 1
