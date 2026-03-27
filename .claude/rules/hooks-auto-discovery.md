# Hooks Auto-Discovery Policy

## Adding New Hooks

New Claude Code hooks MUST follow the auto-discovery convention:

1. Create `src/mde/hooks/<name>.py` (snake_case, no leading underscore)
2. Add `__hook_meta__` dict at module level with `help` and `entry` keys
3. Do NOT edit `src/mde/cli.py` — hooks are auto-discovered from the module
4. Wire the hook in `.claude/settings.json` as `uv run mde-py hooks <kebab-case-name>`

## Required module structure

Every hook module in `src/mde/hooks/` (except `__init__.py` and `_*.py`) MUST have:

```python
"""One-line description of what this hook does.

<longer description of when/how it's called>
"""

from __future__ import annotations

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "Short help text shown in `mde-py hooks --help`",
    "entry": "function_name",  # the callable that returns int
}
```

Optional `name` key overrides the filename-derived command name (e.g., when the
module filename doesn't match the desired CLI subcommand):

```python
__hook_meta__ = {
    "name": "log-edit-outcome",  # override: log_outcome.py → log-edit-outcome
    "help": "PostToolUse logger",
    "entry": "log_edit_outcome",
}
```

## File path checks

- Hook modules: `src/mde/hooks/<snake_case>.py` — never standalone .sh files
- Hook tests: `tests/mde/test_hooks.py` or `tests/mde/test_hook_<name>.py`
- Hook wiring: `.claude/settings.json` hooks section — command must be `uv run mde-py hooks <kebab>`
- NEVER create hooks outside `src/mde/hooks/` — no `scripts/`, no `.claude/hooks/`, no plugin `hooks.json` for project-level hooks

## Third-party hook exceptions

Hooks maintained by external tools (e.g., `rtk init -g` creates `$HOME/.claude/hooks/rtk-rewrite.sh`)
are exempt from the auto-discovery requirement. These are upstream-managed artifacts, not project
automation. Wire them in `.claude/settings.json` using `$HOME` (not absolute paths) for portability.
Do not use third-party hooks as precedent for adding project `.sh` files.

## Non-hook modules

Modules without `__hook_meta__` (e.g., `_common.py`, `_agent_frontmatter_model.py`)
are silently skipped by auto-discovery. Prefix private/utility modules with `_`.
