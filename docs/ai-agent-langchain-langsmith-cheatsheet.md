# LangChain + LangSmith Agent Cheat Sheet

Quick reference for AI agents using the LangChain/LangSmith CLI toolchain.

## Verify
- `scripts/install-langchain-cli-tools.sh`
- `scripts/verify-langchain-tools.sh`

## Auth
- Personal key: `mde-langsmith-api-key`
- Service key: set `LANGSMITH_WORKSPACE_ID` if required
- Override host: `LANGSMITH_ENDPOINT=https://api.smith.langchain.com`

## LangSmith Fetch
- Set project once:
  - `langsmith-fetch config set project-uuid <uuid>`
- Export recent traces:
  - `langsmith-fetch traces ./out/traces --limit 25 --format raw`
- Export recent threads:
  - `langsmith-fetch threads ./out/threads --limit 25 --format raw`
- Fetch single items:
  - `langsmith-fetch trace <trace-id> --format json`
  - `langsmith-fetch thread <thread-id> --format json`

## LangGraph
- `langgraph --help`
- `langgraph-dev --help`

## Notes
- Prefer directory exports over stdout for audits.
- `deepacp` is a server; verify with import checks, not `--help`.
