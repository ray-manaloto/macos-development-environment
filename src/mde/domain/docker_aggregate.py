"""Aggregate Docker stack lifecycle management.

Manages ALL Docker sub-stacks by delegating to each stack module.
Each sub-stack (observability, memory) has its own Compose project
name and runs independently.  This module orchestrates them together.

Ordering rationale:
  - up/status/verify: observability first, then memory
    (telemetry infrastructure is available to capture memory stack startup)
  - down: memory first, then observability
    (final telemetry flushes complete before the observability stack goes down)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def stack_up() -> int:
    """Start all Docker stacks (observability -> memory)."""
    from mde.domain.memory_stack import stack_up as memory_up
    from mde.domain.observability_stack import stack_up as obs_up

    print("=== Observability Stack ===", file=sys.stderr)
    try:
        obs_rc = obs_up()
    except subprocess.TimeoutExpired:
        print("  TIMEOUT: observability stack_up", file=sys.stderr)
        obs_rc = 1

    print("\n=== Memory Stack ===", file=sys.stderr)
    try:
        mem_rc = memory_up()
    except subprocess.TimeoutExpired:
        print("  TIMEOUT: memory stack_up", file=sys.stderr)
        mem_rc = 1

    if obs_rc or mem_rc:
        failed = []
        if obs_rc:
            failed.append("observability")
        if mem_rc:
            failed.append("memory")
        print(f"\nFailed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def stack_down() -> int:
    """Stop all Docker stacks (memory -> observability)."""
    from mde.domain.memory_stack import stack_down as memory_down
    from mde.domain.observability_stack import stack_down as obs_down

    print("=== Memory Stack ===", file=sys.stderr)
    try:
        mem_rc = memory_down()
    except subprocess.TimeoutExpired:
        print("  TIMEOUT: memory stack_down", file=sys.stderr)
        mem_rc = 1

    print("\n=== Observability Stack ===", file=sys.stderr)
    try:
        obs_rc = obs_down()
    except subprocess.TimeoutExpired:
        print("  TIMEOUT: observability stack_down", file=sys.stderr)
        obs_rc = 1

    if obs_rc or mem_rc:
        failed = []
        if mem_rc:
            failed.append("memory")
        if obs_rc:
            failed.append("observability")
        print(f"\nFailed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def stack_status() -> int:
    """Show status of all Docker containers (observability -> memory)."""
    from mde.domain.memory_stack import stack_status as memory_status
    from mde.domain.observability_stack import stack_status as obs_status

    print("=== Observability Stack ===", file=sys.stderr)
    try:
        obs_rc = obs_status()
    except subprocess.TimeoutExpired:
        print("  TIMEOUT: observability stack_status", file=sys.stderr)
        obs_rc = 1

    print("\n=== Memory Stack ===", file=sys.stderr)
    try:
        mem_rc = memory_status()
    except subprocess.TimeoutExpired:
        print("  TIMEOUT: memory stack_status", file=sys.stderr)
        mem_rc = 1

    return 1 if (obs_rc or mem_rc) else 0


def stack_verify() -> int:
    """Verify health of all services (observability -> memory)."""
    from mde.domain.memory_stack import stack_verify as memory_verify
    from mde.domain.observability_stack import stack_verify as obs_verify

    print("=== Observability Stack ===", file=sys.stderr)
    try:
        obs_rc = obs_verify()
    except subprocess.TimeoutExpired:
        print("  TIMEOUT: observability stack_verify", file=sys.stderr)
        obs_rc = 1

    print("\n=== Memory Stack ===", file=sys.stderr)
    try:
        mem_rc = memory_verify()
    except subprocess.TimeoutExpired:
        print("  TIMEOUT: memory stack_verify", file=sys.stderr)
        mem_rc = 1

    return 1 if (mem_rc or obs_rc) else 0


def add_subparsers(sub: argparse._SubParsersAction) -> None:
    """Register the 'docker' subcommand and its children."""
    docker_p = sub.add_parser("docker", help="All Docker stacks (aggregate)")
    docker_sub = docker_p.add_subparsers(dest="docker_action")
    docker_sub.add_parser("up", help="Start all stacks")
    docker_sub.add_parser("down", help="Stop all stacks")
    docker_sub.add_parser("status", help="Show all container status")
    docker_sub.add_parser("verify", help="Verify all service health")


_ACTION_TABLE: dict[str, Callable[[], int]] = {
    "up": stack_up,
    "down": stack_down,
    "status": stack_status,
    "verify": stack_verify,
}


def dispatch(args: argparse.Namespace) -> int:
    """Route to the correct docker subcommand handler."""
    action = getattr(args, "docker_action", None)
    handler = _ACTION_TABLE.get(action)  # type: ignore[arg-type]  # action is str|None, get() accepts that
    if handler is None:
        print("Usage: mde-py docker {up,down,status,verify}", file=sys.stderr)
        return 1
    try:
        return handler()
    except FileNotFoundError:
        print(
            "ERROR: docker not found on PATH. Install Docker Desktop or add docker to PATH.",
            file=sys.stderr,
        )
        return 1
