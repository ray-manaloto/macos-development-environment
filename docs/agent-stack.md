# AI Agent Stack (macOS)

This stack is a superset of LangChain tooling that includes general-purpose
agent CLIs (Claude/Codex/OpenCode/Aider/etc.). It follows the preference
order:

- mise for runtimes (python/node/bun)
- pixi for Python tools (fallback to uv, then pip)
- bun for Node tools

## Install / Update

Use the installer script:

```bash
scripts/install-agent-stack.sh
```

Options:
- `PIXI_ENV=agent-stack` to change the pixi global environment name.
- `INCLUDE_OPTIONAL=0` to skip optional tools like `gh copilot` and `fabric`.

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
- `opencode`
- `openwork`
- `create-agent-chat-app`
- `@modelcontextprotocol/inspector`

Optional tools (when `INCLUDE_OPTIONAL=1`):
- `gh copilot` extension (if `gh` is installed)
- `fabric` (`go install github.com/danielmiessler/fabric@latest`)

## Notes
- `mise` is the runtime source of truth for Python/Node/Bun.
- pixi and uv are installed via their official installers when missing.
- For JS CLIs, bun installs the latest versions using `@latest`.
