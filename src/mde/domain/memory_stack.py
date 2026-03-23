"""Memory stack lifecycle management.

Manages the Docker Compose Honcho stack (API + Deriver + PostgreSQL/pgvector + Redis).
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import TYPE_CHECKING

from mde.domain.docker_stacks import MEMORY_COMPOSE

if TYPE_CHECKING:
    from collections.abc import Callable

COMPOSE_FILE = MEMORY_COMPOSE


def stack_up() -> int:
    """Start the Honcho memory stack.

    Validates HONCHO_DB_PASSWORD is set, then starts compose.
    """
    import subprocess

    password = os.environ.get("HONCHO_DB_PASSWORD", "").strip()
    if not password:
        print(
            "ERROR: HONCHO_DB_PASSWORD not set. "
            "Add it to macOS Keychain: "
            "security add-generic-password -s HONCHO_DB_PASSWORD -a mde -w '<password>'",
            file=sys.stderr,
        )
        return 1

    if not COMPOSE_FILE.is_file():
        print(f"ERROR: Compose file not found: {COMPOSE_FILE}", file=sys.stderr)
        return 1

    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d", "--wait"],
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        print("TIMEOUT: memory stack_up did not complete in time", file=sys.stderr)
        return 1
    return result.returncode


def stack_down() -> int:
    """Stop the Honcho memory stack."""
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "down"],
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        print("TIMEOUT: memory stack_down did not complete in time", file=sys.stderr)
        return 1
    return result.returncode


def stack_status() -> int:
    """Show Honcho memory stack container status."""
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "ps", "--format", "table"],
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        print("TIMEOUT: memory stack_status did not complete in time", file=sys.stderr)
        return 1
    return result.returncode


def stack_verify() -> int:
    """Check health of all Honcho memory stack services.

    Runs health checks for the API (urllib), PostgreSQL (pg_isready),
    and Redis (redis-cli ping) via ``docker compose exec``.
    Returns 0 only if all services report healthy.
    """
    import subprocess

    checks: list[tuple[str, list[str]]] = [
        (
            "honcho-api",
            [
                "docker",
                "compose",
                "-f",
                str(COMPOSE_FILE),
                "exec",
                "honcho-api",
                "python",
                "-c",
                "import urllib.request; urllib.request.urlopen('http://localhost:8000/openapi.json')",
            ],
        ),
        (
            "honcho-db",
            [
                "docker",
                "compose",
                "-f",
                str(COMPOSE_FILE),
                "exec",
                "honcho-db",
                "pg_isready",
                "-U",
                "honcho",
                "-d",
                "honcho",
            ],
        ),
        (
            "honcho-redis",
            [
                "docker",
                "compose",
                "-f",
                str(COMPOSE_FILE),
                "exec",
                "honcho-redis",
                "redis-cli",
                "ping",
            ],
        ),
    ]

    failures = 0
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
    """Register the 'memory' subcommand and its children."""
    mem_p = sub.add_parser("memory", help="Honcho memory stack management")
    mem_sub = mem_p.add_subparsers(dest="memory_action")
    mem_sub.add_parser("up", help="Start the memory stack")
    mem_sub.add_parser("down", help="Stop the memory stack")
    mem_sub.add_parser("status", help="Show stack container status")
    mem_sub.add_parser("verify", help="Check service health")


_ACTION_TABLE: dict[str, Callable[[], int]] = {
    "up": stack_up,
    "down": stack_down,
    "status": stack_status,
    "verify": stack_verify,
}


def dispatch(args: argparse.Namespace) -> int:
    """Route to the correct memory subcommand handler."""
    action = getattr(args, "memory_action", None)
    handler = _ACTION_TABLE.get(action)  # type: ignore[arg-type]  # action is str|None, get() accepts that
    if handler is None:
        print("Usage: mde-py memory {up,down,status,verify}", file=sys.stderr)
        return 1
    try:
        return handler()
    except FileNotFoundError:
        print(
            "ERROR: docker not found on PATH. Install Docker Desktop or add docker to PATH.",
            file=sys.stderr,
        )
        return 1
