# Claude Platform Tool Types -- Definitive Reference

**Date:** 2026-03-20
**Analyst:** research-agent
**Sources:**
- https://platform.claude.com/docs/en/docs/build-with-claude/tool-use
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- https://platform.claude.com/docs/en/agents-and-tools/mcp-connector
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool

---

## Tool Taxonomy

Claude supports two fundamental categories of tools:

### 1. Client Tools (execute on YOUR systems)
- **Custom tools** -- user-defined with JSON Schema input_schema
- **Anthropic-defined client tools** -- text editor, bash, computer use (require your implementation)

### 2. Server Tools (execute on Anthropic's servers)
- **Web search** -- Anthropic executes searches server-side
- **Web fetch** -- Anthropic fetches URLs server-side
- **Code execution** -- runs in Anthropic's sandboxed container
- **Tool search** -- discovers tools from large catalogs on-demand

### 3. Hybrid / Client-Side with Built-in Schema
- **Memory tool** -- client-side file operations, Anthropic provides the schema
- **MCP connector** -- connects to remote MCP servers via Messages API

---

## Tool 1: Custom Tools (User-Defined)

**What it does:** You define tools with name, description, and JSON Schema input_schema. Claude decides when to call them and provides structured input. You execute them and return results.

**How to enable:** Pass `tools` array in Messages API request with `name`, `description`, `input_schema` fields.

**Available in Claude Code:** No -- this is an API construct. Claude Code has its own built-in tools (Read, Write, Edit, Bash, Glob, Grep).

**Key features:**
- `strict: true` option for guaranteed schema conformance (Structured Outputs)
- Tool choice control: `auto`, `any`, `tool` (force specific tool)
- Supports prompt caching on tool definitions
- Stop reason `tool_use` when Claude wants to call a tool

**API type:** `type` is omitted (defaults to custom tool)

**Project benefit:** Foundation for building any custom integration. Our `mde-py` commands could be exposed as custom tools in API-based agents.

---

## Tool 2: Code Execution Tool

**What it does:** Claude runs Bash commands and manipulates files in a secure, sandboxed container on Anthropic's servers. Supports Python, data analysis, visualizations, file processing.

**Type identifier:** `code_execution_20250825`

**How to enable:**
```json
{"type": "code_execution_20250825", "name": "code_execution"}
```

**Available in Claude Code:** NO -- this is API-only. Claude Code uses its own local Bash tool instead.

**Sandbox environment:**
- Python 3.11.12, Linux x86_64
- 5 GiB RAM, 5 GiB disk, 1 CPU
- NO internet access (completely disabled)
- Full isolation from host
- Containers expire after 30 days
- Container reuse across requests via `container` parameter

**Pre-installed libraries:** pandas, numpy, scipy, scikit-learn, matplotlib, seaborn, sympy, pillow, openpyxl, pyarrow, tqdm, ripgrep, sqlite, and many more.

**Sub-tools provided automatically:**
- `bash_code_execution` -- run shell commands
- `text_editor_code_execution` -- view, create, edit files

**Pricing:**
- FREE when used with `web_search_20260209` or `web_fetch_20260209`
- Otherwise: minimum 5 min execution, 1,550 free hours/month/org, then $0.05/hour/container

**Comparison to Bash tool + Python scripts:**

| Aspect | Code Execution (API) | Bash Tool (client) | Claude Code Bash |
|--------|---------------------|--------------------|--------------------|
| Runs where | Anthropic sandbox | Your server | Your local machine |
| Internet | None | Yes | Yes |
| Local files | No | Yes | Yes |
| Install packages | Limited (pip in sandbox) | Full | Full |
| State persistence | Container reuse (30 day expiry) | Session-persistent | Session-persistent |
| Security | Fully sandboxed | You must secure | Sandboxed by CC |
| Best for | Data analysis, math, viz | System automation | Development tasks |

**Programmatic tool calling:** Code execution enables Claude to write code that calls your custom tools programmatically within the container -- an advanced pattern for multi-tool workflows.

---

## Tool 3: Web Search Tool

**What it does:** Claude searches the web in real-time, returns results with automatic citations.

**Type identifiers:**
- `web_search_20260209` (latest, with dynamic filtering via code execution)
- `web_search_20250305` (basic, ZDR-eligible)

**How to enable:**
```json
{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}
```

**Available in Claude Code:** Claude Code has its own WebFetch/WebSearch tools. The API web_search is different.

**Key features:**
- `max_uses` -- limit searches per request
- `allowed_domains` / `blocked_domains` -- domain filtering with wildcard support
- `user_location` -- localize results (city, region, country, timezone)
- Dynamic filtering (20260209): Claude writes code to filter results before context window
- Auto-citations on all responses
- Works with prompt caching and batch API

**Pricing:** $10 per 1,000 searches + standard token costs for search content

**Project benefit:** Could use in API-based research agents to search for tools/libraries before building.

---

## Tool 4: Web Fetch Tool

**What it does:** Retrieves full content from URLs and PDFs. Claude can analyze fetched documents.

**Type identifiers:**
- `web_fetch_20260209` (latest, with dynamic filtering)
- `web_fetch_20250910` (basic, ZDR-eligible)

