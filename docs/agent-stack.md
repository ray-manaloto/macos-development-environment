# AI Agent Stack (macOS)

This stack is a superset of LangChain tooling that includes general-purpose
agent CLIs (Claude/Codex/OpenCode/Aider/etc.). It follows the preference
order:

- mise for runtimes (python/node/bun/go/rust)
- pixi for Python tools (fallback to uv, then pip)
- bun for Node tools

## Install / Update

Use the installer script:

```bash
scripts/install-agent-stack.sh
```

Install AI research skills marketplace (Claude Code plugins):

```bash
scripts/install-ai-research-skills.sh
```

Maintenance integration:
- When `MDE_UPDATE_AGENT_TOOLS=1` (default), the weekly maintenance job runs
  this installer to keep tools updated.

Options:
- `PIXI_ENV=agent-stack` to change the pixi global environment name.
- `INCLUDE_OPTIONAL=0` to skip optional tools like `gh copilot` and `fabric`.
- `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1` is enabled by default to build
  PyO3-based wheels on newer Python versions.
- `TOOL_PYTHON_VERSION=3.12` to install Python tools using a
  stable runtime even when `python@latest` is newer.
- `MDE_AI_RESEARCH_FORCE=1` to reinstall all AI research skills plugins.

## Tools Installed

Python tools:
- `langchain-cli`
- `langgraph-cli`
- `langsmith-fetch`
- `skypilot[aws]` (CLI: `sky`)
- `aider-chat`
- `open-interpreter`
- `crewai`

Node tools:
- `@anthropic-ai/claude-code`
- `@openai/codex`
- `@google/gemini-cli`
- `openwork`
- `create-agent-chat-app`
- `@modelcontextprotocol/inspector`

Go tools:
- `opencode`

Optional tools (when `INCLUDE_OPTIONAL=1`):
- `gh copilot` extension (if `gh` is installed)
- `fabric` (official installer: `curl -fsSL https://raw.githubusercontent.com/danielmiessler/fabric/main/scripts/installer/install.sh | INSTALL_DIR="$HOME/.local/bin" bash`)

## Notes
- `mise` is the runtime source of truth for Python/Node/Bun.
- pixi and uv are installed via their official installers when missing.
- For JS CLIs, bun installs the latest versions using `@latest`.
- Go tools install into `GOBIN` (defaulted to `~/.local/bin`) so upgrades do not wipe them.
- Fabric setup is non-interactive when `MDE_FABRIC_SETUP=1` (default). It writes a profile env file (default `~/.config/fabric/.env.anthropic`) and symlinks `~/.config/fabric/.env`; set `MDE_FABRIC_OVERWRITE=1` to refresh keys, `MDE_FABRIC_PROFILE` to select `anthropic|openai|gemini|all`, `MDE_FABRIC_ENV_FILE` to override the path, and `MDE_FABRIC_DEFAULT_VENDOR`/`MDE_FABRIC_DEFAULT_MODEL` to seed defaults.
- Run `fabric --setup` manually if you want the interactive wizard.
- The `fabric` wrapper enforces the profile symlink and unsets `OPENAI_API_KEY` when using the `anthropic` profile to avoid provider probe errors.
- Gemini CLI reads `GEMINI_API_KEY` (Keychain `mde-gemini-api-key` or `MDE_OP_GEMINI_API_KEY_REF`).
- `gemini` uses the MDE wrapper to run via `bunx` (isolated deps).
- Wrapper prepends mise shims so extensions that invoke `npx` resolve the managed Node install.
- Wrapper also sets `GITHUB_MCP_PAT` (Keychain `mde-github-mcp-pat` or `mde-github-token`, or `MDE_OP_GITHUB_TOKEN_REF`).
- `.env` secrets auto-load from `~/.config/macos-development-environment/secrets.env` when present (set `MDE_ENV_AUTOLOAD=0` to disable).
- oh-my-zsh auto-exports Keychain secrets when `MDE_AUTOLOAD_SECRETS=1` (default) so CLIs inherit `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `LANGSMITH_API_KEY`, `LANGSMITH_WORKSPACE_ID`, `GITHUB_TOKEN`, and `GITHUB_MCP_PAT`. Keychain values override existing env vars only when `MDE_SECRET_OVERRIDE=1`.
- `mcp-toolbox` is skipped when no `tools.yaml` is present unless `MDE_GEMINI_ENABLE_MCP_TOOLBOX=1` or `--extensions` is passed.
