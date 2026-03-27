"""Tests for plugin installation health validation."""

from __future__ import annotations

import json
from pathlib import Path

from mde.validate.plugin_health import validate_plugin_health


def _make_installed_json(plugins_dir: Path, plugins: dict) -> None:
    """Write a minimal installed_plugins.json."""
    plugins_dir.mkdir(parents=True, exist_ok=True)
    data = {"version": 2, "plugins": plugins}
    (plugins_dir / "installed_plugins.json").write_text(json.dumps(data))


def _make_cache(plugins_dir: Path, marketplace: str, plugin: str) -> Path:
    """Create a cache directory for a plugin and return its path."""
    cache = plugins_dir / "cache" / marketplace / plugin / "1.0.0"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def test_broken_install_path(tmp_path: Path) -> None:
    """Plugins with non-existent installPath are flagged as errors."""
    pd = tmp_path / "plugins"
    _make_installed_json(
        pd,
        {
            "good-plugin@mkt": [
                {"installPath": str(_make_cache(pd, "mkt", "good-plugin")), "scope": "project"}
            ],
            "bad-plugin@mkt": [
                {
                    "installPath": str(pd / "cache" / "mkt" / "bad-plugin" / "1.0.0"),
                    "scope": "project",
                }
            ],
        },
    )

    result = validate_plugin_health(plugins_dir=pd, mcp_json_path=tmp_path / "no-mcp.json")

    errors = [f for f in result.findings if f.rule == "plugin-health.broken-path"]
    assert len(errors) == 1
    assert "bad-plugin" in errors[0].message
    assert not result.passed


def test_all_paths_valid(tmp_path: Path) -> None:
    """No errors when all install paths exist."""
    pd = tmp_path / "plugins"
    cache_path = _make_cache(pd, "mkt", "ok-plugin")
    _make_installed_json(
        pd,
        {"ok-plugin@mkt": [{"installPath": str(cache_path), "scope": "project"}]},
    )

    result = validate_plugin_health(plugins_dir=pd, mcp_json_path=tmp_path / "no-mcp.json")

    errors = [f for f in result.findings if f.severity.value == "error"]
    assert len(errors) == 0


def test_stale_temp_dirs(tmp_path: Path) -> None:
    """Stale temp_git_* directories are flagged as warnings."""
    pd = tmp_path / "plugins"
    _make_installed_json(pd, {})

    # Create a stale temp dir
    stale = pd / "cache" / "mkt" / "temp_git_abc123"
    stale.mkdir(parents=True)

    result = validate_plugin_health(plugins_dir=pd, mcp_json_path=tmp_path / "no-mcp.json")

    warnings = [f for f in result.findings if f.rule == "plugin-health.stale-temp-dir"]
    assert len(warnings) == 1
    assert "temp_git_abc123" in warnings[0].message


def test_no_stale_temp_dirs(tmp_path: Path) -> None:
    """Clean cache produces no temp dir warnings."""
    pd = tmp_path / "plugins"
    _make_installed_json(pd, {})
    _make_cache(pd, "mkt", "clean-plugin")

    result = validate_plugin_health(plugins_dir=pd, mcp_json_path=tmp_path / "no-mcp.json")

    warnings = [f for f in result.findings if f.rule == "plugin-health.stale-temp-dir"]
    assert len(warnings) == 0


def test_mcp_dedup_collision(tmp_path: Path) -> None:
    """MCP server name collision between plugin and .mcp.json is flagged."""
    pd = tmp_path / "plugins"
    _make_installed_json(pd, {})

    # Plugin hooks.json with MCP server
    hooks_dir = pd / "cache" / "mkt" / "my-plugin" / "1.0.0" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "hooks.json").write_text(
        json.dumps({"mcpServers": {"shared-server": {"command": "node", "args": ["server.js"]}}})
    )

    # Project .mcp.json with same server name
    mcp_path = tmp_path / ".mcp.json"
    mcp_path.write_text(
        json.dumps({"mcpServers": {"shared-server": {"command": "python", "args": ["server.py"]}}})
    )

    result = validate_plugin_health(plugins_dir=pd, mcp_json_path=mcp_path)

    dedup = [f for f in result.findings if f.rule == "plugin-health.mcp-dedup"]
    assert len(dedup) == 1
    assert "shared-server" in dedup[0].message


def test_no_mcp_collision(tmp_path: Path) -> None:
    """No collision when MCP servers have unique names."""
    pd = tmp_path / "plugins"
    _make_installed_json(pd, {})

    hooks_dir = pd / "cache" / "mkt" / "my-plugin" / "1.0.0" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "hooks.json").write_text(
        json.dumps({"mcpServers": {"plugin-server": {"command": "node"}}})
    )

    mcp_path = tmp_path / ".mcp.json"
    mcp_path.write_text(json.dumps({"mcpServers": {"project-server": {"command": "python"}}}))

    result = validate_plugin_health(plugins_dir=pd, mcp_json_path=mcp_path)

    dedup = [f for f in result.findings if f.rule == "plugin-health.mcp-dedup"]
    assert len(dedup) == 0


def test_missing_installed_json(tmp_path: Path) -> None:
    """Gracefully handles missing installed_plugins.json."""
    pd = tmp_path / "plugins"
    pd.mkdir(parents=True)

    result = validate_plugin_health(plugins_dir=pd, mcp_json_path=tmp_path / "no-mcp.json")

    info = [f for f in result.findings if f.rule == "plugin-health.no-installed-json"]
    assert len(info) == 1


def test_malformed_installed_json(tmp_path: Path) -> None:
    """Malformed JSON is reported as an error."""
    pd = tmp_path / "plugins"
    pd.mkdir(parents=True)
    (pd / "installed_plugins.json").write_text("not json{{{")

    result = validate_plugin_health(plugins_dir=pd, mcp_json_path=tmp_path / "no-mcp.json")

    errors = [f for f in result.findings if f.rule == "plugin-health.parse-error"]
    assert len(errors) == 1
    assert not result.passed
