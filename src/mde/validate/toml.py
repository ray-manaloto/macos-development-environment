"""TOML syntax and mise schema validation."""

from __future__ import annotations

import sys
from pathlib import Path

from mde.models.result import Severity, ValidationResult

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def validate_toml_files(
    *,
    root: Path | None = None,
    fix: bool = False,
) -> ValidationResult:
    """Validate all TOML files in the project.

    Args:
        root: Project root directory. Defaults to cwd.
        fix: Auto-fix known issues (removes bad includes, etc.).

    Returns:
        ValidationResult with findings.
    """
    result = ValidationResult()
    root = root or Path.cwd()

    toml_files: list[Path] = [
        root / ".mise.toml",
        *root.glob("configs/**/*.toml"),
    ]
    chezmoi_src = root / ".chezmoisource"
    if chezmoi_src.exists():
        toml_files.extend(chezmoi_src.rglob("*.toml"))

    for path in toml_files:
        if not path.exists():
            continue
        result.files_checked += 1
        _validate_single_toml(path, result, fix=fix)

    return result


def _validate_single_toml(path: Path, result: ValidationResult, *, fix: bool) -> None:
    """Validate a single TOML file for syntax errors."""
    try:
        content = path.read_text(encoding="utf-8")
        tomllib.loads(content)
    except (ValueError, KeyError) as exc:
        result.add(
            path=str(path),
            message=f"TOML syntax error: {exc}",
            rule="toml.syntax",
            fixable=False,
        )
        return

    # Check for common mise config issues
    if path.name == ".mise.toml" or "mise" in path.name:
        _check_mise_toml(path, content, result, fix=fix)


def _check_mise_toml(
    path: Path,
    content: str,
    result: ValidationResult,
    *,
    fix: bool,
) -> None:
    """Check mise-specific TOML issues."""
    data = tomllib.loads(content)

    # Check for includes pointing to non-existent files
    includes = data.get("includes", [])
    if isinstance(includes, list):
        for include in includes:
            include_str = str(include)
            include_path = path.parent / include_str
            if not include_path.exists():
                result.add(
                    path=str(path),
                    message=f"Include path does not exist: {include_str}",
                    severity=Severity.ERROR,
                    rule="mise.include.missing",
                    fixable=True,
                )
                if fix:
                    _remove_include(path, include_str)

    # Check for deprecated ubi: backend
    tools = data.get("tools", {})
    if isinstance(tools, dict):
        for tool_name, tool_spec in tools.items():
            spec_str = str(tool_spec)
            if spec_str.startswith("ubi:"):
                result.add(
                    path=str(path),
                    message=f"Tool '{tool_name}' uses deprecated 'ubi:' backend, use 'github:'",
                    severity=Severity.WARNING,
                    rule="mise.tool.deprecated-backend",
                    fixable=True,
                )


def _remove_include(path: Path, include_str: str) -> None:
    """Remove a bad include entry from a TOML file."""
    content = path.read_text(encoding="utf-8")
    # Simple line-based removal for includes
    lines = content.splitlines(keepends=True)
    filtered = [line for line in lines if include_str not in line]
    path.write_text("".join(filtered), encoding="utf-8")
