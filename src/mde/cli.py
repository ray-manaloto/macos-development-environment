"""CLI dispatcher for mde subcommands."""

from __future__ import annotations

import argparse
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING

from mde.log import get_tracer, logger
from mde.observability import init_observability

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Sequence
    from typing import Any

_tracer = get_tracer("mde.cli")


@contextmanager
def _traced_command(command: str, **extra: object) -> Generator[dict[str, Any]]:
    """Wrap a CLI command with tracing and structured logging."""
    with _tracer.start_as_current_span(f"mde.cli.{command}") as span:
        logger.bind(command=command, **extra).info("cmd_start")
        ctx: dict[str, Any] = {"span": span, "result": 0}
        yield ctx
        result = ctx.get("result", 0)
        span.set_attribute(f"{command}.passed", result == 0)
        logger.bind(command=command, exit_code=result, **extra).info("cmd_complete")


_SUBPARSERS: dict[str, argparse.ArgumentParser] = {}


def _discover_hooks() -> dict[str, tuple[str, str, str]]:
    """Scan src/mde/hooks/ for modules with __hook_meta__ and return dispatch info.

    Returns a dict mapping command-name -> (module_path, function_name, help_text).
    Modules without __hook_meta__ are silently skipped.
    Uses AST parsing to avoid importing hook modules at startup.
    """
    import ast
    from pathlib import Path

    hooks_dir = Path(__file__).parent / "hooks"
    result: dict[str, tuple[str, str, str]] = {}

    for py_file in sorted(hooks_dir.glob("*.py")):
        if py_file.name.startswith("_") or py_file.name == "__init__.py":
            continue

        try:
            tree = ast.parse(py_file.read_text())
        except SyntaxError:
            continue

        meta = _extract_hook_meta(tree)
        if meta is None:
            continue

        module_stem = py_file.stem
        cmd_name = meta.get("name", module_stem.replace("_", "-"))
        module_path = f"mde.hooks.{module_stem}"
        entry_fn = meta["entry"]
        help_text = meta["help"]

        if cmd_name in result:
            existing_mod = result[cmd_name][0]
            msg = (
                f"Hook command collision: '{cmd_name}' defined by both "
                f"{existing_mod} and {module_path}"
            )
            raise ValueError(msg)

        result[cmd_name] = (module_path, entry_fn, help_text)

    return result


def _extract_hook_meta(tree: object) -> dict[str, str] | None:
    """Extract __hook_meta__ dict from an AST tree, or return None.

    Supports both plain assignment (ast.Assign) and annotated assignment
    (ast.AnnAssign), e.g. ``__hook_meta__: dict[str, str] = {...}``.
    """
    import ast

    for node in ast.iter_child_nodes(tree):  # type: ignore[arg-type]
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__hook_meta__"
            and isinstance(node.value, ast.Dict)
        ):
            return _parse_dict_literal(node.value)
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "__hook_meta__"
            and node.value is not None
            and isinstance(node.value, ast.Dict)
        ):
            return _parse_dict_literal(node.value)
    return None


