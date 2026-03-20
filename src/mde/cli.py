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
    validate_p.add_argument("--all", action="store_true", help="Run all validators")
    validate_p.add_argument("--brew", action="store_true", help="Brew validation only")
    validate_p.add_argument("--docker", action="store_true", help="Docker validation only")
    validate_p.add_argument("--package-managers", action="store_true", help="Dedup check only")
    validate_p.add_argument("--skills", action="store_true", help="Skill frontmatter only")

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

    # install
    install_p = sub.add_parser("install", help="Install tool stacks")
    install_sub = install_p.add_subparsers(dest="install_target")
    install_sub.add_parser("tmux", help="Install tmux + TPM + managed config")
    install_sub.add_parser("aws-k8s", help="Install AWS and Kubernetes tools")

    # skill
    skill_p = sub.add_parser("skill", help="Skill management")
    skill_sub = skill_p.add_subparsers(dest="skill_action")
    sync_p = skill_sub.add_parser("sync", help="Sync .agents/skills/ <-> .claude/skills/")
    sync_p.add_argument("--dry-run", action="store_true", help="Show what would be done")

    # hooks
    hooks_p = sub.add_parser("hooks", help="Claude Code hook handlers")
    hooks_sub = hooks_p.add_subparsers(dest="hooks_action")
    hooks_sub.add_parser("verify-task-completion", help="TaskCompleted gate")
    hooks_sub.add_parser("check-teammate-work", help="TeammateIdle gate")
    hooks_sub.add_parser("log-edit-outcome", help="PostToolUse logger")
    hooks_sub.add_parser("log-agent-event", help="SubagentStarted/Completed logger")
    hooks_sub.add_parser("guard-install", help="PreToolUse install guard")

    # research
    from mde.research.cli import add_subparsers as _add_research_subparsers

    _add_research_subparsers(sub)

    # statusline
    _add_statusline_subparsers(sub)

    return parser


def _add_statusline_subparsers(sub: argparse._SubParsersAction) -> None:
    """Register statusline subcommands."""
    sl_p = sub.add_parser("statusline", help="Multi-agent statusline renderer")
    sl_sub = sl_p.add_subparsers(dest="statusline_action")
    sl_sub.add_parser("render", help="Render statusline (reads stdin JSON)")
    sl_sub.add_parser("toggle", help="Cycle display mode A/B/C")
    sl_sub.add_parser("show-mode", help="Print current mode")
    tw_p = sl_sub.add_parser("toggle-widget", help="Toggle a metrics widget on/off")
    tw_p.add_argument("widget_name", help="Widget name to toggle (or 'all')")
    sl_sub.add_parser("show-widgets", help="Show per-widget toggle states")
    sl_sub.add_parser("last-event", help="Show last captured event (MDE_STATUSLINE_CAPTURE=1)")


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

    return validate_all(
        fix=args.fix,
        configs_only=args.configs,
        json_output=args.json,
        brew_only=args.brew,
        docker_only=args.docker,
        package_managers_only=getattr(args, "package_managers", False),
        skills_only=args.skills,
    )


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


def _cmd_install(args: argparse.Namespace) -> int:
    target = args.install_target
    if target == "tmux":
        from mde.install.tmux import install_tmux

        return install_tmux()
    if target == "aws-k8s":
        from mde.install.aws_k8s import install_aws_k8s_tools

        return install_aws_k8s_tools()
    print(f"Unknown install target: {target}", file=sys.stderr)
    return 1


def _cmd_skill(args: argparse.Namespace) -> int:
    action = args.skill_action
    if action == "sync":
        from pathlib import Path

        from mde.maintain.skill_sync import sync_skills

        actions = sync_skills(Path.cwd(), dry_run=args.dry_run)
        if not actions:
            print("All skills are synced.", file=sys.stderr)
            return 0
        prefix = "[dry-run] " if args.dry_run else ""
        for a in actions:
            print(f"{prefix}{a}", file=sys.stderr)
        return 0
    print(f"Unknown skill action: {action}", file=sys.stderr)
    return 1


def _cmd_hooks(args: argparse.Namespace) -> int:
    action = args.hooks_action
    if action == "verify-task-completion":
        from mde.hooks.verify_task import verify_task_completion

        return verify_task_completion()
    if action == "check-teammate-work":
        from mde.hooks.check_teammate import check_teammate_work

        return check_teammate_work()
    if action == "log-edit-outcome":
        from mde.hooks.log_outcome import log_edit_outcome

        return log_edit_outcome()
    if action == "log-agent-event":
        from mde.hooks.log_agent_event import log_agent_event

        return log_agent_event()
    if action == "guard-install":
        from mde.hooks.guard_install import guard_install

        return guard_install()
    print(f"Unknown hooks action: {action}", file=sys.stderr)
    return 1


def _cmd_research(args: argparse.Namespace) -> int:
    from mde.research.cli import dispatch as research_dispatch

    return research_dispatch(args)


def _cmd_statusline(args: argparse.Namespace) -> int:
    action = args.statusline_action
    handlers: dict[str, tuple[str, str]] = {
        "render": ("mde.statusline.render", "render_statusline"),
        "toggle": ("mde.statusline.toggle", "toggle_mode"),
        "show-mode": ("mde.statusline.toggle", "show_mode"),
        "show-widgets": ("mde.statusline.widget_toggle", "show_widgets"),
        "last-event": ("mde.statusline.render", "show_last_event"),
    }
    if action == "toggle-widget":
        from mde.statusline.widget_toggle import toggle_widget

        return toggle_widget(args.widget_name)
    if action in handlers:
        import importlib

        mod_name, fn_name = handlers[action]
        mod = importlib.import_module(mod_name)
        return getattr(mod, fn_name)()
    print(f"Unknown statusline action: {action}", file=sys.stderr)
    return 1


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
    "install": _cmd_install,
    "team": _cmd_team,
    "refs": _cmd_refs,
    "skill": _cmd_skill,
    "hooks": _cmd_hooks,
    "research": _cmd_research,
    "statusline": _cmd_statusline,
}
