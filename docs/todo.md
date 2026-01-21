# TODO

This is the consolidated task list.

## MCP
- Prepopulate `configs/mcp-servers.mcp.json` with servers from `langchain-ai/langsmith`, `mcp/microsoft/playwright-mcp`, `mcp/upstash/context7`, `mcp/github/github-mcp-server`, `mcp/hashicorp/terraform-mcp-server`, `mcp/vercel/next-devtools-mcp`, and `mcp/com.vercel/vercel-mcp`.
- Enable MCP for mise (per `mise mcp` docs) and document how it fits with the MCP sync flow.

## Mise
- Review and apply tips from `https://mise.jdx.dev/how-i-use-mise.html`.
- Review and apply directory workflows from `https://mise.jdx.dev/directories.html`.
- Add `mise doctor` to validation (script + docs).
- Add `mise test-tool` coverage to validation (script + docs).

## Tooling
- Install Pitchfork CLI (per `https://pitchfork.jdx.dev/quickstart.html`).
- Install `vercel-labs/agent-browser`.
- Install `vercel-labs/dev3000`.
- Decide on optional AWS/Kubernetes tools beyond the defaults.

## LangChain
- Install LangChain integrations: `langchain-openai`, `langchain-anthropic`, `langchain-aws`, `langchain-mcp-adapters`.


## Observability
- Add OpenLIT Kubernetes manifest/Helm integration when available.
