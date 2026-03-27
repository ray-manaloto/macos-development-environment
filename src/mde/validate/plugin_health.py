"""Validate Claude Code plugin installation health.

Checks for broken install paths, stale temp_git_* cache directories,
MCP server dedup conflicts, and missing LSP binary commands across installed plugins.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from mde.models.result import ValidationResult

_PLUGINS_DIR = Path.home() / ".claude" / "plugins"


def validate_plugin_health(
    *,
    plugins_dir: Path | None = None,
    mcp_json_path: Path | None = None,
    settings_path: Path | None = None,
) -> ValidationResult:
    """Run all plugin health checks.

    Args:
        plugins_dir: Override ~/.claude/plugins/ for testing.
        mcp_json_path: Override .mcp.json path for testing.
        settings_path: Override .claude/settings.json for testing enabled plugins.

    Returns:
        ValidationResult with findings.
    """
    result = ValidationResult()
    pd = plugins_dir or _PLUGINS_DIR
    enabled = _load_enabled_plugins(settings_path)

    _check_broken_install_paths(result, pd)
    _check_stale_temp_dirs(result, pd)
    _check_mcp_dedup(result, pd, mcp_json_path)
    _check_lsp_binaries(result, pd, enabled)

    return result


def _load_enabled_plugins(settings_path: Path | None) -> set[str] | None:
    """Load enabled plugin names from settings.json.

    Returns a set of 'name@marketplace' strings that are explicitly enabled,
    or None if no settings file could be read (fall back to checking all plugins).
    """
    paths_to_try = (
        [settings_path]
        if settings_path
        else [
            Path.cwd() / ".claude" / "settings.json",
            Path.home() / ".claude" / "settings.json",
        ]
    )

    for sp in paths_to_try:
        if sp and sp.exists():
            try:
                data = json.loads(sp.read_text(encoding="utf-8"))
                enabled_plugins = data.get("enabledPlugins", {})
                if isinstance(enabled_plugins, dict):
                    return {k for k, v in enabled_plugins.items() if v is True}
            except (json.JSONDecodeError, OSError):
                continue

    return None


def _check_broken_install_paths(result: ValidationResult, plugins_dir: Path) -> None:
    """Find plugins whose installPath no longer exists on disk."""
    installed_json = plugins_dir / "installed_plugins.json"
    if not installed_json.exists():
        result.add_info(
            str(installed_json),
            "installed_plugins.json not found, skipping broken path check",
            rule="plugin-health.no-installed-json",
        )
        return

    result.files_checked += 1
    try:
        data = json.loads(installed_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        result.add_error(
            str(installed_json),
            f"Cannot parse installed_plugins.json: {exc}",
            rule="plugin-health.parse-error",
        )
        return

    plugins = data.get("plugins", {})
    if not isinstance(plugins, dict):
        result.add_error(
            str(installed_json),
            f"Expected 'plugins' to be a dict, got {type(plugins).__name__}",
            rule="plugin-health.unexpected-format",
        )
        return

    broken_count = 0
    for name, entries in plugins.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            install_path = entry.get("installPath", "")
            if install_path and not Path(install_path).is_dir():
                broken_count += 1
                result.add_error(
                    str(installed_json),
                    f"Broken install path for '{name}': {install_path}",
                    rule="plugin-health.broken-path",
                )

    if broken_count == 0:
        result.add_info(
            str(installed_json),
            "All plugin install paths valid",
            rule="plugin-health.paths-ok",
        )


def _check_stale_temp_dirs(result: ValidationResult, plugins_dir: Path) -> None:
    """Find leftover temp_git_* directories in the plugin cache."""
    cache_dir = plugins_dir / "cache"
    if not cache_dir.exists():
        return

    result.files_checked += 1
    stale: list[Path] = [
        child
        for marketplace_dir in cache_dir.iterdir()
        if marketplace_dir.is_dir()
        for child in marketplace_dir.iterdir()
        if child.is_dir() and child.name.startswith("temp_git_")
    ]

    if stale:
        for d in stale:
            result.add_warning(
                str(d),
                f"Stale temp directory: {d.name} (leftover from interrupted clone)",
                rule="plugin-health.stale-temp-dir",
                fixable=True,
            )
    else:
        result.add_info(
            str(cache_dir),
            "No stale temp_git_* directories found",
            rule="plugin-health.temp-dirs-ok",
        )


def _check_mcp_dedup(
    result: ValidationResult,
    plugins_dir: Path,
    mcp_json_path: Path | None,
) -> None:
    """Detect MCP server name collisions across plugins and project .mcp.json."""
    # Collect MCP server names from plugin hooks.json files
    cache_dir = plugins_dir / "cache"
    plugin_mcp_servers: dict[str, list[str]] = {}  # server_name -> [source, ...]

    if cache_dir.exists():
        for hooks_json in cache_dir.rglob("hooks/hooks.json"):
            _collect_mcp_from_hooks(plugin_mcp_servers, hooks_json)

    # Collect from project .mcp.json
    mcp_path = mcp_json_path or Path.cwd() / ".mcp.json"
    if mcp_path.exists():
        result.files_checked += 1
        try:
            mcp_data = json.loads(mcp_path.read_text(encoding="utf-8"))
            for server_name in mcp_data.get("mcpServers", {}):
                plugin_mcp_servers.setdefault(server_name, []).append(str(mcp_path))
        except (json.JSONDecodeError, OSError):
            pass  # .mcp.json parse errors are handled by other validators

    # Report collisions
    collisions = {k: v for k, v in plugin_mcp_servers.items() if len(v) > 1}
    if collisions:
        for server_name, sources in collisions.items():
            result.add_warning(
                str(mcp_path or ".mcp.json"),
                f"MCP server '{server_name}' registered by {len(sources)} sources: "
                + ", ".join(sources[:4]),
                rule="plugin-health.mcp-dedup",
            )
    else:
        result.add_info(
            str(plugins_dir),
            "No MCP server name collisions detected",
            rule="plugin-health.mcp-ok",
        )


def _collect_mcp_from_hooks(servers: dict[str, list[str]], hooks_json: Path) -> None:
    """Extract MCP server names from a plugin's hooks.json."""
    try:
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    # hooks.json can have mcpServers at top level or nested in hooks
    if isinstance(data, dict):
        for server_name in data.get("mcpServers", {}):
            source = str(hooks_json.parent.parent)  # plugin dir
            servers.setdefault(server_name, []).append(source)


