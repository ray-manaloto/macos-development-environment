"""Observability stack lifecycle management.

Manages the Docker Compose LGTM stack (OTEL Collector + Tempo + Loki + Grafana).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

COMPOSE_FILE = (
    Path(__file__).resolve().parents[3] / "docker" / "observability" / "docker-compose.yml"
)


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
            subprocess.run(
                ["docker", "stop", parts[0]],
                capture_output=True,
                timeout=30,
            )


def stack_up() -> int:
    """Start the LGTM observability stack.

    Validates GRAFANA_PASSWORD is set, stops orphan collectors, then starts compose.
    """
    import subprocess

    password = os.environ.get("GRAFANA_PASSWORD", "")
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

    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d", "--wait"],
        timeout=120,
    )
    return result.returncode


def stack_down() -> int:
    """Stop the LGTM observability stack."""
    import subprocess

    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "down"],
        timeout=60,
    )
    return result.returncode


def stack_status() -> int:
    """Show LGTM stack container status."""
    import subprocess

    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "ps", "--format", "table"],
        timeout=10,
    )
    return result.returncode


def add_subparsers(sub: argparse._SubParsersAction) -> None:
    """Register the 'observability' subcommand and its children."""
    obs_p = sub.add_parser("observability", help="LGTM observability stack management")
    obs_sub = obs_p.add_subparsers(dest="observability_action")
    obs_sub.add_parser("up", help="Start the observability stack")
    obs_sub.add_parser("down", help="Stop the observability stack")
    obs_sub.add_parser("status", help="Show stack container status")


def dispatch(args: argparse.Namespace) -> int:
    """Route to the correct observability subcommand handler."""
    action = getattr(args, "observability_action", None)
    if action == "up":
        return stack_up()
    if action == "down":
        return stack_down()
    if action == "status":
        return stack_status()
    print("Usage: mde-py observability {up,down,status}", file=sys.stderr)
    return 1
