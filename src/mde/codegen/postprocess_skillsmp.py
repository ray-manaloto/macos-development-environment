"""Post-generation edits for SkillsMP models.

Applied automatically after datamodel-codegen produces raw output from
docs/schemas/skillsmp.schema.json. Three edits:

1. Remove SkillsmpApiModels RootModel wrapper ($defs-only schema artifact)
2. Add __all__ for explicit public API
3. Add populate_by_name=True to Skill (camelCase API, snake_case Python)

Usage:
    uv run python -m mde.codegen.postprocess_skillsmp
"""

from __future__ import annotations

import re
from pathlib import Path

_TARGET = Path("src/mde/research/clients/skillsmp_models.py")

_ALL_EXPORTS = """
__all__ = [
    "AISearchData",
    "AISearchResponse",
    "AISearchResult",
    "ErrorDetail",
    "ErrorResponse",
    "Skill",
    "SkillSearchData",
    "SkillSearchResponse",
]
"""

_POST_GEN_HEADER = """\
#
# Post-generation edits (applied automatically by mde:codegen:skillsmp task):
#   - Removed SkillsmpApiModels RootModel wrapper (artifact of defs-only schema)
#   - Added __all__ for explicit public API
#   - Added populate_by_name=True to Skill model_config (API returns camelCase,
#     but Python code accesses snake_case attributes like skill.github_url)"""


def postprocess() -> None:
    """Apply post-generation edits to the SkillsMP models file."""
    text = _TARGET.read_text()

    # 1. Remove RootModel wrapper class
    text = re.sub(
        r"class SkillsmpApiModels\(RootModel\[Any\]\):.*?\n\n\n",
        "",
        text,
        flags=re.DOTALL,
    )
    text = text.replace(", Any", "").replace(", RootModel", "")

    # 2. Add populate_by_name=True to Skill model_config
    text = text.replace(
        'class Skill(BaseModel):\n    model_config = ConfigDict(\n        extra="allow",\n    )',
        "class Skill(BaseModel):\n    model_config = ConfigDict(\n"
        '        extra="allow",\n        populate_by_name=True,\n    )',
    )

    # 3. Add __all__ after imports
    marker = "\n\nclass "
    idx = text.index(marker)
    text = text[:idx] + "\n" + _ALL_EXPORTS + text[idx:]

    # 4. Add post-gen header comment after codegen metadata lines
    lines = text.split("\n")
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("#"):
            insert_idx = i + 1
        else:
            break
    lines.insert(insert_idx, _POST_GEN_HEADER)
    text = "\n".join(lines)

    # Clean up excess blank lines
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    _TARGET.write_text(text)
    print("Post-gen edits applied to", _TARGET)


if __name__ == "__main__":
    postprocess()
