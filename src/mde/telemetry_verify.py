"""Telemetry configuration verification."""

from __future__ import annotations

import json
import os
import sys
import tomllib
from collections.abc import Mapping
from pathlib import Path
from urllib.request import urlopen

_REQUIRED_ENV = {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_EXPORTER_OTLP_ENDPOINT": None,  # any value is OK
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
}

_CONFLICTING_PLUGINS = {"hookify@claude-plugins-official"}

# All env vars documented in official Claude Code monitoring docs
# https://code.claude.com/docs/en/monitoring-usage
_OFFICIAL_VARS: set[str] = {
    "CLAUDE_CODE_ENABLE_TELEMETRY",
    "OTEL_METRICS_EXPORTER",
    "OTEL_LOGS_EXPORTER",
    "OTEL_EXPORTER_OTLP_PROTOCOL",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_EXPORTER_OTLP_HEADERS",
    "OTEL_EXPORTER_OTLP_METRICS_PROTOCOL",
    "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
    "OTEL_EXPORTER_OTLP_LOGS_PROTOCOL",
    "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
    "OTEL_EXPORTER_OTLP_METRICS_CLIENT_KEY",
    "OTEL_EXPORTER_OTLP_METRICS_CLIENT_CERTIFICATE",
    "OTEL_METRIC_EXPORT_INTERVAL",
    "OTEL_LOGS_EXPORT_INTERVAL",
    "OTEL_LOG_USER_PROMPTS",
    "OTEL_LOG_TOOL_DETAILS",
    "OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE",
    "CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS",
    "OTEL_METRICS_INCLUDE_SESSION_ID",
    "OTEL_METRICS_INCLUDE_VERSION",
    "OTEL_METRICS_INCLUDE_ACCOUNT_UUID",
    "OTEL_RESOURCE_ATTRIBUTES",
}

# Non-telemetry Claude Code env vars set in settings.json.
# MUST NOT overlap with _OFFICIAL_VARS. Add new Claude Code feature flags here,
# never to _OFFICIAL_VARS (which tracks only official monitoring docs).
_NON_TELEMETRY_VARS: set[str] = {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS",
    "CLAUDE_PLUGIN_DATA",
    "ENABLE_CLAUDEAI_MCP_SERVERS",
    "ENABLE_LSP_TOOL",
    "ENABLE_TOOL_SEARCH",
}


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
            except json.JSONDecodeError as exc:
                print(f"  [WARN] Skipping {p}: malformed JSON: {exc}", file=sys.stderr)
                continue
            except OSError as exc:
                print(f"  [WARN] Skipping {p}: {exc}", file=sys.stderr)
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
    _sensitive_patterns = ("KEY", "TOKEN", "SECRET", "PASSWORD")
    results: list[tuple[str, str, str]] = []
    for var, expected in _REQUIRED_ENV.items():
        # Check settings env first, then real env
        value = settings_env.get(var, os.environ.get(var))
        # Redact sensitive values in output
        is_sensitive = any(p in var.upper() for p in _sensitive_patterns)
        display = "[REDACTED]" if is_sensitive else repr(value)
        if value is None or value == "":
            results.append((var, "MISSING", "not set in settings or environment"))
        elif expected is not None and value != expected:
            results.append((var, "MISMATCH", f"expected {expected!r}, got {display}"))
        else:
            results.append((var, "OK", f"set to {display}"))

    # Warn if OTEL endpoint is non-localhost (PII/telemetry leak risk)
    endpoint = settings_env.get(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
    )
    if endpoint:
        host = endpoint.replace("http://", "").replace("https://", "").split(":")[0]
        _loopback = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}  # noqa: S104
        if host and host not in _loopback:
            results.append(
                (
                    "OTEL_EXPORTER_OTLP_ENDPOINT",
                    "WARNING",
                    f"non-localhost endpoint {host!r} — telemetry may leave this machine",
                )
            )

    return results


