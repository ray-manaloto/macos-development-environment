"""CLI dispatcher for mde subcommands."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from mde.observability import get_logger, get_tracer, init_observability

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

_logger = get_logger("mde.cli")
_tracer = get_tracer("mde.cli")


_SUBPARSERS: dict[str, argparse.ArgumentParser] = {}


def _build_parser() -> argparse.ArgumentParser:  # noqa: PLR0915
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

    # quality
    quality_p = sub.add_parser("quality", help="Run quality gate (lint + test + validate)")
    quality_p.add_argument("--lint", action="store_true", help="Lint only (ruff + ty + pyright)")
    quality_p.add_argument("--test", action="store_true", help="Test only (pytest)")
    quality_p.add_argument("--validate", action="store_true", help="Validate only")

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

    # telemetry
    telemetry_p = sub.add_parser("telemetry", help="Telemetry management")
    telemetry_p.add_argument("action", choices=["verify"], help="Telemetry action")

    # hooks
    hooks_p = sub.add_parser("hooks", help="Claude Code hook handlers")
    hooks_sub = hooks_p.add_subparsers(dest="hooks_action")
    hooks_sub.add_parser("log-edit-outcome", help="PostToolUse logger")
    hooks_sub.add_parser("log-agent-event", help="SubagentStart/SubagentStop logger")
    hooks_sub.add_parser("guard-install", help="PreToolUse install guard")
    hooks_sub.add_parser("session-start", help="SessionStart context setup")
    hooks_sub.add_parser("post-compact", help="PostCompact research state save")
    hooks_sub.add_parser("team-quality-gate", help="Per-team quality gate validation")
    _SUBPARSERS["hooks"] = hooks_p

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
    init_observability()
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
    with _tracer.start_as_current_span("mde.cli.validate") as span:
        _logger.info("cmd_start", command="validate")
        from mde.validate import validate_all

        result = validate_all(
            fix=args.fix,
            configs_only=args.configs,
            json_output=args.json,
            brew_only=args.brew,
            docker_only=args.docker,
            package_managers_only=getattr(args, "package_managers", False),
            skills_only=args.skills,
        )
        span.set_attribute("validate.passed", result == 0)
        _logger.info("cmd_complete", command="validate", exit_code=result)
        return result


def _cmd_update(_args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.update") as span:
        _logger.info("cmd_start", command="update")
        from mde.maintain.update import run_update

        result = run_update()
        span.set_attribute("update.passed", result == 0)
        _logger.info("cmd_complete", command="update", exit_code=result)
        return result


def _cmd_verify(_args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.verify") as span:
        _logger.info("cmd_start", command="verify")
        from mde.validate import validate_all

        result = validate_all(fix=False, configs_only=False, json_output=False)
        span.set_attribute("verify.passed", result == 0)
        _logger.info("cmd_complete", command="verify", exit_code=result)
        return result


def _cmd_status(_args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.status") as span:
        _logger.info("cmd_start", command="status")
        from mde.status.dashboard import show_dashboard

        result = show_dashboard()
        span.set_attribute("status.passed", result == 0)
        _logger.info("cmd_complete", command="status", exit_code=result)
        return result


def _cmd_doctor(_args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.doctor") as span:
        _logger.info("cmd_start", command="doctor")
        from mde.status.health import run_doctor

        result = run_doctor()
        span.set_attribute("doctor.passed", result == 0)
        _logger.info("cmd_complete", command="doctor", exit_code=result)
        return result


def _cmd_drift(_args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.drift") as span:
        _logger.info("cmd_start", command="drift")
        from mde.maintain.drift import check_drift

        result = check_drift()
        span.set_attribute("drift.passed", result == 0)
        _logger.info("cmd_complete", command="drift", exit_code=result)
        return result


def _cmd_secrets(args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.secrets") as span:
        _logger.info("cmd_start", command="secrets", action=args.action)
        from mde.secrets import dispatch_secrets

        result = dispatch_secrets(args.action)
        span.set_attribute("secrets.action", args.action)
        span.set_attribute("secrets.passed", result == 0)
        _logger.info("cmd_complete", command="secrets", exit_code=result)
        return result


def _cmd_learn(args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.learn") as span:
        _logger.info("cmd_start", command="learn", action=args.action)
        from mde.learn import dispatch_learn

        result = dispatch_learn(args.action, query=args.query)
        span.set_attribute("learn.action", args.action)
        span.set_attribute("learn.passed", result == 0)
        _logger.info("cmd_complete", command="learn", exit_code=result)
        return result


def _cmd_team(args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.team") as span:
        _logger.info("cmd_start", command="team", team_name=args.name)
        from mde.teams.runner import run_team

        result = run_team(args.name, dry_run=args.dry_run)
        span.set_attribute("team.name", args.name)
        span.set_attribute("team.passed", result == 0)
        _logger.info("cmd_complete", command="team", exit_code=result)
        return result


def _cmd_prune(_args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.prune") as span:
        _logger.info("cmd_start", command="prune")
        from mde.maintain.prune import run_prune

        result = run_prune()
        span.set_attribute("prune.passed", result == 0)
        _logger.info("cmd_complete", command="prune", exit_code=result)
        return result


def _cmd_remediate(_args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.remediate") as span:
        _logger.info("cmd_start", command="remediate")
        from mde.maintain.remediate import run_remediate

        result = run_remediate()
        span.set_attribute("remediate.passed", result == 0)
        _logger.info("cmd_complete", command="remediate", exit_code=result)
        return result


def _cmd_refs(args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.refs") as span:
        _logger.info("cmd_start", command="refs", action=args.action)
        from mde.domain.refs import dispatch_refs

        result = dispatch_refs(args.action, dry_run=args.dry_run)
        span.set_attribute("refs.action", args.action)
        span.set_attribute("refs.passed", result == 0)
        _logger.info("cmd_complete", command="refs", exit_code=result)
        return result


def _cmd_install(args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.install") as span:
        target = args.install_target
        _logger.info("cmd_start", command="install", target=target)
        span.set_attribute("install.target", str(target))
        if target == "tmux":
            from mde.install.tmux import install_tmux

            result = install_tmux()
        elif target == "aws-k8s":
            from mde.install.aws_k8s import install_aws_k8s_tools

            result = install_aws_k8s_tools()
        else:
            print(f"Unknown install target: {target}", file=sys.stderr)
            result = 1
        span.set_attribute("install.passed", result == 0)
        _logger.info("cmd_complete", command="install", exit_code=result)
        return result


def _cmd_skill(args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.skill") as span:
        action = args.skill_action
        _logger.info("cmd_start", command="skill", action=action)
        span.set_attribute("skill.action", str(action))
        if action == "sync":
            from pathlib import Path

            from mde.maintain.skill_sync import sync_skills

            actions = sync_skills(Path.cwd(), dry_run=args.dry_run)
            if not actions:
                print("All skills are synced.", file=sys.stderr)
                result = 0
            else:
                prefix = "[dry-run] " if args.dry_run else ""
                for a in actions:
                    print(f"{prefix}{a}", file=sys.stderr)
                result = 0
        else:
            print(f"Unknown skill action: {action}", file=sys.stderr)
            result = 1
        span.set_attribute("skill.passed", result == 0)
        _logger.info("cmd_complete", command="skill", exit_code=result)
        return result


def _cmd_telemetry(args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.telemetry") as span:
        action = args.action
        _logger.info("cmd_start", command="telemetry", action=action)
        span.set_attribute("telemetry.action", action)
        if action == "verify":
            from mde.telemetry_verify import verify_telemetry

            result = verify_telemetry()
        else:
            print(f"Unknown telemetry action: {action}", file=sys.stderr)
            result = 1
        span.set_attribute("telemetry.passed", result == 0)
        _logger.info("cmd_complete", command="telemetry", exit_code=result)
        return result


_HOOKS_DISPATCH: dict[str, tuple[str, str]] = {
    "log-edit-outcome": ("mde.hooks.log_outcome", "log_edit_outcome"),
    "log-agent-event": ("mde.hooks.log_agent_event", "log_agent_event"),
    "guard-install": ("mde.hooks.guard_install", "guard_install"),
    "session-start": ("mde.hooks.session_start", "session_start"),
    "post-compact": ("mde.hooks.post_compact", "post_compact"),
    "team-quality-gate": ("mde.hooks.team_quality_gates", "team_quality_gate_hook"),
}


def _cmd_hooks(args: argparse.Namespace) -> int:
    action = args.hooks_action
    if action is None:
        _SUBPARSERS["hooks"].print_help()
        return 1
    entry = _HOOKS_DISPATCH.get(action)
    if entry is None:
        print(f"Unknown hooks action: {action}", file=sys.stderr)
        return 1
    with _tracer.start_as_current_span("mde.cli.hooks") as span:
        span.set_attribute("hook.action", action)
        import importlib

        module = importlib.import_module(entry[0])
        handler = getattr(module, entry[1])
        result = handler()
        span.set_attribute("hook.passed", result == 0)
        return result


def _cmd_research(args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.research") as span:
        _logger.info("cmd_start", command="research")
        from mde.research.cli import dispatch as research_dispatch

        result = research_dispatch(args)
        span.set_attribute("research.passed", result == 0)
        _logger.info("cmd_complete", command="research", exit_code=result)
        return result


def _cmd_quality(args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.quality") as span:
        _logger.info("cmd_start", command="quality")
        from mde.quality import cli_main

        cli_args: list[str] = []
        if getattr(args, "lint", False):
            cli_args.append("--lint")
        if getattr(args, "test", False):
            cli_args.append("--test")
        if getattr(args, "validate", False):
            cli_args.append("--validate")
        result = cli_main(cli_args)
        span.set_attribute("quality.passed", result == 0)
        _logger.info("cmd_complete", command="quality", exit_code=result)
        return result


def _cmd_statusline(args: argparse.Namespace) -> int:
    with _tracer.start_as_current_span("mde.cli.statusline") as span:
        action = args.statusline_action
        _logger.info("cmd_start", command="statusline", action=action)
        span.set_attribute("statusline.action", str(action))
        handlers: dict[str, tuple[str, str]] = {
            "render": ("mde.statusline.render", "render_statusline"),
            "toggle": ("mde.statusline.toggle", "toggle_mode"),
            "show-mode": ("mde.statusline.toggle", "show_mode"),
            "show-widgets": ("mde.statusline.widget_toggle", "show_widgets"),
            "last-event": ("mde.statusline.render", "show_last_event"),
        }
        if action == "toggle-widget":
            from mde.statusline.widget_toggle import toggle_widget

            result = toggle_widget(args.widget_name)
        elif action in handlers:
            import importlib

            mod_name, fn_name = handlers[action]
            mod = importlib.import_module(mod_name)
            result = getattr(mod, fn_name)()
        else:
            print(f"Unknown statusline action: {action}", file=sys.stderr)
            result = 1
        span.set_attribute("statusline.passed", result == 0)
        _logger.info("cmd_complete", command="statusline", exit_code=result)
        return result


_DISPATCH_TABLE: dict[str, Callable[[argparse.Namespace], int]] = {
    "validate": _cmd_validate,
    "update": _cmd_update,
    "verify": _cmd_verify,
    "quality": _cmd_quality,
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
    "telemetry": _cmd_telemetry,
    "hooks": _cmd_hooks,
    "research": _cmd_research,
    "statusline": _cmd_statusline,
}
