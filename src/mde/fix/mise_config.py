"""Auto-fix: remove bad includes, 404 packages from mise config."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def fix_mise_config(root: Path | None = None) -> int:
    """Auto-fix known mise config issues.

    Args:
        root: Project root. Defaults to cwd.

    Returns:
        Number of fixes applied.
    """
    root = root or Path.cwd()
    mise_toml = root / ".mise.toml"
    if not mise_toml.exists():
        return 0

    content = mise_toml.read_text(encoding="utf-8")
    original = content

    # Parse to check for issues
    try:
        data = tomllib.loads(content)
    except (ValueError, KeyError):
        print(f"Cannot parse {mise_toml} — skipping auto-fix")
        return 0

    fixes = 0

    # Remove includes pointing to non-existent files
    includes = data.get("includes", [])
    if isinstance(includes, list):
        for include in includes:
            include_path = root / str(include)
            if not include_path.exists():
                # Remove the line containing this include
                lines = content.splitlines(keepends=True)
                content = "".join(line for line in lines if str(include) not in line)
                fixes += 1
                print(f"  Removed missing include: {include}")

    if content != original:
        mise_toml.write_text(content, encoding="utf-8")
    return fixes
