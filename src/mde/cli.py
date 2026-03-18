"""CLI dispatcher for mde subcommands."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="mde",
        description="macOS development environment management",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # validate
    validate_p = sub.add_parser("validate", help="Validate all configs")
    validate_p.add_argument("--fix", action="store_true", help="Auto-fix known issues")
    validate_p.add_argument("--configs", action="store_true", help="Validate config files only")
    validate_p.add_argument("--json", action="store_true", help="Output JSON")

    # update
    sub.add_parser("update", help="Run maintenance cycle")

    # verify
    sub.add_parser("verify", help="Run verification checks")

    # status
    sub.add_parser("status", help="Show dashboard")

    # doctor
    sub.add_parser("doctor", help="System health check")

    # drift
    drift_p = sub.add_parser("drift", help="Drift detection")
    drift_p.add_argument("action", choices=["check"], help="Drift action")

    # secrets
    secrets_p = sub.add_parser("secrets", help="Secrets management")
    secrets_p.add_argument("action", choices=["refresh", "smoke"], help="Secrets action")

    # learn
    learn_p = sub.add_parser("learn", help="Learning system")
    learn_p.add_argument("action", choices=["status", "search", "verify"], help="Learn action")
    learn_p.add_argument("query", nargs="?", default="", help="Search query")

    # team
    team_p = sub.add_parser("team", help="Team management")
    team_p.add_argument("action", choices=["run"], help="Team action")
    team_p.add_argument("name", help="Team name")
    team_p.add_argument("--dry-run", action="store_true", help="Dry run mode")

    # prune
    sub.add_parser("prune", help="Prune stale globals and orphan mise versions")

    # remediate
    sub.add_parser("remediate", help="Run deterministic host remediation")

    # refs
    refs_p = sub.add_parser("refs", help="Reference management")
    refs_p.add_argument(
        "action",
        choices=["clone-frameworks", "refresh", "verify"],
        help="Refs action",
    )
    refs_p.add_argument("--dry-run", action="store_true", help="Dry run mode")

    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and dispatch to the appropriate subcommand."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    return _dispatch(args)


def _dispatch(args: argparse.Namespace) -> int:
    """Dispatch to the appropriate module based on the command."""
    command: str = args.command
    handler = _DISPATCH_TABLE.get(command)
    if handler is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 1
    return handler(args)


def _cmd_validate(args: argparse.Namespace) -> int:
    from mde.validate import validate_all

    return validate_all(fix=args.fix, configs_only=args.configs, json_output=args.json)


def _cmd_update(_args: argparse.Namespace) -> int:
    from mde.maintain.update import run_update

    return run_update()


def _cmd_verify(_args: argparse.Namespace) -> int:
    from mde.validate import validate_all

    return validate_all(fix=False, configs_only=False, json_output=False)


def _cmd_status(_args: argparse.Namespace) -> int:
    from mde.status.dashboard import show_dashboard

    return show_dashboard()


def _cmd_doctor(_args: argparse.Namespace) -> int:
    from mde.status.health import run_doctor

    return run_doctor()


def _cmd_drift(_args: argparse.Namespace) -> int:
    from mde.maintain.drift import check_drift

    return check_drift()


def _cmd_secrets(args: argparse.Namespace) -> int:
    from mde.secrets import dispatch_secrets

    return dispatch_secrets(args.action)


def _cmd_learn(args: argparse.Namespace) -> int:
    from mde.learn import dispatch_learn

    return dispatch_learn(args.action, query=args.query)


def _cmd_team(args: argparse.Namespace) -> int:
    from mde.teams.runner import run_team

    return run_team(args.name, dry_run=args.dry_run)


def _cmd_prune(_args: argparse.Namespace) -> int:
    from mde.maintain.prune import run_prune

    return run_prune()


def _cmd_remediate(_args: argparse.Namespace) -> int:
    from mde.maintain.remediate import run_remediate

    return run_remediate()


def _cmd_refs(args: argparse.Namespace) -> int:
    from mde.domain.refs import dispatch_refs

    return dispatch_refs(args.action, dry_run=args.dry_run)


_DISPATCH_TABLE: dict[str, Callable[[argparse.Namespace], int]] = {
    "validate": _cmd_validate,
    "update": _cmd_update,
    "verify": _cmd_verify,
    "status": _cmd_status,
    "doctor": _cmd_doctor,
    "drift": _cmd_drift,
    "secrets": _cmd_secrets,
    "learn": _cmd_learn,
    "prune": _cmd_prune,
    "remediate": _cmd_remediate,
    "team": _cmd_team,
    "refs": _cmd_refs,
}
