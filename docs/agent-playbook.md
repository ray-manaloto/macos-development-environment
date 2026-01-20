# Agent Playbook (LangChain + LangSmith)

This playbook is the shared workflow for AI agents using the LangChain and
LangSmith CLIs in this environment. It focuses on reproducible research,
trace-driven debugging, and consistent artifact capture.

## Preflight
- Install or update tools: `scripts/install-langchain-cli-tools.sh`
- Validate the toolchain: `scripts/verify-langchain-tools.sh`
- Keep outputs in a stable folder (for example `./out/`)

## Research
- Start from real traces and threads instead of assumptions.
- Export a small baseline sample to a folder so it can be attached to reports.

```bash
langsmith-fetch traces ./out/traces --limit 25 --format raw
langsmith-fetch threads ./out/threads --limit 25 --format raw
```

## Debugging
- Use `langsmith-fetch trace <id>` for a deep dive when you have a specific ID.
- Reproduce locally with `langgraph-dev` or `langgraph` and compare traces.
- Keep before/after artifacts to confirm regressions or improvements.

## Testing And QA
- Run the verification script before and after changes.
- Use checkpoint validation for LangGraph JS work (`validate-checkpointer`).
- Compare output diffs from known corpora when using `pylon-extract`.

## Multi-Agent Orchestration
- Use `deepagents` for multi-agent workflows.
- Use `deepacp` when an ACP server is required (stdin/stdout protocol).
- Prefer LangGraph state machines for explicit, auditable orchestration.

## Context And Token Optimization
- Inspect traces for repeated context blocks or unused inputs.
- Use `langchain-profiles` to standardize model choices per workflow.
- Export traces to JSON and summarize outside the runtime.

## MCP Integration
- Expose LangSmith data via MCP for cross-tool reuse:
  - `langsmith-mcp-server`
- Use MCP documents for consistent context boundaries.

## Secrets And Auth
- Store `LANGSMITH_API_KEY` in Keychain (`mde-langsmith-api-key`).
- For service keys, add `LANGSMITH_WORKSPACE_ID` (Keychain: `mde-langsmith-workspace-id`).
- Override API host with `LANGSMITH_ENDPOINT` if using a non-default deployment.

## Output Conventions
- `./out/traces/` and `./out/threads/` for exports.
- `./out/before/` and `./out/after/` for comparisons.
- Never commit secrets or raw keys.

## Related Docs
- Guide: `docs/ai-agent-langchain-langsmith.md`
- Workflow optimization: `docs/langchain-langsmith-workflow-optimization.md`
- Weekly checklist: `docs/langchain-langsmith-weekly-checklist.md`
