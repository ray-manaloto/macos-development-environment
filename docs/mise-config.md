# mise Configuration

This project assumes `mise` is the runtime source of truth for Python, Node,
and Bun. pixi and uv are installed via their official installers when
missing, because their mise plugins are not consistently maintained.

## Example

Create `~/.config/mise/config.toml`:

```toml
[tools]
python = "latest"
node = "latest"
bun = "latest"
go = "latest"
rust = "latest"

[env]
# Identity
GITHUB_USER = "your_username"

# Provider keys
ANTHROPIC_API_KEY = "sk-ant-..."
OPENAI_API_KEY = "sk-proj-..."
GOOGLE_API_KEY = "AIza..."

# Python toolchain behavior
UV_NO_MANAGED_PYTHON = "1"

# LangChain observability
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_PROJECT = "agent-sandbox-local"
LANGCHAIN_API_KEY = "lsv2-..."
```

## Notes
- Keep secrets out of Git repositories.
- Prefer per-project `.env` or `direnv` for repo-scoped secrets.
- Ensure mise shims are early in `PATH` (handled in oh-my-zsh custom config).
