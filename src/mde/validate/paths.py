"""Validate .generated/ path centralization conventions.

Checks that environment variables, symlinks, config files, and code
references follow the centralized path architecture defined in the
centralize-generated-paths plan.
"""

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path

from mde.models.result import ValidationResult

# Environment variables that should be set when mise is active
_EXPECTED_ENV_VARS = ("MDE_PROJECT_DIR", "MDE_GENERATED_DIR")

# Regex for chezmoi template expressions
_CHEZMOI_TEMPLATE_RE = re.compile(r"\{\{.*?\}\}")

# Files that are allowed to reference ".generated" literally
_HARDCODED_ALLOWLIST = {
    "paths.py",
    "test_validate_paths.py",
}


def validate_paths(root: Path | None = None) -> ValidationResult:
    """Run all 9 path-centralisation checks.

    Args:
        root: Project root directory. Defaults to cwd.

    Returns:
        ValidationResult with findings.
    """
    result = ValidationResult()
    root = root or Path.cwd()

    _check_env_var_missing(result)
    _check_dir_missing(result)
    _check_remember_symlink(root, result)
    _check_mise_global_missing(result)
    _check_chezmoi_template_missing(root, result)
    _check_hardcoded_ref(root, result)
    _check_reference_doc_missing(root, result)
    _check_composition_violation(root, result)
    _check_env_shell_expand_missing(result)

    return result


# ---------------------------------------------------------------------------
# Check 1: paths.env-var-missing (WARNING)
# ---------------------------------------------------------------------------
def _check_env_var_missing(result: ValidationResult) -> None:
    """MDE_GENERATED_DIR should be in env when mise is active."""
    for var in _EXPECTED_ENV_VARS:
        if not os.environ.get(var):
            result.add_warning(
                path="env",
                message=f"{var} is not set. Ensure mise global config exports it.",
                rule="paths.env-var-missing",
            )


# ---------------------------------------------------------------------------
# Check 2: paths.dir-missing (WARNING)
# ---------------------------------------------------------------------------
def _check_dir_missing(result: ValidationResult) -> None:
    """Env var values should point to existing directories."""
    for var in _EXPECTED_ENV_VARS:
        value = os.environ.get(var)
        if value and not Path(value).is_dir():
            result.add_warning(
                path="env",
                message=f"{var}={value} does not point to an existing directory.",
                rule="paths.dir-missing",
            )


# ---------------------------------------------------------------------------
# Check 3: paths.remember-symlink (ERROR)
# ---------------------------------------------------------------------------
def _check_remember_symlink(root: Path, result: ValidationResult) -> None:
    """.remember must be a symlink, not a directory."""
    remember = root / ".remember"
    if remember.exists() or remember.is_symlink():
        result.files_checked += 1
        if remember.is_dir() and not remember.is_symlink():
            result.add_error(
                path=str(remember),
                message=(
                    ".remember is a directory, not a symlink. "
                    "Run: uv run mde-py migrate consolidate-generated"
                ),
                rule="paths.remember-symlink",
                fixable=True,
            )


