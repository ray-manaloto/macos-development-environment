# mise Configuration

This project assumes `mise` is the runtime source of truth. Use a global
config to pin runtimes and expose shared environment variables.

## Example

Create `~/.config/mise/config.toml`:

```toml
[tools]
python = "latest"
node = "latest"
bun = "latest"
uv = "latest"
pixi = "latest"

[env]
# Identity
GITHUB_USER = "your_username"

# Provider keys
ANTHROPIC_API_KEY = "sk-ant-..."
OPENAI_API_KEY = "sk-proj-..."
GOOGLE_API_KEY = "AIza..."

# LangChain observability
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_PROJECT = "agent-sandbox-local"
LANGCHAIN_API_KEY = "lsv2-..."
```

## Notes
- Keep secrets out of Git repositories.
- `mise` integrates best when its shims are early in `PATH`.
- Prefer project-specific `.env` files for repo-scoped secrets.