def _check_settings_against_docs(
    settings_env: dict[str, str],
) -> list[tuple[str, str, str]]:
    """Validate settings.json env vars against official Claude Code monitoring docs.

    Checks that every telemetry-related env var we configure is documented in the
    official monitoring docs, and that protocol/endpoint port combinations are consistent.

    Args:
        settings_env: The env block from settings.json.

    Returns:
        List of (var_name, status, detail) tuples.
    """
    results: list[tuple[str, str, str]] = []

    for var in sorted(settings_env):
        if var in _NON_TELEMETRY_VARS:
            continue
        if var in _OFFICIAL_VARS:
            results.append((var, "OK", "documented in official monitoring docs"))
        else:
            results.append((var, "WARNING", "not in official Claude Code monitoring docs"))

    # Check protocol/endpoint port consistency (parse port as integer to avoid
    # substring false positives like ":4317" matching in ":43170")
    protocol = settings_env.get("OTEL_EXPORTER_OTLP_PROTOCOL", "")
    endpoint = settings_env.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if protocol and endpoint:
        import re

        port_match = re.search(r":(\d+)(?:/|$)", endpoint.split("//", 1)[-1])
        port = int(port_match.group(1)) if port_match else None
        if protocol == "grpc" and port is not None and port != 4317:  # noqa: PLR2004
            results.append(
                (
                    "protocol-endpoint",
                    "WARNING",
                    f"protocol mismatch: {protocol!r} typically uses port 4317, "
                    f"but endpoint is {endpoint!r}",
                )
            )
        elif (
            protocol in ("http/json", "http/protobuf") and port is not None and port != 4318  # noqa: PLR2004
        ):
            results.append(
                (
                    "protocol-endpoint",
                    "WARNING",
                    f"protocol mismatch: {protocol!r} typically uses port 4318, "
                    f"but endpoint is {endpoint!r}",
                )
            )

    return results


def _check_plugins(settings: Mapping[str, object]) -> list[tuple[str, str, str]]:
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
    from mde.cli import _build_parser, _discover_hooks

    results: list[tuple[str, str, str]] = []
    parser = _build_parser()

    for hook_name in _discover_hooks():
        try:
            parser.parse_args(["hooks", hook_name])
            results.append((hook_name, "OK", "has matching subparser"))
        except SystemExit:
            results.append((hook_name, "MISSING", "no matching subparser registration"))

    return results


def _check_collector_infrastructure() -> list[tuple[str, str, str]]:
    """Check that OTEL Collector Docker container is running and healthy.

    Returns:
        List of (check_name, status, detail) tuples.
    """
    import subprocess

    results: list[tuple[str, str, str]] = []

    # Check if Docker is available
    try:
        docker_check = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if docker_check.returncode != 0:
            results.append(("docker", "MISSING", "Docker is not running"))
            return results
    except (FileNotFoundError, subprocess.TimeoutExpired):
        results.append(("docker", "MISSING", "Docker CLI not found"))
        return results

    results.append(("docker", "OK", "Docker is running"))

    # Check for OTEL Collector container
    try:
        ps_result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        otel_containers = []
        for line in ps_result.stdout.strip().splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and "otel" in parts[1].lower():  # noqa: PLR2004
                status = parts[2] if len(parts) > 2 else "unknown"  # noqa: PLR2004
                otel_containers.append({"name": parts[0], "image": parts[1], "status": status})

        if otel_containers:
            results.extend(
                (f"container:{c['name']}", "OK", f"{c['image']} ({c['status']})")
                for c in otel_containers
            )
        else:
            results.append(
                (
                    "otel-collector",
                    "MISSING",
                    "no OTEL Collector container running (image containing 'otel')",
                )
            )
    except (subprocess.TimeoutExpired, OSError) as exc:
        results.append(("docker-ps", "FAIL", f"docker ps failed: {exc}"))

    # Check OTEL Collector health endpoint
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    health_host = "localhost"
    health_port = "13133"
    if endpoint:
        health_host = endpoint.replace("http://", "").replace("https://", "").split(":")[0]

    try:
        from urllib.request import urlopen

        health_url = f"http://{health_host}:{health_port}/health"
        resp = urlopen(health_url, timeout=2)  # noqa: S310
        health_data = json.loads(resp.read().decode())
        status_msg = health_data.get("status", "unknown")
        uptime = health_data.get("uptime", "unknown")
        results.append(("collector-health", "OK", f"{status_msg}, uptime: {uptime}"))
    except Exception as exc:  # noqa: BLE001
        results.append(("collector-health", "MISSING", f"health endpoint not responding: {exc}"))

    return results