def _check_lsp_binaries(
    result: ValidationResult, plugins_dir: Path, enabled: set[str] | None
) -> None:
    """Find enabled LSP plugins whose command binary is not on PATH."""
    cache_dir = plugins_dir / "cache"
    if not cache_dir.exists():
        return

    lsp_files = list(cache_dir.rglob(".lsp.json"))
    if not lsp_files:
        return

    result.files_checked += 1
    missing_count = 0
    checked_count = 0

    for lsp_json in lsp_files:
        # Derive plugin identity: cache/<marketplace>/<name>/<version>/.lsp.json
        plugin_dir = lsp_json.parent
        plugin_name = plugin_dir.parent.name
        marketplace = plugin_dir.parent.parent.name
        plugin_key = f"{plugin_name}@{marketplace}"

        # Skip disabled plugins when settings are available
        if enabled is not None and plugin_key not in enabled:
            continue

        checked_count += 1
        missing_count += _check_single_lsp(result, lsp_json, cache_dir)

    if missing_count == 0 and checked_count > 0:
        result.add_info(
            str(cache_dir),
            f"All {checked_count} enabled LSP plugin binaries found on PATH",
            rule="plugin-health.lsp-ok",
        )


def _check_single_lsp(result: ValidationResult, lsp_json: Path, cache_dir: Path) -> int:
    """Check a single .lsp.json file. Return count of missing binaries."""
    try:
        data = json.loads(lsp_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0

    if not isinstance(data, dict):
        return 0

    plugin_dir = lsp_json.parent
    plugin_name = plugin_dir.parent.name if plugin_dir.parent != cache_dir else plugin_dir.name
    missing = 0

    for lang, config in data.items():
        if not isinstance(config, dict):
            continue
        command = config.get("command", "")
        if command and shutil.which(command) is None:
            missing += 1
            result.add_error(
                str(lsp_json),
                f"LSP plugin '{plugin_name}' command '{command}' not found on PATH "
                f"(language: {lang})",
                rule="plugin-health.lsp-binary-missing",
            )

    return missing