**How to enable:**
```json
{"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 10}
```

**Available in Claude Code:** Claude Code has its own WebFetch tool (different implementation).

**Key features:**
- `max_uses` -- limit fetches per request
- `allowed_domains` / `blocked_domains` -- domain filtering
- `citations.enabled` -- optional citations (unlike web search where always on)
- `max_content_tokens` -- limit fetched content size
- PDF text extraction automatic
- URL validation: can only fetch URLs from conversation context (security)
- Dynamic filtering (20260209): code execution to filter content pre-context

**Pricing:** FREE -- no additional cost beyond standard token costs

**Security warning:** Data exfiltration risk when processing untrusted input with sensitive data.

**Project benefit:** Full-page content retrieval for research pipeline.

---

## Tool 5: Text Editor Tool

**What it does:** Anthropic-defined tool for viewing and modifying text files. Client-side -- you implement the file operations.

**Type identifiers:**
- `text_editor_20250728` (Claude 4.x) -- tool name: `str_replace_based_edit_tool`
- `text_editor_20250124` (Claude 3.7) -- tool name: `str_replace_editor`

**How to enable:**
```json
{"type": "text_editor_20250728", "name": "str_replace_based_edit_tool", "max_characters": 10000}
```

**Available in Claude Code:** YES -- Claude Code's Edit tool IS essentially this. Claude Code implements the text editor client-side.

**Commands:**
- `view` -- read file/directory contents (optional `view_range` for line ranges)
- `str_replace` -- exact string replacement (must match exactly once)
- `create` -- create new file with content
- `insert` -- insert text at specific line number
- `undo_edit` -- revert last edit (Claude 3.7 only, NOT in Claude 4.x)

**Pricing:** 700 additional input tokens per request

**Project benefit:** Already using this pattern via Claude Code's Edit tool.

---

## Tool 6: Bash Tool

**What it does:** Anthropic-defined tool for executing shell commands in a persistent bash session. Client-side -- you run the commands.

**Type identifier:** `bash_20250124`

**How to enable:**
```json
{"type": "bash_20250124", "name": "bash"}
```

**Available in Claude Code:** YES -- Claude Code's Bash tool IS this.

**Key features:**
- Persistent session (state maintained between commands: env vars, cwd)
- `command` parameter for running commands
- `restart` parameter to restart session
- No interactive commands (no vim, less, password prompts)

**Pricing:** 245 additional input tokens per request

**Security:** You must implement: isolated environments, command filtering, resource limits, logging.

**Project benefit:** Already using this via Claude Code.

---

## Tool 7: Computer Use Tool

**What it does:** Claude interacts with desktop environments via screenshots, mouse clicks, keyboard input, drag operations.

**Type identifiers:**
- `computer_20251124` (Claude 4.5+)
- `computer_20250124` (Claude 3.7-4.x)

**Status:** BETA -- requires beta header `computer-use-2025-11-24`

**How to enable:**
```json
{"type": "computer_20251124", "name": "computer", "display_width_px": 1024, "display_height_px": 768, "display_number": 1}
```

**Available in Claude Code:** Available via MCP plugins (chrome-devtools, claude-in-chrome).

**Key features:**
- Screenshot capture, mouse control (click, drag, move), keyboard input
- Requires you to implement the screenshot/action execution
- NOT ZDR-eligible

**Project benefit:** Could automate GUI testing or browser-based workflows.

---

## Tool 8: Memory Tool

**What it does:** Claude stores and retrieves information across conversations via a file-based memory directory. Client-side -- you implement file storage.

**Type identifier:** `memory_20250818`

**How to enable:**
```json
{"type": "memory_20250818", "name": "memory"}
```

**Available in Claude Code:** Claude Code has its own CLAUDE.md and memory system. The API memory tool is a different pattern.

**Commands:**
- `view` -- list directory or read file (with line numbers)
- `create` -- create new file
- `str_replace` -- replace text in file
- `insert` -- insert text at line
- `delete` -- delete file/directory
- `rename` -- rename/move file

**Key pattern:** Claude automatically checks `/memories` directory before starting tasks. Stores progress, decisions, knowledge for cross-conversation continuity.

**Works with:**
- Context editing (`clear_tool_uses_20250919`) -- clears old tool results while memory persists
- Compaction -- server-side summarization + memory for critical info

**Security considerations:**
- Path traversal protection required (validate all paths under /memories)
- Size limits on memory files
- Memory expiration policies
- Sensitive info filtering

**ZDR eligible:** YES

**Project benefit:** Cross-session agent memory. Our project already uses CLAUDE.md + auto-memory. The API memory tool provides a more structured pattern for API-based agents.

---

## Tool 9: MCP Connector

**What it does:** Connects to remote MCP servers directly from the Messages API without implementing an MCP client.

**Status:** BETA -- requires `anthropic-beta: mcp-client-2025-11-20`

**How to enable:**
```json
{
  "mcp_servers": [{"type": "url", "url": "https://...", "name": "my-mcp", "authorization_token": "..."}],
  "tools": [{"type": "mcp_toolset", "mcp_server_name": "my-mcp"}]
}
```

