"""Skill YAML frontmatter validation."""

from __future__ import annotations

from pathlib import Path

from mde.models.result import ValidationResult

_MIN_FRONTMATTER_PARTS = 3


def validate_skill_frontmatter(root: Path | None = None) -> ValidationResult:
    """Validate YAML frontmatter in SKILL.md files under .agents/skills/."""
    result = ValidationResult()
    root = root or Path.cwd()
    skills_dir = root / ".agents" / "skills"
    if not skills_dir.exists():
        return result
    for skill_dir in sorted(skills_dir.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        result.files_checked += 1
        _validate_single_skill(result, skill_md)
    return result


def _validate_single_skill(result: ValidationResult, skill_md: Path) -> None:
    content = skill_md.read_text(encoding="utf-8")
    path = str(skill_md)
    if not content.startswith("---"):
        result.add_error(
            path,
            "Missing YAML frontmatter (must start with ---)",
            rule="skill.missing-frontmatter",
        )
        return
    parts = content.split("---", 2)
    if len(parts) < _MIN_FRONTMATTER_PARTS:
        result.add_error(
            path,
            "Incomplete YAML frontmatter (missing closing ---)",
            rule="skill.incomplete-frontmatter",
        )
        return
    fm = _parse_frontmatter(result, path, parts[1])
    if fm is None:
        return
    if "name" not in fm:
        result.add_error(
            path,
            "Frontmatter missing required 'name' field",
            rule="skill.missing-name",
        )
    if "description" not in fm:
        result.add_error(
            path,
            "Frontmatter missing required 'description' field",
            rule="skill.missing-description",
        )


def _parse_frontmatter(result: ValidationResult, path: str, raw: str) -> dict | None:
    """Parse YAML frontmatter, recording errors on failure."""
    import yaml

    try:
        fm = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        result.add_error(
            path,
            f"Invalid YAML frontmatter: {exc}",
            rule="skill.invalid-yaml",
        )
        return None
    if not isinstance(fm, dict):
        result.add_error(
            path,
            "Frontmatter is not a YAML mapping",
            rule="skill.invalid-frontmatter",
        )
        return None
    return fm
