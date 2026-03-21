"""PostToolUse hook: validate agent frontmatter on Write/Edit to .claude/agents/.

Uses Pydantic model generated from docs/schemas/agent-frontmatter.schema.json
via datamodel-code-generator. Regenerate the model after schema changes:

    uv run datamodel-codegen \
      --input docs/schemas/agent-frontmatter.schema.json \
      --output src/mde/hooks/agent_frontmatter_model.py \
      --input-file-type jsonschema \
      --output-model-type pydantic_v2.BaseModel \
      --target-python-version 3.12
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import ValidationError

if TYPE_CHECKING:
    from pydantic_core import ErrorDetails

from mde.hooks.agent_frontmatter_model import ClaudeCodeAgentFrontmatter

_AGENTS_DIR = ".claude/agents/"


def _extract_frontmatter(text: str) -> tuple[dict[str, Any] | None, str | None]:
    """Extract YAML frontmatter from a markdown file's content.

    Returns a tuple (frontmatter, error):
    - (dict, None)  — valid frontmatter parsed successfully
    - (None, None)  — no frontmatter delimiters found
    - (None, str)   — frontmatter delimiters present but YAML is malformed
    """
    if not text.startswith("---"):
        return None, None
    end = text.find("---", 3)
    if end == -1:
        return None, None
    raw = text[3:end].strip()
    if not raw:
        return None, None
    try:
        result = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return None, f"malformed YAML: {exc}"
    if not isinstance(result, dict):
        return None, None
    return result, None


def validate_agent_frontmatter(frontmatter: dict[str, Any]) -> list[str]:
    """Validate agent frontmatter dict against the Pydantic model.

    Returns a list of human-readable error messages (empty if valid).
    """
    try:
        ClaudeCodeAgentFrontmatter.model_validate(frontmatter)
    except ValidationError as exc:
        return [_format_pydantic_error(e) for e in exc.errors()]
    return []


def _format_pydantic_error(error: ErrorDetails) -> str:
    """Convert a single Pydantic error dict to a human-readable string."""
    loc = error.get("loc", ())
    msg = error.get("msg", "validation error")
    err_type = error.get("type", "")

    if err_type == "missing":
        field = loc[-1] if loc else "unknown"
        return f"missing required field: {field}"

    if err_type == "extra_forbidden":
        field = loc[-1] if loc else "unknown"
        return f"unknown field(s): {field}"

    if loc:
        field = ".".join(str(p) for p in loc)
        return f"'{field}': {msg}"

    return msg


def validate_agent_file(path: Path) -> list[str]:
    """Validate a single agent .md file, returning error messages."""
    if not path.exists():
        return [f"file not found: {path}"]
    text = path.read_text(encoding="utf-8")
    fm, parse_error = _extract_frontmatter(text)
    if fm is None:
        if parse_error is not None:
            return [f"{path.name}: {parse_error}"]
        return [f"no YAML frontmatter in {path.name}"]

    errors = validate_agent_frontmatter(fm)
    name = fm.get("name")
    if isinstance(name, str) and name != path.stem:
        errors.append(f"'name' ({name}) does not match filename ({path.stem})")
    return [f"{path.name}: {e}" for e in errors]


def validate_all_agents(agents_dir: Path | None = None) -> list[str]:
    """Validate all .claude/agents/*.md files, returning all errors."""
    if agents_dir is None:
        agents_dir = Path(".claude/agents")
    if not agents_dir.is_dir():
        return [f"agents directory not found: {agents_dir}"]
    errors: list[str] = []
    for md in sorted(agents_dir.glob("*.md")):
        errors.extend(validate_agent_file(md))
    return errors


def validate_agents_hook() -> int:
    """PostToolUse hook entry point.

    Reads hook JSON from stdin.  If the edited file is under .claude/agents/,
    validates its frontmatter and prints errors to stderr.  Exit 1 signals
    validation failure (PostToolUse cannot block -- the edit already happened).
    """
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path or _AGENTS_DIR not in file_path:
        return 0

    path = Path(file_path)
    errors = validate_agent_file(path)
    if errors:
        msg = "Agent frontmatter validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        print(msg, file=sys.stderr)
        return 1

    return 0