**Available in Claude Code:** Claude Code has its own MCP integration (`claude mcp add`). The API MCP connector is different -- it removes the need for a client-side MCP SDK.

**Key features:**
- Direct API integration -- no MCP client needed
- Tool configuration: allowlist/denylist specific tools, per-tool configs
- `defer_loading` -- don't load tool description until searched (for tool search)
- OAuth authentication support
- Multiple servers in one request
- Response types: `mcp_tool_use`, `mcp_tool_result`

**Limitations:**
- Only tool calls supported (not MCP prompts/resources/sampling)
- Server must be publicly exposed via HTTP (no STDIO)
- Not available on Bedrock/Vertex

**Project benefit:** If we exposed our mde-py tools as an MCP server, API agents could connect directly without local setup.

---

## Tool 10: Tool Search Tool

**What it does:** Enables Claude to work with hundreds/thousands of tools by dynamically discovering and loading them on-demand. Reduces context bloat by 85%+.

**Type identifier:** Server-side tool for searching tool catalogs

**How to enable:** Works with MCP connector's `defer_loading: true` config

**Key features:**
- Searches tool names, descriptions, argument names/descriptions
- Loads only the 3-5 tools Claude needs per request
- Keeps selection accuracy high even across thousands of tools
- Can also implement custom client-side tool search

**Project benefit:** If we scale to many MCP tools, tool search prevents context bloat.

---

## Tool 11: Files API

**What it does:** Upload and download files for use with code execution and messages.

**Status:** BETA -- requires `anthropic-beta: files-api-2025-04-14`

**How to use:**
- Upload: `POST /v1/files` with form data
- Reference in messages: `{"type": "container_upload", "file_id": "file_abc123"}`
- Download generated files from code execution results

**Available in Claude Code:** Claude Code reads/writes files directly. Files API is for API-based workflows.

**Supported formats:** CSV, Excel, JSON, XML, images (JPEG/PNG/GIF/WebP), text files (.txt, .md, .py, etc.)

**Project benefit:** Could upload data files for API-based analysis agents.

---

## Summary: Claude Code Availability

| Tool | In Claude Code | In API | Notes |
|------|---------------|--------|-------|
| Custom tools | N/A (CC has built-in) | YES | CC uses its own tool system |
| Code execution | NO | YES | CC uses local Bash instead |
| Web search | WebSearch tool (different) | YES | CC version is simpler |
| Web fetch | WebFetch tool (different) | YES | CC version uses AI model |
| Text editor | YES (Edit tool) | YES | Same pattern, CC implements it |
| Bash | YES (Bash tool) | YES | Same pattern, CC implements it |
| Computer use | Via MCP plugins | YES (beta) | Chrome devtools MCP |
| Memory | CLAUDE.md + auto-memory | YES | Different mechanisms |
| MCP connector | `claude mcp add` | YES (beta) | CC does local MCP, API does remote |
| Tool search | ToolSearch (deferred) | YES | CC has built-in deferred loading |
| Files API | Read/Write tools | YES (beta) | CC accesses filesystem directly |

---

## Project-Specific Analysis

### Can we package `uv run mde-py` as code execution tools?

**NO.** The code execution sandbox has no internet, no access to our filesystem, and cannot install our packages. Our `mde-py` toolchain requires:
- Local filesystem access (mise, git, project files)
- Network access (PyPI, GitHub)
- System tools (ruff, ty, pytest)

### Better approach for API-based agents:

1. **Bash tool (client-side):** Expose `uv run mde-py <subcommand>` as a custom tool with the bash tool pattern. The agent calls the tool, you execute locally, return results.
2. **MCP server:** Build an MCP server around mde-py commands. API agents connect via MCP connector; Claude Code connects via `claude mcp add`.
3. **Custom tools:** Define JSON Schema for each mde-py subcommand. Most direct approach for API integration.

### Repetitive tasks that COULD use code execution:

- Data analysis of test results (pure computation)
- CSV/JSON transformation
- Generating charts/visualizations from metrics
- Mathematical calculations
- Code generation/template rendering (no imports from our project)

### Tools we should investigate further:

1. **Memory tool** -- structured alternative to our CLAUDE.md approach
2. **MCP connector** -- expose mde-py as remote MCP for API agents
3. **Tool search** -- scale our tool catalog without context bloat
4. **Programmatic tool calling** -- code execution calling custom tools

---

## Version Reference

| Tool | Current Version | Previous Version |
|------|----------------|-----------------|
| Code execution | `code_execution_20250825` | `code_execution_20250522` (Python only) |
| Web search | `web_search_20260209` | `web_search_20250305` |
| Web fetch | `web_fetch_20260209` | `web_fetch_20250910` |
| Text editor | `text_editor_20250728` | `text_editor_20250429`, `text_editor_20250124` |
| Bash | `bash_20250124` | -- |
| Computer use | `computer_20251124` | `computer_20250124` |
| Memory | `memory_20250818` | -- |
| MCP connector | `mcp-client-2025-11-20` (beta) | `mcp-client-2025-04-04` (deprecated) |
