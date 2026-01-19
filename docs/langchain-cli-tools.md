# LangChain-AI CLI Tool Inventory

This inventory was built by reviewing the LangChain-AI org for CLI entry points
in `pyproject.toml` (`[project.scripts]` / `[tool.poetry.scripts]`) and
`package.json` (`bin`). The list below is the full set of CLI tools discovered
at the time of review, grouped by ecosystem.

## Python CLI Tools

| Command(s) | Package | Repo / Path |
| --- | --- | --- |
| `langchain`, `langchain-cli` | `langchain-cli` | `langchain-ai/langchain` (`libs/cli`) |
| `langchain-profiles` | `langchain-model-profiles` | `langchain-ai/langchain` (`libs/model-profiles`) |
| `langgraph` | `langgraph-cli` | `langchain-ai/langgraph` (`libs/cli`) |
| `langgraph-gen` | `langgraph-gen` | `langchain-ai/langgraph-gen-py` |
| `langgraph-engineer` | `langgraph-engineer` | `langchain-ai/langgraph-engineer` |
| `langsmith-fetch` | `langsmith-fetch` | `langchain-ai/langsmith-fetch` |
| `langsmith-migrator` | `langsmith-data-migration-tool` | `langchain-ai/langsmith-data-migration-tool` |
| `langsmith-mcp-server` | `langsmith-mcp-server` | `langchain-ai/langsmith-mcp-server` |
| `mcpdoc` | `mcpdoc` | `langchain-ai/mcpdoc` |
| `deepagents`, `deepagents-cli` | `deepagents-cli` | `langchain-ai/deepagents` (`libs/deepagents-cli`) |
| `deepacp` | `deepagents-acp` | `langchain-ai/deepagents` (`libs/acp`) |
| `pylon-extract` | `pylon-data-extractor` | `langchain-ai/pylon_data_extractor` |
| `langchain` | `langc` | `langchain-ai/cli` |
| `docs` | `docs-monorepo` | `langchain-ai/docs` |
| `app` | `langchain-plugin` | `langchain-ai/langchain-aiplugin` |
| `langgraph-dev` | `learning-langchain` | `langchain-ai/learning-langchain` |
| `mcp-simple-streamablehttp-stateless` | `mcp-simple-streamablehttp-stateless` | `langchain-ai/langchain-mcp-adapters` (`examples/servers/streamable-http-stateless`) |

## Node CLI Tools

| Command(s) | Package | Repo / Path |
| --- | --- | --- |
| `create-agent-chat-app` | `create-agent-chat-app` | `langchain-ai/create-agent-chat-app` |
| `deepagents` | `deepagents-cli` | `langchain-ai/deepagentsjs` (`libs/cli`) |
| `create-langchain-integration` | `create-langchain-integration` | `langchain-ai/langchainjs` (`libs/create-langchain-integration`) |
| `validate-checkpointer` | `@langchain/langgraph-checkpoint-validation` | `langchain-ai/langgraphjs` (`libs/checkpoint-validation`) |
| `create-langgraph` | `create-langgraph` | `langchain-ai/langgraphjs` and `langchain-ai/langgraphjs-api` |
| `langgraphjs` | `@langchain/langgraph-cli` | `langchain-ai/langgraphjs` and `langchain-ai/langgraphjs-api` |
| `langgraphjs-ui` | `@langchain/langgraph-ui` | `langchain-ai/langgraphjs` and `langchain-ai/langgraphjs-api` |
| `openwork` | `openwork` | `langchain-ai/openwork` |

## Conflicts to Expect

- `langchain` is defined by both `langchain-cli` and `langc`. The last one
  installed will win on your `PATH`.
- `deepagents` exists in both Python (`deepagents-cli`) and Node
  (`deepagents-cli`) toolchains. The winner depends on `PATH` ordering between
  `~/.local/bin` (uv) and `~/.bun/bin`.

## Known Upstream Issues

- `learning-langchain` ships an invalid `project.scripts.langgraph-dev`. The
  installer patches it to `langgraph.cli:dev_command` so the tool can install;
  pass `--config ch9/py/langgraph.json --verbose` manually if needed.
- `docs-monorepo` requires Python >=3.13; the installer uses `python@latest`
  for it. The upstream `pyproject.toml` only lists `packages = ["pipeline"]`,
  so the installer patches it to include `pipeline.*` plus notebook templates
  before installing so the `docs` CLI works.

## Install Script

Use `scripts/install-langchain-cli-tools.sh` to install and upgrade the
inventory in this doc. The script:

- Uses `bun` for Node CLIs (preferred over Node).
- Attempts `pixi` for Python CLIs (preferred), then falls back to `uv` for PyPI
  or git installs.
- Falls back to git installs for Python CLIs that are not published to PyPI.

Maintenance integration:
- When `MDE_UPDATE_AGENT_TOOLS=1` (default), the weekly maintenance job runs
  this installer to keep tools updated.

Options:
- `INCLUDE_INTERNAL=0` to skip internal or example CLIs (default is `1`).
- `PIXI_ENV=langchain-cli-tools` to change the pixi global environment name.
- `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1` is enabled by default to build
  PyO3-based wheels on newer Python versions.
- `UV_TOOL_FORCE=1` to allow uv to overwrite conflicting binaries (for example `langchain`).
- `UV_TOOL_TIMEOUT_SECONDS=600` to cap long installs (used for `docs-monorepo`).
- `DOCS_MONOREPO_SUBMODULES=1` to clone docs submodules (set `0` to skip when
  you only need the `docs` CLI).
- `DOCS_MONOREPO_DEPTH=1` to control clone depth (set `0` for full history).
- `TOOL_PYTHON_VERSION=3.12` to install tools using a stable
  Python runtime when `python@latest` is newer.

Example:

```bash
INCLUDE_INTERNAL=0 scripts/install-langchain-cli-tools.sh
```