# ---------------------------------------------------------------------------
# Check 4: paths.mise-global-missing (ERROR)
# ---------------------------------------------------------------------------
def _check_mise_global_missing(result: ValidationResult) -> None:
    """~/.config/mise/config.toml must contain MDE_PROJECT_DIR in [env]."""
    mise_config = Path.home() / ".config" / "mise" / "config.toml"
    if not mise_config.exists():
        return

    result.files_checked += 1
    try:
        parsed = tomllib.loads(mise_config.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        result.add_error(
            path=str(mise_config),
            message="Global mise config is not valid TOML.",
            rule="paths.mise-global-missing",
        )
        return

    env = parsed.get("env", {})
    if "MDE_PROJECT_DIR" not in env:
        result.add_error(
            path=str(mise_config),
            message="Global mise config missing MDE_PROJECT_DIR in [env].",
            rule="paths.mise-global-missing",
        )


# ---------------------------------------------------------------------------
# Check 5: paths.chezmoi-template-missing (ERROR)
# ---------------------------------------------------------------------------
def _check_chezmoi_template_missing(root: Path, result: ValidationResult) -> None:
    """Chezmoi template must contain MDE_PROJECT_DIR."""
    tpl = root / "home" / "dot_config" / "mise" / "config.toml.tmpl"
    if not tpl.exists():
        return

    result.files_checked += 1
    content = tpl.read_text(encoding="utf-8")
    if "MDE_PROJECT_DIR" not in content:
        result.add_error(
            path=str(tpl),
            message="Chezmoi template missing MDE_PROJECT_DIR declaration.",
            rule="paths.chezmoi-template-missing",
        )


# ---------------------------------------------------------------------------
# Check 6: paths.hardcoded-ref (WARNING)
# ---------------------------------------------------------------------------
def _check_hardcoded_ref(root: Path, result: ValidationResult) -> None:
    """No .py file (except allowlisted) should contain literal '.generated'."""
    src_dir = root / "src" / "mde"
    if not src_dir.is_dir():
        return

    for py_file in src_dir.rglob("*.py"):
        if py_file.name in _HARDCODED_ALLOWLIST:
            continue
        result.files_checked += 1
        try:
            content = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            if line.lstrip().startswith("#"):
                continue
            if '".generated"' in line or "'.generated'" in line:
                result.add_warning(
                    path=str(py_file),
                    message=(
                        'Hardcoded ".generated" reference. Use MDE_GENERATED_DIR env var instead.'
                    ),
                    rule="paths.hardcoded-ref",
                    line=lineno,
                )


# ---------------------------------------------------------------------------
# Check 7: paths.reference-doc-missing (ERROR)
# ---------------------------------------------------------------------------
def _check_reference_doc_missing(root: Path, result: ValidationResult) -> None:
    """.claude/rules/generated-paths.md must exist."""
    doc = root / ".claude" / "rules" / "generated-paths.md"
    result.files_checked += 1
    if not doc.exists():
        result.add_error(
            path=str(doc),
            message="Reference doc generated-paths.md not found in .claude/rules/.",
            rule="paths.reference-doc-missing",
        )


# ---------------------------------------------------------------------------
# Check 8: paths.composition-violation (ERROR)
# ---------------------------------------------------------------------------
def _check_composition_violation(root: Path, result: ValidationResult) -> None:
    """In chezmoi template, only MDE_PROJECT_DIR may use chezmoi template vars."""
    tpl = root / "home" / "dot_config" / "mise" / "config.toml.tmpl"
    if not tpl.exists():
        return

    result.files_checked += 1
    in_env = False
    for lineno, line in enumerate(tpl.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        # Track [env] section
        if stripped.startswith("["):
            in_env = stripped == "[env]"
            continue
        if not in_env:
            continue

        # Skip blank lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Parse KEY = VALUE lines
        if "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()

        # MDE_PROJECT_DIR is allowed to use chezmoi templates
        if key == "MDE_PROJECT_DIR":
            continue

        # Only check MDE_* child variables for composition violations;
        # non-MDE vars (CC, LDFLAGS, _.path, etc.) legitimately use
        # chezmoi templates for platform-specific values.
        if not key.startswith("MDE_"):
            continue

        # MDE_* child var using chezmoi template syntax is a violation
        value = stripped.split("=", 1)[1]
        if _CHEZMOI_TEMPLATE_RE.search(value):
            result.add_error(
                path=str(tpl),
                message=(
                    f"Composition violation: {key} uses chezmoi template vars. "
                    f"Only MDE_PROJECT_DIR should reference chezmoi directly; "
                    f"derive child paths from MDE_PROJECT_DIR."
                ),
                rule="paths.composition-violation",
                line=lineno,
            )


# ---------------------------------------------------------------------------
# Check 9: paths.env-shell-expand-missing (ERROR)
# ---------------------------------------------------------------------------
def _check_env_shell_expand_missing(result: ValidationResult) -> None:
    """Global mise config must have env_shell_expand = true in [settings]."""
    mise_config = Path.home() / ".config" / "mise" / "config.toml"
    if not mise_config.exists():
        return

    # files_checked already incremented by check 4
    try:
        parsed = tomllib.loads(mise_config.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return  # already reported by check 4

    settings = parsed.get("settings", {})
    if settings.get("env_shell_expand") is not True:
        result.add_error(
            path=str(mise_config),
            message=(
                "Global mise config missing env_shell_expand = true in [settings]. "
                "Required for $MDE_PROJECT_DIR expansion in child vars."
            ),
            rule="paths.env-shell-expand-missing",
        )