def _parse_dict_literal(node: object) -> dict[str, str] | None:
    """Parse an ast.Dict of string constants into a plain dict."""
    import ast

    if not isinstance(node, ast.Dict):
        return None
    meta: dict[str, str] = {}
    for key, value in zip(node.keys, node.values, strict=False):
        if isinstance(key, ast.Constant) and isinstance(value, ast.Constant):
            meta[str(key.value)] = str(value.value)
    if "help" in meta and "entry" in meta:
        return meta
    return None


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
    validate_p.add_argument(
        "--plugins",
        action="store_true",
        help="Plugin validation only",
    )
    validate_p.add_argument(
        "--evaluations",
        action="store_true",
        help="Research evaluation completeness only",
    )
    validate_p.add_argument(
        "--eval-file",
        default="docs/research/trail/findings/community-plugin-evaluations.yaml",
        help="Path to evaluation YAML file",
    )
    validate_p.add_argument(
        "--eval-candidates",
        nargs="+",
        default=None,
        help="Required candidate names to check",
    )

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
    secrets_p.add_argument(
        "action", choices=["refresh", "smoke", "export", "sync"], help="Secrets action"
    )

    # learn
    learn_p = sub.add_parser("learn", help="Learning system")
    learn_p.add_argument("action", choices=["status", "search", "verify"], help="Learn action")
    learn_p.add_argument("query", nargs="?", default="", help="Search query")

    # team
    team_p = sub.add_parser("team", help="Team management")
    team_p.add_argument("action", choices=["run"], help="Team action")
    team_p.add_argument("name", help="Team name")
    team_p.add_argument("--dry-run", action="store_true", help="Dry run mode")

    # review
    review_p = sub.add_parser("review", help="Run autonomous multi-model code review")
    review_p.add_argument("finding", help="Finding file (YAML) or description string")
    review_p.add_argument(
        "--autonomy",
        choices=["supervised", "semi-autonomous", "autonomous"],
        default="semi-autonomous",
        help="Autonomy mode (default: semi-autonomous)",
    )
    review_p.add_argument("--skip-quality", action="store_true", help="Skip quality gate")

    # debate
    debate_p = sub.add_parser("debate", help="Multi-model debate via CLI backends")
    debate_p.add_argument("prompt", help="Debate prompt or question")
    debate_p.add_argument(
        "--model",
        choices=["codex", "gemini", "all"],
        default="all",
        help="Model to invoke (default: all)",
    )
    debate_p.add_argument("--output-dir", help="Save results as JSON to this directory")
    debate_p.add_argument("--timeout", type=int, default=300, help="Timeout per model (seconds)")
    debate_p.add_argument("--json", action="store_true", help="JSON output for agent consumption")

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
    # HOOKS AUTO-DISCOVERY: Scans src/mde/hooks/ for modules with __hook_meta__.
    # Adding a new hook requires ONLY creating a new module — cli.py is NOT modified.
    # See .claude/rules/hooks-auto-discovery.md for the full convention.
    hooks_p = sub.add_parser("hooks", help="Claude Code hook handlers")
    hooks_sub = hooks_p.add_subparsers(dest="hooks_action")
    for cmd_name, entry in _discover_hooks().items():
        hooks_sub.add_parser(cmd_name, help=entry[2])
    _SUBPARSERS["hooks"] = hooks_p

    # research
    from mde.research.cli import add_subparsers as _add_research_subparsers

    _add_research_subparsers(sub)

    # statusline
    _add_statusline_subparsers(sub)

    # observability
    from mde.domain.observability_stack import add_subparsers as _add_obs_subparsers

    _add_obs_subparsers(sub)

    # memory
    from mde.domain.memory_stack import add_subparsers as _add_memory_subparsers

    _add_memory_subparsers(sub)

    # docker (aggregate: all stacks)
    from mde.domain.docker_aggregate import add_subparsers as _add_docker_subparsers

    _add_docker_subparsers(sub)

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
    try:
        init_observability()
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: Observability init failed: {exc}", file=sys.stderr)
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    result = _dispatch(args)
    # Drain loguru's async file sink before exit
    logger.complete()
    return result


def _dispatch(args: argparse.Namespace) -> int:
    """Dispatch to the appropriate module based on the command."""
    command: str = args.command
    handler = _DISPATCH_TABLE.get(command)
    if handler is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 1
    return handler(args)


def _cmd_validate(args: argparse.Namespace) -> int:
    with _traced_command("validate") as ctx:
        if getattr(args, "evaluations", False):
            from pathlib import Path

            from mde.validate.evaluations import validate_evaluations

            candidates = args.eval_candidates or []
            result_obj = validate_evaluations(
                evaluation_path=Path(args.eval_file),
                required_candidates=candidates,
            )
            from mde.validate import _print_findings

            _print_findings(result_obj)
            result = 0 if result_obj.passed else 1
        else:
            from mde.validate import validate_all

            result = validate_all(
                fix=args.fix,
                configs_only=args.configs,
                json_output=args.json,
                brew_only=args.brew,
                docker_only=args.docker,
                package_managers_only=getattr(args, "package_managers", False),
                skills_only=args.skills,
                plugins_only=args.plugins,
            )
        ctx["result"] = result
        return result


