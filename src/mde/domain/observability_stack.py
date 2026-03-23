"""Observability stack lifecycle management.

Manages the Docker Compose LGTM stack (OTEL Collector + Tempo + Loki + Grafana).
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


def stack_verify() -> int:
    """Check health of all observability stack services.

    Checks collector health via host-side HTTP (port 13133, scratch-based image
    has no wget). Grafana, Loki, and Tempo are checked via ``docker compose exec``.
    Returns 0 only if all services report healthy.
    """
    import subprocess

    failures = 0

    # Collector: scratch-based image has no shell/wget — probe health extension from host
    try:
        urllib.request.urlopen("http://localhost:13133/health", timeout=5)
        print("  HEALTHY: collector", file=sys.stderr)
    except (urllib.error.URLError, OSError) as exc:
        print(f"  UNHEALTHY: collector — {exc}", file=sys.stderr)
        failures += 1

    checks: list[tuple[str, list[str]]] = [
        (
            "grafana",
            [
                "docker",
                "compose",
                "-f",
                str(COMPOSE_FILE),
                "exec",
                "grafana",
                "wget",
                "--spider",
                "-q",
                "http://localhost:3000/api/health",
            ],
        ),
        (
            "loki",
            [
                "docker",
                "compose",
                "-f",
                str(COMPOSE_FILE),
                "exec",
                "loki",
                "wget",
                "--spider",
                "-q",
                "http://localhost:3100/ready",
            ],
        ),
        (
            "tempo",
            [
                "docker",
                "compose",
                "-f",
                str(COMPOSE_FILE),
                "exec",
                "tempo",
                "wget",
                "--spider",
                "-q",
                "http://localhost:3200/ready",
            ],
        ),
    ]

    for name, cmd in checks:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
            )
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT: {name}", file=sys.stderr)
            failures += 1
            continue

        if result.returncode != 0:
            print(f"  UNHEALTHY: {name}", file=sys.stderr)
            if result.stderr:
                print(f"    {result.stderr.strip()}", file=sys.stderr)
            failures += 1
        else:
            print(f"  HEALTHY: {name}", file=sys.stderr)

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
