# AI Agent Guide: LangChain + LangSmith (MDE)

This guide describes how AI agents should use the LangChain/LangSmith CLI tools
installed by macos-development-environment for research, debugging, and
automation.

**Overview**
- Treat LangSmith as the source of truth for traces, threads, and evaluations.
- Prefer the CLIs over SDKs for quick investigations and reproducible exports.
- Keep outputs in a workspace directory that can be attached to reports.
- Run the verification script before heavy automation to avoid partial failures.

**Install And Verify**
- Run `scripts/install-langchain-cli-tools.sh` to install or update the toolchain.
- Run `scripts/verify-langchain-tools.sh` to validate tools, wrappers, and auth.
- Use `INCLUDE_INTERNAL=0` to skip internal/example CLIs when speed matters.
- Use `MDE_LANGCHAIN_SMOKE=0` for a faster tool presence check.

**Secrets And Auth**
- Set `LANGSMITH_API_KEY` via Keychain entry `mde-langsmith-api-key`.
- For service keys, add `LANGSMITH_WORKSPACE_ID` or Keychain `mde-langsmith-workspace-id`.
- Override the API host with `LANGSMITH_ENDPOINT` when using non-default hosting.
- Avoid printing secrets; let wrappers load them when possible.

**Core Tools (What To Use)**
- `langsmith-fetch`: export traces, threads, and single items for analysis.
- `langsmith-migrator`: migrate or copy LangSmith data across projects.
- `langsmith-mcp-server`: expose LangSmith data to MCP-based tools.
- `langchain`/`langchain-cli`: bootstrap and manage LangChain projects.
- `langgraph`, `langgraph-dev`, `langgraph-engineer`, `langgraph-gen`: build and run LangGraph workflows.
- `mcpdoc`, `pylon-extract`, `deepagents`, `deepacp`: docs extraction, data extraction, and agent servers.

**Research Workflow (Recommended)**
- Confirm the target project UUID in LangSmith (`langsmith-fetch config set project-uuid <uuid>`).
- Export the newest traces/threads into a dedicated folder for inspection.
- Summarize errors, latency spikes, or tool failures from the exported JSON.
- Reproduce the issue locally with `langgraph-dev` or `langgraph` CLIs.
- Record findings and attach exported data to your final report.

**Problem-Solving Workflow (Recommended)**
- Start with `langsmith-fetch trace <id>` or `thread <id>` when a specific ID is known.
- Use `langsmith-fetch traces ./out --limit 20` to build a baseline sample.
- Verify tool availability with `scripts/verify-langchain-tools.sh` before changes.
- Iterate with small fixes and re-check traces to confirm improvement.

**Command Examples**

```bash
# Set the project once (optional, stored in config)
langsmith-fetch config set project-uuid <uuid>

# Export recent traces/threads to disk
langsmith-fetch traces ./out/traces --limit 25 --format raw
langsmith-fetch threads ./out/threads --limit 25 --format raw

# Fetch a single trace or thread
langsmith-fetch trace <trace-id> --format json
langsmith-fetch thread <thread-id> --format json

# Local LangGraph exploration
langgraph-dev --help
langgraph --help
```

**Gotchas**
- `langchain` is provided by `langc`; it is patched during install to avoid upstream breakages.
- `deepacp` is a server and does not support `--help`; verification uses import checks.
- `docs` is built from a patched `langchain-ai/docs` checkout and rebuilds on each install.
- Many tools require Python runtimes managed by `mise`; keep `mise` healthy.

**Outputs And Storage**
- Prefer directory exports (`./out/traces`, `./out/threads`) over stdout.
- Keep artifacts next to your investigation notes for auditability.
- Rotate or archive old exports to keep working sets small.
- Avoid saving secrets in the output folders.
