"""Telemetry configuration verification."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REQUIRED_ENV = {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_EXPORTER_OTLP_ENDPOINT": None,  # any value is OK
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
}

_CONFLICTING_PLUGINS = {"hookify@claude-plugins-official"}


def _load_settings() -> tuple[dict[str, object], dict[str, str]]:
    """Load and merge settings from ~/.claude/settings.json and .claude/settings.json.

    Returns:
        Tuple of (merged settings dict, merged env vars dict).
    """
    merged: dict[str, object] = {}
    merged_env: dict[str, str] = {}

    # Global settings first, project settings override
    paths = [
        Path.home() / ".claude" / "settings.json",
        Path(".claude") / "settings.json",
    ]
    for p in paths:
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            merged.update(data)
            if "env" in data and isinstance(data["env"], dict):
                merged_env.update(data["env"])

    return merged, merged_env


def _check_env_vars(settings_env: dict[str, str]) -> list[tuple[str, str, str]]:
    """Check required telemetry env vars are set.

    Checks both settings.json env block and actual environment variables.

    Returns:
        List of (var_name, status, detail) tuples.
    """
    results: list[tuple[str, str, str]] = []
    for var, expected in _REQUIRED_ENV.items():
        # Check settings env first, then real env
        value = settings_env.get(var, os.environ.get(var))
        if value is None or value == "":
            results.append((var, "MISSING", "not set in settings or environment"))
        elif expected is not None and value != expected:
            results.append((var, "MISMATCH", f"expected {expected!r}, got {value!r}"))
        else:
            results.append((var, "OK", f"set to {value!r}"))
    return results


def _check_plugins(settings: dict[str, object]) -> list[tuple[str, str, str]]:
    """Check enabledPlugins for conflicting plugins.

    Returns:
        List of (plugin_name, status, detail) tuples.
    """
    results: list[tuple[str, str, str]] = []
    raw = settings.get("enabledPlugins", {})
    if not isinstance(raw, dict):
        return [("enabledPlugins", "MISMATCH", "expected dict, got something else")]

    enabled_plugins = dict(raw)

    for plugin in _CONFLICTING_PLUGINS:
        value = enabled_plugins.get(plugin)
        if value is True:
            results.append((plugin, "MISMATCH", "conflicting plugin is enabled"))
        elif value is False:
            results.append((plugin, "OK", "correctly disabled"))
        else:
            results.append((plugin, "OK", "not present in enabledPlugins"))
    return results


def _check_hooks_dispatch() -> list[tuple[str, str, str]]:
    """Check all _HOOKS_DISPATCH entries have matching subparser registrations.

    Uses parse_args to probe whether each hook name is accepted by the hooks
    subparser, avoiding access to argparse private internals.

    Returns:
        List of (hook_name, status, detail) tuples.
    """
    from mde.cli import _HOOKS_DISPATCH, _build_parser

    results: list[tuple[str, str, str]] = []
    parser = _build_parser()

    for hook_name in _HOOKS_DISPATCH:
        try:
            parser.parse_args(["hooks", hook_name])
            results.append((hook_name, "OK", "has matching subparser"))
        except SystemExit:
            results.append((hook_name, "MISSING", "no matching subparser registration"))

    return results


def verify_telemetry() -> int:
    """Run all telemetry checks, print results, return 0/1."""
    settings, settings_env = _load_settings()
    all_passed = True

    sections: list[tuple[str, list[tuple[str, str, str]]]] = [
        ("Environment Variables", _check_env_vars(settings_env)),
        ("Plugin Conflicts", _check_plugins(settings)),
        ("Hooks Dispatch", _check_hooks_dispatch()),
    ]

    for section_name, results in sections:
        print(f"\n=== {section_name} ===", file=sys.stderr)
        for name, status, detail in results:
            marker = "OK" if status == "OK" else "FAIL"
            if status != "OK":
                all_passed = False
            print(f"  [{marker}] {name}: {status} — {detail}", file=sys.stderr)

    print(file=sys.stderr)
    if all_passed:
        print("All telemetry checks passed.", file=sys.stderr)
        return 0
    print("Some telemetry checks failed.", file=sys.stderr)
    return 1
