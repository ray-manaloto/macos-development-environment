# LangChain + LangSmith Workflow Optimization

This guide explains how the LangChain/LangSmith CLI toolchain can streamline
research, debugging, testing, multi-agent orchestration, and context optimization
in the macOS development environment.

## Why This Toolchain
- LangSmith provides trace, thread, and eval observability for agents.
- LangGraph and DeepAgents provide orchestrated, multi-agent workflows.
- CLI-first workflows keep investigations reproducible and auditable.
- MCP integration makes outputs reusable across tools.

## Tool Index (What To Use)

LangSmith
- `langsmith-fetch`: export traces/threads for analysis and audits.
- `langsmith-migrator`: migrate data between projects.
- `langsmith-mcp-server`: expose LangSmith data to MCP tools.

LangGraph + LangChain
- `langchain` / `langchain-cli`: LangChain project bootstrap and utilities.
- `langchain-profiles`: profile and manage model config presets.
- `langgraph`: core CLI for graph-based agent services.
- `langgraph-dev`: local dev server for LangGraph apps.
- `langgraph-gen`: generate graph scaffolds/templates.
- `langgraph-engineer`: generate graph components and assist planning.

Multi-Agent and Services
- `deepagents` / `deepagents-cli`: multi-agent workflows and orchestration.
- `deepacp`: ACP server (no `--help`; server entrypoint only).
- `mcp-simple-streamablehttp-stateless`: MCP example server.

Docs + Data Extraction
- `mcpdoc`: build or validate MCP-compatible docs.
- `pylon-extract`: structured extraction from data sources.
- `docs`: docs pipeline for LangChain docs repo.

Node (Scaffolding)
- `create-agent-chat-app`: quick agent UI scaffolding.
- `create-langchain-integration`: LangChain integration skeletons.
- `create-langgraph`: LangGraph JS/API scaffolds.
- `langgraphjs`, `langgraphjs-ui`: LangGraph JS tooling.
- `validate-checkpointer`: checkpoint validation.
- `openwork`: worker/task scaffolding.

## Research Workflows

### 1) Trace-First Investigation (Recommended)
- Export recent traces to inspect common errors and latency patterns.
- Save outputs to a dedicated folder for auditability.

```bash
langsmith-fetch traces ./out/traces --limit 25 --format raw
langsmith-fetch threads ./out/threads --limit 25 --format raw
```

### 2) Single-Trace Deep Dive
- Use when you have a specific trace or thread ID.

```bash
langsmith-fetch trace <trace-id> --format json
langsmith-fetch thread <thread-id> --format json
```

### 3) Project Baseline Snapshot
- Set a project UUID for repeatable exports.

```bash
langsmith-fetch config set project-uuid <uuid>
langsmith-fetch traces ./out/traces --limit 50 --format raw
```

## Debugging Workflows

### 1) Reproduce Locally With LangGraph
- Run the dev server, reproduce the issue, compare trace output.

```bash
langgraph-dev --help
langgraph --help
```

### 2) Compare Before/After Traces
- Export traces before and after changes, diff key metrics.
- Keep the outputs under `./out/traces-before` and `./out/traces-after`.

### 3) MCP for Cross-Tool Debugging
- Serve LangSmith data via MCP and re-use across agents or IDEs.

```bash
langsmith-mcp-server
```

## Testing And Validation

### 1) Toolchain Validation
- Validate install + wrappers + LangSmith auth.

```bash
scripts/verify-langchain-tools.sh
```

### 2) Checkpoint Validation
- For LangGraph JS workflows, validate checkpoint state.

```bash
validate-checkpointer --help
```

### 3) Data Extraction Regression Checks
- Run `pylon-extract` on a known corpus and compare output diffs.

## Multi-Agent Orchestration

### 1) Local Multi-Agent Development
- Use `deepagents` for agent orchestration.
- Use `deepacp` when you need an ACP server (stdin/stdout protocol).

### 2) Graph-Based Orchestration
- Use `langgraph` + `langgraph-engineer` for explicit state machines.
- Prefer `langgraph-gen` to bootstrap new graph templates.

### 3) LangGraph JS Tooling
- Use `langgraphjs` + `langgraphjs-ui` for JS-based graphs and UI.

## Context And Token Optimization

### 1) Trace-Based Context Audit
- Review traces for prompt bloat and unused context.
- Identify repeated large inputs and move them to cached retrieval.

### 2) Profile And Preset Models
- Use `langchain-profiles` to standardize model configs per workflow.

### 3) Export, Compress, Summarize
- Export traces to JSON, summarize outside the runtime.
- Keep context windows tight and re-check token usage after changes.

## Additional Optimizations
- Use `langsmith-migrator` to consolidate project data and reduce duplication.
- Use `create-*` scaffolds to standardize new agent projects.
- Use `mcpdoc` and MCP servers to share context across tools consistently.
- Use `scripts/verify-all.sh` for one-shot validation across the stack.

## Guardrails And Gotchas
- `langchain` is provided by `langc`; it is patched during install.
- `deepacp` is a server (import-only checks are used in verification).
- `docs` rebuilds from a patched checkout each install.
- Prefer directory exports over stdout for trace/thread data.

## Recommended Output Conventions
- `./out/traces/` for trace exports.
- `./out/threads/` for thread exports.
- `./out/before/` and `./out/after/` for comparisons.
- Never store secrets in exported JSON or logs.
