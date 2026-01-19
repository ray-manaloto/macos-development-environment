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

## Tools Installed

Python tools:
- `langchain-cli`
- `langgraph-cli`
- `langsmith-fetch`
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
- `fabric` (`go install github.com/danielmiessler/fabric@latest`)

## Notes
- `mise` is the runtime source of truth for Python/Node/Bun.
- pixi and uv are installed via their official installers when missing.
- For JS CLIs, bun installs the latest versions using `@latest`.
- Gemini CLI reads `GEMINI_API_KEY` (Keychain `mde-gemini-api-key` or `MDE_OP_GEMINI_API_KEY_REF`).
- `gemini` uses the MDE wrapper to run via `bunx` (isolated deps).
- Wrapper prepends mise shims so extensions that invoke `npx` resolve the managed Node install.
- Wrapper also sets `GITHUB_MCP_PAT` (Keychain `mde-github-mcp-pat` or `mde-github-token`, or `MDE_OP_GITHUB_TOKEN_REF`).
- `mcp-toolbox` is skipped when no `tools.yaml` is present unless `MDE_GEMINI_ENABLE_MCP_TOOLBOX=1` or `--extensions` is passed.
