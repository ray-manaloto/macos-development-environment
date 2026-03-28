"""Validate rsm-subagents marketplace plugins.

Runs `claude plugin validate` on the marketplace and each plugin,
then checks skill/agent/command frontmatter and reference integrity.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import yaml

from mde.models.result import ValidationResult

_MARKETPLACE_DIR = "rsm-subagents"
_MARKETPLACE_JSON = ".claude-plugin/marketplace.json"
_PLUGIN_JSON = ".claude-plugin/plugin.json"

# Fields that claude plugin validate rejects as unrecognized
_FORBIDDEN_PLUGIN_KEYS = {"minVersion"}

# Required agent frontmatter fields
_AGENT_REQUIRED_FIELDS = {"name", "description", "model", "color"}

# Required skill frontmatter fields
_SKILL_REQUIRED_FIELDS = {"name", "description"}

# Required command frontmatter fields
_COMMAND_REQUIRED_FIELDS = {"description"}


def validate_plugins(root: Path | None = None) -> ValidationResult:
    """Validate the rsm-subagents marketplace and all its plugins."""
    result = ValidationResult()
    root = root or Path.cwd()
    marketplace_dir = root / _MARKETPLACE_DIR

    if not marketplace_dir.exists():
        result.add_info(
            str(marketplace_dir),
            "rsm-subagents directory not found, skipping plugin validation",
            rule="plugin.no-marketplace",
        )
        return result

    # 0. Check for absolute marketplace paths in settings.json
    _check_marketplace_path_portability(result, root)

    # 1. Validate marketplace manifest
    _validate_marketplace_cli(result, marketplace_dir)

    # 2. Parse marketplace.json and iterate plugins
    manifest_path = marketplace_dir / _MARKETPLACE_JSON
    if not manifest_path.exists():
        result.add_error(
            str(manifest_path),
            "Missing marketplace.json",
            rule="plugin.missing-manifest",
        )
        return result

    result.files_checked += 1
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.add_error(
            str(manifest_path),
            f"Invalid JSON: {exc}",
            rule="plugin.invalid-json",
        )
        return result

    plugins = manifest.get("plugins", [])
    if not plugins:
        result.add_warning(
            str(manifest_path),
            "No plugins listed in marketplace.json",
            rule="plugin.empty-marketplace",
        )
        return result

    for plugin_entry in plugins:
        plugin_name = plugin_entry.get("name", "unknown")
        source = plugin_entry.get("source", "")
        plugin_dir = marketplace_dir / source.lstrip("./")

        if not plugin_dir.exists():
            result.add_error(
                str(plugin_dir),
                f"Plugin directory not found for '{plugin_name}'",
                rule="plugin.missing-dir",
            )
            continue

        # 2a. claude plugin validate
        _validate_plugin_cli(result, plugin_dir, plugin_name)

        # 2b. Check plugin.json for forbidden keys
        _validate_plugin_json(result, plugin_dir, plugin_name)

        # 2c. Validate skills
        _validate_skills(result, plugin_dir, plugin_name)

        # 2d. Validate agents
        _validate_agents(result, plugin_dir, plugin_name)

        # 2e. Validate commands
        _validate_commands(result, plugin_dir, plugin_name)

        # 2f. Validate hooks
        _validate_hooks(result, plugin_dir, plugin_name)

    return result


def _check_marketplace_path_portability(result: ValidationResult, root: Path) -> None:
    """Warn if settings.json has absolute paths for marketplace directories."""
    settings_path = root / ".claude" / "settings.json"
    if not settings_path.exists():
        return

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    marketplaces = data.get("pluginMarketplaces", {})
    for name, config in marketplaces.items():
        source = config.get("source", {})
        if source.get("source") == "directory":
            path = source.get("path", "")
            if path.startswith("/"):
                result.add_warning(
                    str(settings_path),
                    f"Marketplace '{name}' uses absolute path '{path}' — "
                    "use a relative path (e.g. './rsm-subagents') for portability",
                    rule="plugin.absolute-marketplace-path",
                )


def _run_claude_validate(target: Path) -> tuple[bool, str]:
    """Run `claude plugin validate <path>` and return (passed, output)."""
    try:
        proc = subprocess.run(
            ["claude", "plugin", "validate", str(target)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = proc.stdout + proc.stderr
        passed = proc.returncode == 0 and "Validation passed" in output
        return passed, output.strip()
    except FileNotFoundError:
        return False, "claude CLI not found"
    except subprocess.TimeoutExpired:
        return False, "claude plugin validate timed out"


def _validate_marketplace_cli(result: ValidationResult, marketplace_dir: Path) -> None:
    """Run claude plugin validate on the marketplace."""
    result.files_checked += 1
    passed, output = _run_claude_validate(marketplace_dir)
    if not passed:
        result.add_error(
            str(marketplace_dir),
            f"Marketplace validation failed: {output}",
            rule="plugin.marketplace-validate",
        )


def _validate_plugin_cli(result: ValidationResult, plugin_dir: Path, name: str) -> None:
    """Run claude plugin validate on a single plugin."""
    result.files_checked += 1
    passed, output = _run_claude_validate(plugin_dir)
    if not passed:
        result.add_error(
            str(plugin_dir),
            f"Plugin '{name}' validation failed: {output}",
            rule="plugin.cli-validate",
        )


def _validate_plugin_json(result: ValidationResult, plugin_dir: Path, name: str) -> None:
    """Check plugin.json for forbidden keys and required fields."""
    pj = plugin_dir / _PLUGIN_JSON
    if not pj.exists():
        result.add_error(
            str(pj),
            f"Plugin '{name}' missing plugin.json",
            rule="plugin.missing-plugin-json",
        )
        return

    result.files_checked += 1
    try:
        data = json.loads(pj.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.add_error(str(pj), f"Invalid JSON: {exc}", rule="plugin.invalid-json")
        return

    # Check for forbidden keys
    for key in _FORBIDDEN_PLUGIN_KEYS:
        if key in data:
            result.add_error(
                str(pj),
                f"Forbidden key '{key}' in plugin.json (causes validation failure)",
                rule="plugin.forbidden-key",
            )

    # Check required name field
    if "name" not in data:
        result.add_error(
            str(pj),
            "Missing required 'name' field",
            rule="plugin.missing-name",
        )


def _validate_skills(result: ValidationResult, plugin_dir: Path, _plugin_name: str) -> None:
    """Validate all SKILL.md files in a plugin."""
    skills_dir = plugin_dir / "skills"
    if not skills_dir.exists():
        return

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            result.add_warning(
                str(skill_dir),
                f"Skill directory '{skill_dir.name}' has no SKILL.md",
                rule="plugin.skill-missing-md",
            )
            continue

        result.files_checked += 1
        fm = _parse_yaml_frontmatter(result, skill_md)
        if fm is None:
            continue

        # Check required fields
        for field in _SKILL_REQUIRED_FIELDS:
            if field not in fm:
                result.add_error(
                    str(skill_md),
                    f"Skill missing required '{field}' field",
                    rule=f"plugin.skill-missing-{field}",
                )

        # Check description uses third person
        desc = fm.get("description", "")
        if desc and not re.search(r"[Tt]his skill", desc):
            result.add_warning(
                str(skill_md),
                "Skill description should use third person ('This skill should be used when...')",
                rule="plugin.skill-third-person",
            )

        # Check for references that don't exist
        _validate_references(result, skill_md, skill_dir)


def _validate_agents(result: ValidationResult, plugin_dir: Path, _plugin_name: str) -> None:
    """Validate all agent .md files in a plugin."""
    agents_dir = plugin_dir / "agents"
    if not agents_dir.exists():
        return

    for agent_md in sorted(agents_dir.glob("*.md")):
        result.files_checked += 1
        fm = _parse_yaml_frontmatter(result, agent_md)
        if fm is None:
            continue

        for field in _AGENT_REQUIRED_FIELDS:
            if field not in fm:
                result.add_error(
                    str(agent_md),
                    f"Agent missing required '{field}' field",
                    rule=f"plugin.agent-missing-{field}",
                )

        # Check agent name format (3-50 chars, lowercase + hyphens)
        name = fm.get("name", "")
        if name and not re.match(r"^[a-z0-9][a-z0-9-]{1,48}[a-z0-9]$", name):
            result.add_warning(
                str(agent_md),
                f"Agent name '{name}' should be 3-50 chars, lowercase + hyphens",
                rule="plugin.agent-name-format",
            )

        # Check description has <example> blocks
        desc = fm.get("description", "")
        if desc and "<example>" not in desc:
            result.add_warning(
                str(agent_md),
                "Agent description should include <example> blocks for triggering",
                rule="plugin.agent-missing-examples",
            )

        # Check model is valid
        model = fm.get("model", "")
        valid_models = {"inherit", "sonnet", "opus", "haiku"}
        if model and model not in valid_models:
            result.add_error(
                str(agent_md),
                f"Invalid model '{model}' (must be one of {valid_models})",
                rule="plugin.agent-invalid-model",
            )

        # Check color is valid
        color = fm.get("color", "")
        valid_colors = {"blue", "cyan", "green", "yellow", "magenta", "red"}
        if color and color not in valid_colors:
            result.add_error(
                str(agent_md),
                f"Invalid color '{color}' (must be one of {valid_colors})",
                rule="plugin.agent-invalid-color",
            )


def _validate_commands(result: ValidationResult, plugin_dir: Path, _plugin_name: str) -> None:
    """Validate all command .md files in a plugin."""
    commands_dir = plugin_dir / "commands"
    if not commands_dir.exists():
        return

    for cmd_md in sorted(commands_dir.glob("*.md")):
        result.files_checked += 1
        fm = _parse_yaml_frontmatter(result, cmd_md)
        if fm is None:
            continue

        for field in _COMMAND_REQUIRED_FIELDS:
            if field not in fm:
                result.add_error(
                    str(cmd_md),
                    f"Command missing required '{field}' field",
                    rule=f"plugin.command-missing-{field}",
                )

        # Commands should have allowed-tools
        if "allowed-tools" not in fm:
            result.add_warning(
                str(cmd_md),
                "Command should specify 'allowed-tools' for least privilege",
                rule="plugin.command-missing-allowed-tools",
            )


def _validate_hooks(result: ValidationResult, plugin_dir: Path, _plugin_name: str) -> None:
    """Validate hooks.json if present."""
    hooks_json = plugin_dir / "hooks" / "hooks.json"
    if not hooks_json.exists():
        return

    result.files_checked += 1
    try:
        json.loads(hooks_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.add_error(
            str(hooks_json),
            f"Invalid hooks.json: {exc}",
            rule="plugin.invalid-hooks-json",
        )


def _validate_references(result: ValidationResult, skill_md: Path, skill_dir: Path) -> None:
    """Check that all `references/*.md` paths mentioned in SKILL.md exist."""
    content = skill_md.read_text(encoding="utf-8")
    refs = re.findall(r"references/[\w-]+\.md", content)
    for ref in set(refs):
        ref_path = skill_dir / ref
        if not ref_path.exists():
            result.add_error(
                str(skill_md),
                f"Referenced file '{ref}' does not exist",
                rule="plugin.missing-reference",
            )


def _parse_yaml_frontmatter(result: ValidationResult, md_file: Path) -> dict | None:
    """Parse YAML frontmatter from a markdown file."""
    content = md_file.read_text(encoding="utf-8")
    path = str(md_file)

    if not content.startswith("---"):
        result.add_error(
            path,
            "Missing YAML frontmatter (must start with ---)",
            rule="plugin.missing-frontmatter",
        )
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:  # noqa: PLR2004
        result.add_error(
            path,
            "Incomplete YAML frontmatter (missing closing ---)",
            rule="plugin.incomplete-frontmatter",
        )
        return None

    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        result.add_error(
            path,
            f"Invalid YAML frontmatter: {exc}",
            rule="plugin.invalid-yaml",
        )
        return None

    if not isinstance(fm, dict):
        result.add_error(
            path,
            "Frontmatter is not a YAML mapping",
            rule="plugin.invalid-frontmatter",
        )
        return None

    return fm