def _cmd_update(_: argparse.Namespace) -> int:
    with _traced_command("update") as ctx:
        from mde.maintain.update import run_update

        result = run_update()
        ctx["result"] = result
        return result


def _cmd_verify(_: argparse.Namespace) -> int:
    with _traced_command("verify") as ctx:
        from mde.validate import validate_all

        result = validate_all(fix=False, configs_only=False, json_output=False)
        ctx["result"] = result
        return result


def _cmd_status(_: argparse.Namespace) -> int:
    with _traced_command("status") as ctx:
        from mde.status.dashboard import show_dashboard

        result = show_dashboard()
        ctx["result"] = result
        return result


def _cmd_doctor(_: argparse.Namespace) -> int:
    with _traced_command("doctor") as ctx:
        from mde.status.health import run_doctor

        result = run_doctor()
        ctx["result"] = result
        return result


def _cmd_drift(_: argparse.Namespace) -> int:
    with _traced_command("drift") as ctx:
        from mde.maintain.drift import check_drift

        result = check_drift()
        ctx["result"] = result
        return result


def _cmd_secrets(args: argparse.Namespace) -> int:
    with _traced_command("secrets", action=args.action) as ctx:
        from mde.secrets import dispatch_secrets

        result = dispatch_secrets(args.action)
        ctx["span"].set_attribute("secrets.action", args.action)
        ctx["result"] = result
        return result


def _cmd_learn(args: argparse.Namespace) -> int:
    with _traced_command("learn", action=args.action) as ctx:
        from mde.learn import dispatch_learn

        result = dispatch_learn(args.action, query=args.query)
        ctx["span"].set_attribute("learn.action", args.action)
        ctx["result"] = result
        return result


def _cmd_team(args: argparse.Namespace) -> int:
    with _traced_command("team", team_name=args.name) as ctx:
        from mde.teams.runner import run_team

        result = run_team(args.name, dry_run=args.dry_run)
        ctx["span"].set_attribute("team.name", args.name)
        ctx["result"] = result
        return result


def _cmd_review(args: argparse.Namespace) -> int:
    with _traced_command("review") as ctx:
        from mde.autonomous_review import cli_review

        result = cli_review(args)
        ctx["result"] = result
        return result


def _cmd_debate(args: argparse.Namespace) -> int:
    with _traced_command("debate") as ctx:
        from pathlib import Path

        from mde.debate.invoke import invoke_all

        model_arg: str = args.model
        models = ["codex", "gemini"] if model_arg == "all" else [model_arg]
        output_dir = Path(args.output_dir) if args.output_dir else None

        results = invoke_all(
            prompt=args.prompt,
            models=models,
            timeout=args.timeout,
            output_dir=output_dir,
        )

        import json
        import sys

        json_mode = getattr(args, "json", False)

        if json_mode:
            # Machine-readable JSON output for agent consumption
            sys.stdout.write(json.dumps([r.model_dump() for r in results], indent=2))
            sys.stdout.write("\n")
        else:
            # Human-readable output
            for r in results:
                status = "OK" if r.success else "FAIL"
                sys.stderr.write(f"[{r.model}] {status} ({r.duration_seconds}s)\n")
                if r.response:
                    sys.stderr.write(f"{r.response[:500]}\n\n")
                if r.error:
                    sys.stderr.write(f"  Error: {r.error}\n")

        ctx["result"] = 0 if all(r.success for r in results) else 1
        return ctx["result"]


def _cmd_prune(_: argparse.Namespace) -> int:
    with _traced_command("prune") as ctx:
        from mde.maintain.prune import run_prune

        result = run_prune()
        ctx["result"] = result
        return result


def _cmd_remediate(_: argparse.Namespace) -> int:
    with _traced_command("remediate") as ctx:
        from mde.maintain.remediate import run_remediate

        result = run_remediate()
        ctx["result"] = result
        return result


def _cmd_refs(args: argparse.Namespace) -> int:
    with _traced_command("refs", action=args.action) as ctx:
        from mde.domain.refs import dispatch_refs

        result = dispatch_refs(args.action, dry_run=args.dry_run)
        ctx["span"].set_attribute("refs.action", args.action)
        ctx["result"] = result
        return result


