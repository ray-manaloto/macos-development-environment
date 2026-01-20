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
| `langchain` | `langc` | `langchain-ai/cli` (git install) |
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

- `learning-langchain` ships a `langgraph-dev` entrypoint that targets
  `langgraph.cli:dev_command`, which no longer exists. The installer patches it
  to `langgraph_cli.cli:cli` so `langgraph-dev --help` works consistently.
- `langc` depends on `typer<0.10`, which is incompatible with newer `click`.
  The installer pins `click<8.2` and removes the `--no-poetry/--with-poetry`
  alias so `langchain --help` works.
- `deepagents-acp` requires Python >=3.14 and launches an ACP server (no `--help`).
  The verifier checks the module import instead of running the server.
- `docs-monorepo` requires Python >=3.13; the installer uses `python@latest`
  for it. The upstream `pyproject.toml` only lists `packages = ["pipeline"]`,
  so the installer patches it to include `pipeline.*` plus notebook templates
  before installing so the `docs` CLI works.
- `docs-monorepo` installs from a patched local checkout each run, so it will
  always rebuild (git clone + patch). To skip or speed it up, set
  `INCLUDE_INTERNAL=0` or `DOCS_MONOREPO_SUBMODULES=0`.

## LangSmith Credentials

- `langsmith-fetch`, `langsmith-migrator`, and `langsmith-mcp-server` require
  `LANGSMITH_API_KEY` (env var or `~/.langsmith-cli/config.yaml` via
  `langsmith-fetch config set api-key`).
- MDE installs wrappers for these CLIs in `~/.local/bin` to load
  `LANGSMITH_API_KEY` from 1Password (`MDE_OP_LANGSMITH_API_KEY_REF`) or
  Keychain (`mde-langsmith-api-key`) when present.
- Optional overrides: `LANGSMITH_ENDPOINT` (defaults to
  `https://api.smith.langchain.com`), `LANGSMITH_PROJECT`, or
  `LANGSMITH_PROJECT_UUID`.
- For service API keys, set `LANGSMITH_WORKSPACE_ID` (or `LANGCHAIN_WORKSPACE_ID`).
  The verifier also checks `MDE_OP_LANGSMITH_WORKSPACE_ID_REF` or Keychain entry
  `mde-langsmith-workspace-id` if present.
- The LangSmith SDK also honors `LANGCHAIN_API_KEY`/`LANGCHAIN_ENDPOINT`,
  but this setup standardizes on `LANGSMITH_*`.

## Install Script

- `langc` is git-only; the installer skips the PyPI lookup to avoid
  confusing resolution errors.

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
## Validation

Run the verification script to confirm installs + wrappers + LangSmith auth:

```bash
scripts/verify-langchain-tools.sh
```

Options:
- `MDE_LANGCHAIN_SMOKE=0` to skip CLI smoke tests.
- `MDE_LANGCHAIN_SMOKE_TIMEOUT=8` to change the per-command timeout (seconds).
- `MDE_LANGCHAIN_SMOKE_STRICT=1` to force smoke checks even without a TTY (useful in CI).
- `MDE_LANGSMITH_PING=0` to skip the LangSmith API key check.
- `LANGSMITH_ENDPOINT` or `LANGSMITH_API_URL` to target a non-default API host.

