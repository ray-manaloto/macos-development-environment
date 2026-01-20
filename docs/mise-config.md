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

# Python toolchain behavior
UV_NO_MANAGED_PYTHON = "1"

# LangChain observability (non-secret)
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_PROJECT = "agent-sandbox-local"
```

## Notes
- Keep secrets out of Git repositories.
- Prefer `~/.config/macos-development-environment/secrets.env` for global API keys.
- Use per-project `.env` or `direnv` for repo-scoped secrets.
- Ensure mise shims are early in `PATH` (handled in oh-my-zsh custom config).