def _cmd_install(args: argparse.Namespace) -> int:
    target = args.install_target
    with _traced_command("install", target=target) as ctx:
        ctx["span"].set_attribute("install.target", str(target))
        if target == "tmux":
            from mde.install.tmux import install_tmux

            result = install_tmux()
        elif target == "aws-k8s":
            from mde.install.aws_k8s import install_aws_k8s_tools

            result = install_aws_k8s_tools()
        else:
            print(f"Unknown install target: {target}", file=sys.stderr)
            result = 1
        ctx["result"] = result
        return result


def _cmd_skill(args: argparse.Namespace) -> int:
    action = args.skill_action
    with _traced_command("skill", action=action) as ctx:
        ctx["span"].set_attribute("skill.action", str(action))
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
        ctx["result"] = result
        return result


def _cmd_telemetry(args: argparse.Namespace) -> int:
    action = args.action
    with _traced_command("telemetry", action=action) as ctx:
        ctx["span"].set_attribute("telemetry.action", action)
        if action == "verify":
            from mde.telemetry_verify import verify_telemetry

            result = verify_telemetry()
        else:
            print(f"Unknown telemetry action: {action}", file=sys.stderr)
            result = 1
        ctx["result"] = result
        return result


def _cmd_hooks(args: argparse.Namespace) -> int:
    action = args.hooks_action
    if action is None:
        _SUBPARSERS["hooks"].print_help()
        return 1
    hooks = _discover_hooks()
    entry = hooks.get(action)
    if entry is None:
        print(f"Unknown hooks action: {action}", file=sys.stderr)
        return 1
    with _traced_command("hooks", action=action) as ctx:
        ctx["span"].set_attribute("hook.action", action)
        import importlib

        module = importlib.import_module(entry[0])
        handler = getattr(module, entry[1])
        result = handler()
        ctx["result"] = result
        return result


def _cmd_research(args: argparse.Namespace) -> int:
    with _traced_command("research") as ctx:
        from mde.research.cli import dispatch as research_dispatch

        result = research_dispatch(args)
        ctx["result"] = result
        return result


def _cmd_quality(args: argparse.Namespace) -> int:
    with _traced_command("quality") as ctx:
        from mde.quality import cli_main

        cli_args: list[str] = []
        if getattr(args, "lint", False):
            cli_args.append("--lint")
        if getattr(args, "test", False):
            cli_args.append("--test")
        if getattr(args, "validate", False):
            cli_args.append("--validate")
        result = cli_main(cli_args)
        ctx["result"] = result
        return result


def _cmd_statusline(args: argparse.Namespace) -> int:
    action = args.statusline_action
    with _traced_command("statusline", action=action) as ctx:
        ctx["span"].set_attribute("statusline.action", str(action))
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
        ctx["result"] = result
        return result


def _cmd_observability(args: argparse.Namespace) -> int:
    action = getattr(args, "observability_action", None)
    with _traced_command("observability", action=action) as ctx:
        ctx["span"].set_attribute("observability.action", str(action))
        from mde.domain.observability_stack import dispatch as obs_dispatch

        result = obs_dispatch(args)
        ctx["result"] = result
        return result


def _cmd_memory(args: argparse.Namespace) -> int:
    action = getattr(args, "memory_action", None)
    with _traced_command("memory", action=action) as ctx:
        ctx["span"].set_attribute("memory.action", str(action))
        from mde.domain.memory_stack import dispatch as mem_dispatch

        result = mem_dispatch(args)
        ctx["result"] = result
        return result


def _cmd_docker(args: argparse.Namespace) -> int:
    action = getattr(args, "docker_action", None)
    with _traced_command("docker", action=action) as ctx:
        ctx["span"].set_attribute("docker.action", str(action))
        from mde.domain.docker_aggregate import dispatch as docker_dispatch

        result = docker_dispatch(args)
        ctx["result"] = result
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
    "review": _cmd_review,
    "debate": _cmd_debate,
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
    "observability": _cmd_observability,
    "memory": _cmd_memory,
    "docker": _cmd_docker,
}