def _check_collector_pipelines(config_path: Path) -> list[tuple[str, str, str]]:
    """Check OTEL Collector pipelines have non-debug exporters.

    Args:
        config_path: Path to the collector-config.yaml file.

    Returns:
        List of (pipeline_name, status, detail) tuples.
    """
    import yaml

    results: list[tuple[str, str, str]] = []

    if not config_path.is_file():
        results.append(("collector-config", "MISSING", f"file not found: {config_path}"))
        return results

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        results.append(("collector-config", "FAIL", f"YAML parse error: {exc}"))
        return results

    pipelines = (data or {}).get("service", {}).get("pipelines", {})
    for name, pipeline in pipelines.items():
        exporters = pipeline.get("exporters", [])
        non_debug = [e for e in exporters if e != "debug"]
        if non_debug:
            results.append((f"pipeline:{name}", "OK", f"exporters: {exporters}"))
        else:
            results.append((f"pipeline:{name}", "WARNING", f"only debug exporter(s): {exporters}"))

    return results


_EXPECTED_SERVICES = [
    "claude-code",
    "codex-app-server",
    "codex_exec",
    "gemini-cli",
    "mde",
]

_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}  # noqa: S104


def _check_claude_code_config(home: Path) -> tuple[str, str, str]:
    """Check Claude Code telemetry configuration.

    Checks both global (~/.claude/settings.json) and project-level (.claude/settings.json)
    since OTEL env vars may be in either location. Project settings override global.
    """
    paths = [
        home / ".claude" / "settings.json",
        Path(".claude") / "settings.json",
    ]
    merged_env: dict[str, str] = {}
    found_any = False
    for p in paths:
        if p.is_file():
            found_any = True
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                env = data.get("env", {})
                if isinstance(env, dict):
                    merged_env.update(env)
            except (json.JSONDecodeError, OSError):
                pass  # skip unreadable files, check remaining
    if not found_any:
        return ("claude-code", "WARNING", "no settings.json found (global or project)")
    has_telemetry = merged_env.get("CLAUDE_CODE_ENABLE_TELEMETRY") == "1"
    has_endpoint = bool(merged_env.get("OTEL_EXPORTER_OTLP_ENDPOINT"))
    if has_telemetry and has_endpoint:
        return ("claude-code", "OK", "telemetry enabled with OTLP endpoint")
    missing = []
    if not has_telemetry:
        missing.append("CLAUDE_CODE_ENABLE_TELEMETRY")
    if not has_endpoint:
        missing.append("OTEL_EXPORTER_OTLP_ENDPOINT")
    return ("claude-code", "WARNING", f"missing env vars: {', '.join(missing)}")


