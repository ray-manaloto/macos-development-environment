# Declarative Configuration Policy

- Python tool settings: pyproject.toml ([tool.ruff], [tool.ty], [tool.pytest])
- Git hooks: hk.pkl (managed by mise via `mise use hk`)
- CLI entry points: [project.scripts] in pyproject.toml
- Dev dependencies: [dependency-groups] in pyproject.toml
- NEVER create standalone config files (.cfg, .ini, .yaml) for Python tools
- NEVER use `uv run python` — use `uv run <entry-point>` or `uv run <tool>`
