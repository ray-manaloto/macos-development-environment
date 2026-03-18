# No Shell Scripts Policy

- ALL automation/hook logic MUST be Python modules in src/mde/
- Claude Code hooks MUST call `uv run mde-py hooks <subcommand>`, never .sh files
- Use `uv run <tool>` for ruff, ty, pytest — never `uv run python -m <module>`
- All tool configuration MUST be in pyproject.toml — no standalone .cfg, .ini, or YAML
- Declarative configuration is required: hk.pkl for git hooks, pyproject.toml for Python tools