def _check_codex_config(home: Path) -> tuple[str, str, str]:
    """Check Codex OTLP configuration in ~/.codex/config.toml.

    The Codex config uses nested TOML tables:
        [otel]
        exporter = { otlp-http = { endpoint = "http://127.0.0.1:4318/v1/logs" } }
        trace_exporter = { otlp-http = { endpoint = "http://127.0.0.1:4318/v1/traces" } }
    """
    codex_config_path = home / ".codex" / "config.toml"
    if not codex_config_path.is_file():
        return ("codex", "WARNING", "~/.codex/config.toml not found")
    try:
        codex_data = tomllib.loads(codex_config_path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return ("codex", "WARNING", f"cannot parse config.toml: {exc}")
    otel_section = codex_data.get("otel")
    if not otel_section or not isinstance(otel_section, dict):
        return ("codex", "WARNING", "[otel] section missing from config.toml")

    endpoint = _extract_codex_endpoint(otel_section)
    if not endpoint:
        return ("codex", "WARNING", "[otel] section exists but no endpoint found in exporters")
    host = endpoint.replace("http://", "").replace("https://", "").split(":")[0].split("/")[0]
    if host in _LOOPBACK_HOSTS:
        return ("codex", "OK", f"[otel] configured, endpoint={endpoint}")
    return ("codex", "WARNING", f"[otel] endpoint points to non-localhost: {endpoint}")


def _extract_codex_endpoint(otel_section: dict[str, object]) -> str:
    """Extract the first OTLP endpoint from a Codex [otel] section."""
    for key in ("exporter", "trace_exporter"):
        exp = otel_section.get(key, {})
        if isinstance(exp, dict):
            for backend in exp.values():
                if isinstance(backend, dict) and "endpoint" in backend:
                    return str(backend["endpoint"])
    return ""


def _check_gemini_config(home: Path) -> tuple[str, str, str]:
    """Check Gemini CLI OTLP configuration in ~/.gemini/settings.json.

    Gemini CLI supports OTLP via settings.json telemetry block or env vars:
    - telemetry.enabled (GEMINI_TELEMETRY_ENABLED) — default false
    - telemetry.otlpEndpoint (GEMINI_TELEMETRY_OTLP_ENDPOINT) — default localhost:4317
    - telemetry.otlpProtocol (GEMINI_TELEMETRY_OTLP_PROTOCOL) — default grpc

    See: https://geminicli.com/docs/cli/telemetry/
    """
    gemini_settings_path = home / ".gemini" / "settings.json"
    if not gemini_settings_path.is_file():
        return ("gemini", "WARNING", "~/.gemini/settings.json not found")
    try:
        data = json.loads(gemini_settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return ("gemini", "WARNING", f"cannot read settings: {exc}")

    telemetry = data.get("telemetry", {})
    if not isinstance(telemetry, dict):
        telemetry = {}

    # Check enabled — can also be set via GEMINI_TELEMETRY_ENABLED env var
    enabled = telemetry.get("enabled", False)
    env_enabled = os.environ.get("GEMINI_TELEMETRY_ENABLED", "").lower()
    is_enabled = enabled is True or env_enabled == "true"

    endpoint = telemetry.get(
        "otlpEndpoint",
        os.environ.get("GEMINI_TELEMETRY_OTLP_ENDPOINT", ""),
    )

    if is_enabled and endpoint:
        host = endpoint.replace("http://", "").replace("https://", "").split(":")[0].split("/")[0]
        if host in _LOOPBACK_HOSTS:
            return ("gemini", "OK", f"telemetry enabled, endpoint={endpoint}")
        return ("gemini", "WARNING", f"endpoint points to non-localhost: {endpoint}")
    if is_enabled:
        return ("gemini", "OK", "telemetry enabled (default endpoint localhost:4317)")
    return (
        "gemini",
        "WARNING",
        "telemetry not enabled — set telemetry.enabled=true in "
        "~/.gemini/settings.json or GEMINI_TELEMETRY_ENABLED=true",
    )


def _check_source_configs() -> list[tuple[str, str, str]]:
    """Verify each telemetry source has OTLP endpoints configured.

    Checks Claude Code, Codex, Gemini, and mde library configurations.

    Returns:
        List of (source_name, status, detail) tuples.
    """
    home = Path.home()
    results: list[tuple[str, str, str]] = [
        _check_claude_code_config(home),
        _check_codex_config(home),
        _check_gemini_config(home),
    ]

    # mde library: check observability.py exists
    mde_obs_path = Path(__file__).resolve().parent / "observability.py"
    if mde_obs_path.is_file():
        results.append(("mde", "OK", "observability.py found — handles OTEL setup internally"))
    else:
        results.append(("mde", "WARNING", "observability.py not found in src/mde/"))

    return results


def _check_data_arrival_loki() -> list[tuple[str, str, str]]:
    """Query Loki for service_name labels to verify data arrival.

    Returns:
        List of (check_name, status, detail) tuples.
    """
    results: list[tuple[str, str, str]] = []
    loki_url = "http://localhost:3100/loki/api/v1/label/service_name/values"

    try:
        resp = urlopen(loki_url, timeout=3)  # noqa: S310
        data = json.loads(resp.read().decode())
        service_names = set(data.get("data", []) or [])

        for svc in _EXPECTED_SERVICES:
            if svc in service_names:
                results.append((f"loki:{svc}", "OK", "sending logs to Loki"))
            else:
                results.append((f"loki:{svc}", "WARNING", "no logs found in Loki"))
    except Exception as exc:  # noqa: BLE001
        # Stack may be down — WARNING, not FAIL
        results.append(("loki", "WARNING", f"Loki unreachable: {exc}"))

    return results


def _check_data_arrival_tempo() -> list[tuple[str, str, str]]:
    """Query Tempo for recent traces to verify data arrival.

    Returns:
        List of (check_name, status, detail) tuples.
    """
    results: list[tuple[str, str, str]] = []
    tempo_url = "http://localhost:3200/api/search?limit=10"

    try:
        resp = urlopen(tempo_url, timeout=3)  # noqa: S310
        data = json.loads(resp.read().decode())
        traces = data.get("traces") or []

        if traces:
            results.append(
                (
                    "tempo:traces",
                    "OK",
                    f"{len(traces)} traces found in Tempo",
                )
            )
            # List unique service names from traces
            svc_names = sorted(
                {t.get("rootServiceName", "unknown") for t in traces if t.get("rootServiceName")}
            )
            if svc_names:
                results.append(
                    (
                        "tempo:services",
                        "OK",
                        f"services: {', '.join(svc_names)}",
                    )
                )
        else:
            results.append(("tempo:traces", "WARNING", "no recent traces found in Tempo"))
    except Exception as exc:  # noqa: BLE001
        # Stack may be down — WARNING, not FAIL
        results.append(("tempo", "WARNING", f"Tempo unreachable: {exc}"))

    return results


def verify_telemetry() -> int:
    """Run all telemetry checks, print results, return 0/1."""
    settings, settings_env = _load_settings()
    all_passed = True

    sections: list[tuple[str, list[tuple[str, str, str]]]] = [
        ("Environment Variables", _check_env_vars(settings_env)),
        ("Official Docs Compliance", _check_settings_against_docs(settings_env)),
        ("Plugin Conflicts", _check_plugins(settings)),
        ("Hooks Dispatch", _check_hooks_dispatch()),
        ("Collector Infrastructure", _check_collector_infrastructure()),
        (
            "Collector Pipelines",
            _check_collector_pipelines(
                Path(__file__).resolve().parents[2]
                / "docker"
                / "observability"
                / "collector-config.yaml"
            ),
        ),
        ("Source Configurations", _check_source_configs()),
        ("Data Arrival (Loki)", _check_data_arrival_loki()),
        ("Data Arrival (Tempo)", _check_data_arrival_tempo()),
    ]

    for section_name, results in sections:
        print(f"\n=== {section_name} ===", file=sys.stderr)
        for name, status, detail in results:
            if status == "OK":
                marker = "OK"
            elif status == "WARNING":
                marker = "WARN"
            else:
                marker = "FAIL"
                all_passed = False
            print(f"  [{marker}] {name}: {status} — {detail}", file=sys.stderr)

    print(file=sys.stderr)
    if all_passed:
        print("All telemetry checks passed.", file=sys.stderr)
        return 0
    print("Some telemetry checks failed.", file=sys.stderr)
    return 1
