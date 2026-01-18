# IDE Integrations

## Cursor
- Best for day-to-day coding and existing codebases.
- Use Composer mode for multi-file edits.
- Add a `.cursorrules` file per repo with agent-specific guidance.
- Use MCP connections for local data sources (Settings > Features > MCP).

## JetBrains (PyCharm/CLion/GoLand)
- Best for deep debugging.
- Use `langsmith-fetch run <RUN_ID>` to download traces from LangSmith and
  debug locally.

## Antigravity / Project IDX
- Best for greenfield prototypes and full-stack scaffolding.
- Use the agent manager for high-level goals, then review and approve plans
  before generating artifacts.
