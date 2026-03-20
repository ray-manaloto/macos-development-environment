# Library-First Policy

- ALWAYS search for existing libraries before writing code from scratch
- Use context7, PyPI, npm, or WebSearch to find battle-tested solutions
- Prefer libraries already in the dependency tree (check pyproject.toml)
- For Python: check if pydantic, anyio, or other existing deps provide the feature
- For structured logging: use structlog or stdlib logging with JSON formatter, not custom file writes
- For schema validation: use Pydantic models generated from JSON Schema, not hand-coded validation
- For async file I/O: check if anyio (already a dep) provides what you need before adding aiofiles
- Document WHY a library was chosen or rejected in commit messages
- When adding a new dependency, declare it in pyproject.toml per declarative-config policy
- ALWAYS search skills.sh and awesome-claude-plugins/skills before creating new skills or agents
- For research: use agent-fetch, notebooklm CLI, second-brain skill — don't build custom tools
