# MCP Access Policy

- NEVER use MCP tool schemas directly in the context window (wastes 96-99% of tokens)
- Use mcp2cli baked tools: `mcp2cli @<name> <tool> [args]`
- Use cli-anything generated CLIs for GUI applications
- For GitHub: `mcp2cli @github <tool> --arg value`
- For Docker: `mcp2cli @docker <tool> --arg value`
- For new MCP servers: `mcp2cli bake create <name> --mcp-stdio "<command>"`
- TOON output format (--toon) for large uniform arrays (40-60% token savings)
- Secret values use `env:` or `file:` prefix, never bare CLI arguments
