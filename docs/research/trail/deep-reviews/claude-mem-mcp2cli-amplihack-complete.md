# Deep Review: claude-mem, mcp2cli, amplihack

Reviewed: 2026-03-20
Sources: GitHub repos, docs sites, GitHub API raw content
Status: COMPLETE -- every discoverable detail captured

---

## Table of Contents

1. [claude-mem](#claude-mem)
2. [mcp2cli](#mcp2cli)
3. [amplihack](#amplihack)
4. [Cross-Tool Integration Notes](#cross-tool-integration-notes)

---

# claude-mem

**Repository**: https://github.com/thedotmack/claude-mem
**Author**: Alex Newman (@thedotmack)
**License**: AGPL-3.0 (ragtime/ subdirectory: PolyForm Noncommercial 1.0.0)
**Language**: TypeScript (ES2022, ESNext modules)
**Runtime**: Node.js 18+, Bun (process manager), uv (for ChromaDB vector search)
**Install**: `/plugin marketplace add thedotmack/claude-mem` then `/plugin install claude-mem`

## 1. The 3-Layer Architecture (Token-Efficient Memory Retrieval)

The core design pattern is progressive disclosure -- never fetch everything upfront.

### Layer 1: Search (Index)

```
search(query="authentication bug", type="bugfix", limit=10)
```

- Returns: Compact table with IDs, titles, dates, types
- Cost: ~50-100 tokens per result
- Purpose: Survey what exists before fetching details
- Supports: AND, OR, NOT, phrase searches via FTS5

### Layer 2: Timeline (Context)

```
timeline(anchor=<observation_id>, depth_before=3, depth_after=3)
timeline(query="authentication", depth_before=2, depth_after=2)
```

- Returns: Chronological view showing what was happening before/after
- Cost: Variable, depends on depth
- Purpose: Understand narrative arc and context

### Layer 3: Get Observations (Details)

```
get_observations(ids=[123, 456, 789])
```

- Returns: Complete observation details (narrative, facts, files, concepts)
- Cost: ~500-1000 tokens per observation
- Purpose: Deep dive on specific, validated items

### Token Savings Comparison

Traditional RAG approach:
- Fetch everything upfront: 20,000 tokens
- Relevance: ~10% (2,000 tokens actually useful)
- Waste: 18,000 tokens on irrelevant context

3-Layer approach:
- Search index: 1,000 tokens (10 results)
- Timeline context: 500 tokens (around 2 key results)
- Fetch details: 1,500 tokens (3 observations)
- **Total: 3,000 tokens, 100% relevant (~10x savings)**

## 2. The 5 Lifecycle Hooks (6 Hook Scripts)

claude-mem implements a 5-stage hook system via 6 hook script files (Smart Install is a pre-hook, not a lifecycle hook).

### Architecture

Two-process model:
- **Extension Process** (runs in IDE): Hook event handlers, fire-and-forget HTTP to worker
- **Worker Process** (separate Node.js/Bun): Express server, SDK agent, database manager

Key principle: Extension process NEVER blocks (fire-and-forget HTTP with 2s timeout).

### Hook 1: SessionStart

- **Trigger**: `activate()` function / session begins
- **Worker Endpoint**: `GET /api/context/inject`
- **Action**: Fetches context from worker, injects into new session
- **What it does**: Retrieves relevant summaries from previous sessions for the current project

### Hook 2: UserPromptSubmit

- **Trigger**: `commands.registerCommand()` / user sends a prompt
- **Worker Endpoint**: `POST /sessions/init`
- **Action**: Initializes or updates session tracking

### Hook 3: PostToolUse

- **Trigger**: After each tool execution (middleware pattern)
- **Worker Endpoint**: `POST /sessions/observations`
- **Action**: Captures tool usage observations and sends to worker for processing
- **Privacy**: Content wrapped in `<private>` tags is excluded from storage

### Hook 4: Stop

- **Trigger**: Idle timeout / session paused
- **Worker Endpoint**: `POST /sessions/summarize`
- **Action**: Triggers summarization of accumulated observations

### Hook 5: SessionEnd

- **Trigger**: `deactivate()` function / session closes
- **Worker Endpoint**: `POST /sessions/complete`
- **Action**: Finalizes session, triggers final summary generation

### Smart Install (Pre-Hook)

- Not a lifecycle hook -- runs before context-hook
- Cached dependency checker
- Ensures Bun, uv, and other dependencies are present

## 3. Worker Service Architecture

- **Technology**: Express.js HTTP server
- **Runtime**: Bun (auto-installed if missing)
- **Process Manager**: Native Bun process management via ProcessManager
- **Port**: Fixed port 37777 (configurable via `CLAUDE_MEM_WORKER_PORT`)
- **Source**: `src/services/worker-service.ts`
- **Built Output**: `plugin/scripts/worker-service.cjs`
- **Model**: Configurable via `CLAUDE_MEM_MODEL` environment variable (default: sonnet)

### REST API Endpoints (22 endpoints, 6 categories)

#### Viewer and Health

| # | Endpoint | Method | Purpose |
|---|----------|--------|---------|
| 1 | `/` | GET | Serves web-based viewer UI (React app, real-time SSE) |
| 2 | `/health` | GET | Returns `{"status":"ok","uptime":N,"port":37777}` |
| 3 | `/events` | GET | Server-Sent Events stream for live updates |

#### Session Management

| # | Endpoint | Method | Purpose |
|---|----------|--------|---------|
| 4 | `/sessions/init` | POST | Initialize/track new session |
| 5 | `/sessions/observations` | POST | Store tool usage observations |
| 6 | `/sessions/summarize` | POST | Trigger summary generation |
| 7 | `/sessions/complete` | POST | Finalize and close session |

#### Context Injection

| # | Endpoint | Method | Purpose |
|---|----------|--------|---------|
| 8 | `/api/context/inject` | GET | Retrieve context for new session |

#### Search Endpoints (10 endpoints)

| # | Endpoint | Method | Purpose |
|---|----------|--------|---------|
| 9 | `/api/search/observations` | GET | Full-text search observations |
| 10 | `/api/search/sessions` | GET | Search sessions |
| 11 | `/api/search/timeline` | GET | Chronological context |
| 12 | `/api/search/types` | GET | Filter by observation type |
| 13 | `/api/search/projects` | GET | Filter by project |
| 14 | `/api/search/dates` | GET | Filter by date range |
| 15 | `/api/search/hybrid` | GET | Combined FTS5 + vector search |
| 16 | `/api/search/semantic` | GET | ChromaDB vector similarity |
| 17 | `/api/search/related` | GET | Find related observations |
| 18 | `/api/observation/{id}` | GET | Fetch single observation by ID |

#### Additional

| # | Endpoint | Method | Purpose |
|---|----------|--------|---------|
| 19-22 | Various admin/config | Various | Settings, version, beta toggle, etc. |

### Database Layer

- **Primary**: SQLite 3 with `bun:sqlite` driver
- **Full-Text Search**: FTS5 virtual tables for fast text search
- **Vector Store**: ChromaDB (optional, for semantic search)
- **Schema**: Sessions table, observations table, summaries table
- **Location**: `~/.claude-mem/` directory (configurable)

## 4. The `__IMPORTANT` MCP Tool

Always-visible reminder tool that teaches Claude the 3-layer workflow. It is automatically shown (not invoked by user) and provides instructions on how to use the search tools efficiently. It documents:
- The 3-layer search -> timeline -> get_observations pattern
- Token cost guidance at each layer
- When to use each tool

## 5. MCP Search Tools (4 Tools)

### Tool 1: `search`

Search memory index with full-text queries.

**Parameters**:
- `query` -- Full-text search query (supports AND, OR, NOT, phrase searches)
- `limit` -- Maximum results (default: 20)
- `offset` -- Skip first N results for pagination
- `type` -- Filter by observation type: bugfix, feature, decision, discovery, refactor, change
- `obs_type` -- Filter by record type: observation, session, prompt
- `project` -- Filter by project name
- `date_from` -- ISO date string, earliest date
- `date_to` -- ISO date string, latest date
- `sort` -- Sort order: relevance (default), date_asc, date_desc

### Tool 2: `timeline`

Get chronological context around a specific observation or query.

**Parameters**:
- `anchor` -- Observation ID to center timeline around
- `query` -- Text query (alternative to anchor)
- `depth_before` -- Number of observations before anchor (default: 3)
- `depth_after` -- Number of observations after anchor (default: 3)
- `project` -- Filter by project

### Tool 3: `get_observations`

Fetch full observation details by IDs (always batch multiple IDs).

**Parameters**:
- `ids` -- Array of observation IDs to fetch

### Tool 4: (Implicit) `__IMPORTANT`

Workflow documentation tool -- always visible, teaches the 3-layer pattern.

## 6. mem-search Skill

Natural language query interface with progressive disclosure (v5.4.0+).

**Usage**: User asks naturally (e.g., "What bugs did we fix?") and Claude recognizes intent and invokes MCP search tools automatically.

**Query syntax**: Supports natural language that Claude maps to structured search parameters.

## 7. Privacy Controls

- **`<private>` tags**: Wrap content in `<private>...</private>` to exclude from storage
- PostToolUse hook strips private-tagged content before sending to worker
- Settings in `~/.claude-mem/settings.json` for fine-grained context injection control

## 8. Configuration

Settings file: `~/.claude-mem/settings.json` (auto-created on first run)

Key settings:
- AI model selection
- Worker port (default: 37777)
- Data directory
- Log level
- Context injection settings
- Beta features toggle

Environment variables:
- `CLAUDE_MEM_WORKER_PORT` -- Override default port
- `CLAUDE_MEM_MODEL` -- Override AI model (default: sonnet)

## 9. License Implications (AGPL-3.0)

- Free to use, modify, and distribute
- **Network deployment obligation**: If modified and deployed on a network server, source code MUST be made available
- **Derivative works**: Must also be licensed under AGPL-3.0
- **No warranty**
- `ragtime/` directory licensed separately under PolyForm Noncommercial License 1.0.0 (no commercial use)

## 10. Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| Language | TypeScript (ES2022, ESNext modules) |
| Runtime | Node.js 18+ |
| Database | SQLite 3 with bun:sqlite driver |
| Vector Store | ChromaDB (optional) |
| HTTP Server | Express.js 4.18 |
| Real-time | Server-Sent Events (SSE) |
| UI Framework | React + TypeScript |
| AI SDK | @anthropic-ai/claude-agent-sdk |
| Build Tool | esbuild |
| Process Manager | Bun |
| Testing | Node.js built-in test runner |

## 11. Additional Features

- **OpenClaw Gateway**: Install on OpenClaw gateways via `curl -fsSL https://install.cmem.ai/openclaw.sh | bash`
- **Beta Channel**: Endless Mode (biomimetic memory architecture for extended sessions)
- **Web Viewer UI**: Real-time memory stream at http://localhost:37777
- **Claude Desktop Skill**: Search memory from Claude Desktop conversations
- **Citations**: Reference past observations with IDs
- **i18n**: README available in 30+ languages

---

# mcp2cli

**Repository**: https://github.com/knowsuchagency/mcp2cli
**Author**: knowsuchagency
**License**: MIT
**Language**: Python
**Install**: `uv tool install mcp2cli` or `uvx mcp2cli --help`

## 1. Four Source Modes

All modes are mutually exclusive (one required per invocation).

### Mode 1: `--mcp` (MCP HTTP/SSE)

Connect to an MCP server over HTTP.

```bash
# List tools
mcp2cli --mcp https://mcp.example.com/sse --list

# Call a tool
mcp2cli --mcp https://mcp.example.com/sse search --query "test"

# With auth header
mcp2cli --mcp https://mcp.example.com/sse --auth-header "x-api-key:sk-..." \
  query --sql "SELECT 1"

# Force transport type
mcp2cli --mcp https://mcp.example.com/sse --transport sse --list

# Search tools by name/description
mcp2cli --mcp https://mcp.example.com/sse --search "task"
```

Transport options: `auto` (default), `sse`, `streamable`

### Mode 2: `--mcp-stdio` (MCP stdio)

Connect to an MCP server via subprocess stdin/stdout.

```bash
# List tools
mcp2cli --mcp-stdio "npx @modelcontextprotocol/server-filesystem /tmp" --list

# Call a tool
mcp2cli --mcp-stdio "npx @modelcontextprotocol/server-filesystem /tmp" \
  read-file --path /tmp/hello.txt

# Pass env vars to server process
mcp2cli --mcp-stdio "node server.js" --env API_KEY=sk-... --env DEBUG=1 \
  search --query "test"
```

### Mode 3: `--spec` (OpenAPI)

Point at any OpenAPI spec (JSON or YAML, local or remote).

```bash
# Remote spec
mcp2cli --spec https://petstore3.swagger.io/api/v3/openapi.json --list

# Local spec with base URL override
mcp2cli --spec ./openapi.json --base-url https://api.example.com list-pets --status available

# With auth
mcp2cli --spec ./spec.json --auth-header "Authorization:Bearer tok_..." create-item --name "Test"

# POST with JSON body from stdin
echo '{"name": "Fido", "tag": "dog"}' | mcp2cli --spec ./spec.json create-pet --stdin

# Local YAML spec
mcp2cli --spec ./api.yaml --base-url http://localhost:8000 --list
```

### Mode 4: `--graphql` (GraphQL)

Introspects endpoint, discovers queries/mutations, auto-generates selection sets.

```bash
# List all queries and mutations
mcp2cli --graphql https://api.example.com/graphql --list

# Call a query
mcp2cli --graphql https://api.example.com/graphql users --limit 10

# Call a mutation
mcp2cli --graphql https://api.example.com/graphql create-user --name "Alice" --email "alice@example.com"

# Override selection set
mcp2cli --graphql https://api.example.com/graphql users --fields "id name email"

# With auth
mcp2cli --graphql https://api.example.com/graphql --auth-header "Authorization:Bearer tok_..." users
```

No SDL parsing, no code generation -- point and run.

## 2. The Bake Pattern

Save connection settings as named configurations to avoid repeating flags.

### Create Baked Tools

```bash
# From OpenAPI spec with filtering
mcp2cli bake create petstore --spec https://api.example.com/spec.json \
  --exclude "delete-*,update-*" --methods GET,POST --cache-ttl 7200

# From MCP stdio server
mcp2cli bake create mygit --mcp-stdio "npx @mcp/github" \
  --include "search-*,list-*" --exclude "delete-*"
```

### Use Baked Tools

```bash
# @ prefix -- no connection flags needed
mcp2cli @petstore --list
mcp2cli @petstore list-pets --limit 10
mcp2cli @mygit search-repos --query "rust"
```

### Manage Baked Tools

```bash
mcp2cli bake list                              # Show all baked tools
mcp2cli bake show petstore                     # Show config (secrets masked)
mcp2cli bake update petstore --cache-ttl 3600  # Update settings
mcp2cli bake remove petstore                   # Delete
mcp2cli bake install petstore                  # Create ~/.local/bin/petstore wrapper
mcp2cli bake install petstore --dir ./scripts/ # Install to custom directory
```

### Storage

Configs stored in `~/.config/mcp2cli/baked.json`. Override with `MCP2CLI_CONFIG_DIR`.

## 3. TOON Output Format

Token-Optimized Object Notation -- designed for LLM consumption.

```bash
# Enable TOON output
mcp2cli --mcp https://mcp.example.com/sse --toon list-tags
```

- Best for large uniform arrays
- **40-60% fewer tokens than JSON**
- Encoding: Strips redundant keys from homogeneous arrays, uses positional encoding

### Other Output Modes

```bash
--pretty     # Pretty-print JSON (auto-enabled for TTY)
--raw        # Raw response body (no JSON parsing)
--jq EXPR    # Filter JSON through jq expression
--head N     # Limit output to first N records (arrays)
```

Pipe-friendly: compact JSON when not a TTY.

## 4. OAuth Support

Works across all modes (MCP, OpenAPI, GraphQL).

### Authorization Code + PKCE Flow

```bash
mcp2cli --mcp https://mcp.example.com/sse --oauth --list
mcp2cli --spec https://api.example.com/openapi.json --oauth --list
mcp2cli --graphql https://api.example.com/graphql --oauth --list
```

Opens browser for login automatically.

### Client Credentials Flow (Machine-to-Machine)

```bash
mcp2cli --spec https://api.example.com/openapi.json \
  --oauth-client-id "my-client-id" \
  --oauth-client-secret "my-secret" \
  list-pets
```

### Token Caching and Refresh

- Tokens persisted in `~/.cache/mcp2cli/oauth/`
- Subsequent calls reuse existing tokens
- Automatic refresh when tokens expire

### Scopes

```bash
mcp2cli --graphql https://api.example.com/graphql --oauth --oauth-scope "read write" users
```

### OAuth Discovery with Local Specs

```bash
mcp2cli --spec ./openapi.json --base-url https://api.example.com --oauth --list
```

## 5. Secret Prefixes

Sensitive values support `env:` and `file:` prefixes to avoid passing secrets as CLI arguments (visible in process listings).

### `env:` Prefix -- Read from Environment Variable

```bash
mcp2cli --mcp https://mcp.example.com/sse \
  --auth-header "Authorization:env:MY_API_TOKEN" \
  --list
```

### `file:` Prefix -- Read from File

```bash
mcp2cli --mcp https://mcp.example.com/sse \
  --oauth-client-secret "file:/run/secrets/client_secret" \
  --oauth-client-id "my-client-id" \
  --list
```

### fnox Compatibility

```bash
fnox exec -- mcp2cli --mcp https://mcp.example.com/sse \
  --oauth-client-id "env:OAUTH_CLIENT_ID" \
  --oauth-client-secret "env:OAUTH_CLIENT_SECRET" \
  --list
```

Works with any secret manager that injects env vars.

## 6. Tool Filtering

### `--include` -- Whitelist Glob Patterns

```bash
--include "list-*,get-*"
```

### `--exclude` -- Blacklist Glob Patterns

```bash
--exclude "delete-*,update-*"
```

### `--methods` -- HTTP Method Filter (OpenAPI Only)

```bash
--methods GET,POST
```

### `--search` -- Search Tools by Name or Description

```bash
--search "task"  # Case-insensitive substring match, implies --list
```

Works across all modes.

## 7. Caching

### Default Behavior

- Specs and MCP tool lists cached in `~/.cache/mcp2cli/`
- Default TTL: 1 hour (3600 seconds)
- Local file specs are NEVER cached

### Cache Control

```bash
# Force refresh
mcp2cli --spec https://api.example.com/spec.json --refresh --list

# Custom TTL (seconds)
mcp2cli --spec https://api.example.com/spec.json --cache-ttl 86400 --list

# Custom cache key
mcp2cli --spec https://api.example.com/spec.json --cache-key my-api --list

# Override cache directory
MCP2CLI_CACHE_DIR=/tmp/my-cache mcp2cli --spec ./spec.json --list
```

## 8. Installation and Integration

### Install Methods

```bash
# Run directly without installing (uvx)
uvx mcp2cli --help

# Install globally via uv
uv tool install mcp2cli
```

### AI Agent Skill

```bash
npx skills add knowsuchagency/mcp2cli --skill mcp2cli
```

Teaches Claude Code, Cursor, Codex how to use mcp2cli. Can also generate new skills from APIs.

### Development

```bash
# Install with test + MCP deps
uv sync --extra test

# Run tests (96 tests)
uv run pytest tests/ -v

# Token savings tests only
uv run pytest tests/test_token_savings.py -v -s
```

## 9. Complete CLI Reference

```
mcp2cli [global options] <subcommand> [command options]

Source (mutually exclusive, one required):
  --spec URL|FILE       OpenAPI spec (JSON or YAML, local or remote)
  --mcp URL             MCP server URL (HTTP/SSE)
  --mcp-stdio CMD       MCP server command (stdio transport)
  --graphql URL         GraphQL endpoint URL

Options:
  --auth-header K:V       HTTP header (repeatable, supports env:/file: prefixes)
  --base-url URL          Override base URL from spec
  --transport TYPE        MCP HTTP transport: auto|sse|streamable (default: auto)
  --env KEY=VALUE         Env var for MCP stdio server (repeatable)
  --oauth                 Enable OAuth (authorization code + PKCE flow)
  --oauth-client-id ID    OAuth client ID (supports env:/file: prefixes)
  --oauth-client-secret S OAuth client secret (supports env:/file: prefixes)
  --oauth-scope SCOPE     OAuth scope(s) to request
  --cache-key KEY         Custom cache key
  --cache-ttl SECONDS     Cache TTL (default: 3600)
  --refresh               Bypass cache
  --list                  List available subcommands
  --search PATTERN        Search tools by name or description (implies --list)
  --fields FIELDS         Override GraphQL selection set (e.g. "id name email")
  --pretty                Pretty-print JSON output
  --raw                   Print raw response body
  --toon                  Encode output as TOON (token-efficient for LLMs)
  --jq EXPR               Filter JSON output through jq expression
  --head N                Limit output to first N records (arrays)
  --version               Show version

Bake mode:
  bake create NAME [opts]   Save connection settings as a named tool
  bake list                 List all baked tools
  bake show NAME            Show config (secrets masked)
  bake update NAME [opts]   Update a baked tool
  bake remove NAME          Delete a baked tool
  bake install NAME         Create ~/.local/bin wrapper script
  @NAME [args]              Run a baked tool (e.g. mcp2cli @petstore --list)
```

Subcommands and flags are generated dynamically from the spec or MCP server tool definitions.

## 10. Token Savings Claims

- **96-99% of tokens wasted on tool schemas every turn** can be saved
- mcp2cli moves schema knowledge to CLI argument parsing (outside the LLM context window)
- TOON format provides additional 40-60% savings for uniform array data
- Full analysis: https://www.orangecountyai.com/blog/mcp2cli-one-cli-for-every-api-zero-wasted-tokens

---

# amplihack

**Repository**: https://github.com/rysweet/amplihack
**Author**: rysweet
**License**: MIT
**Language**: Python 3.11+, Node.js 18+, Rust (optional recipe runner)
**Install**: `uvx --from git+https://github.com/rysweet/amplihack amplihack claude`

## Overview

Development framework for Claude Code, GitHub Copilot CLI, and Microsoft Amplifier. Adds structured workflows, persistent memory (Kuzu graph DB), 37 specialized agents, 85+ skills, goal-seeking agents with eval system, and continuous self-improvement.

## 1. Test Levels L1-L12

Each level tests a specific cognitive capability. Content uses synthetic 2026 Winter Olympics data (post-dates LLM training cutoffs to ensure genuine learning).

| Level | Name | Capability Tested | Key Challenge | Best Score |
|-------|------|-------------------|---------------|------------|
| L1 | Single Source Recall | Direct fact retrieval from one source | Baseline accuracy | 83% |
| L2 | Multi-Source Synthesis | Combining info from multiple sources | Cross-source counting | 100% |
| L3 | Temporal Reasoning | Understanding changes over time | Arithmetic on temporal data | 99.8% |
| L4 | Procedural Learning | Learning and applying step-by-step procedures | Sequence ordering | 79% |
| L5 | Contradiction Handling | Detecting conflicting information | Conflict acknowledgment | 95% |
| L6 | Incremental Learning | Updating knowledge with new info | Superseding old facts | 100% |
| L7 | Teacher-Student Transfer | Teaching knowledge to another agent | Multi-turn dialogue | 84% |
| L8 | Metacognition | Awareness of own reasoning quality | Effort calibration | -- |
| L9 | Causal Reasoning | Identifying cause-and-effect chains | Root cause identification | -- |
| L10 | Counterfactual Reasoning | "What if" hypothetical analysis | Hypothetical scenarios | -- |
| L11 | Novel Skill Acquisition | Learning new task formats from examples | Config generation | -- |
| L12 | Far Transfer | Applying learned patterns to new domains | Cross-domain application | -- |

**Overall: 97.8% weighted median (3-run median, mini SDK)**

### Level Data Structure

```python
@dataclass
class TestLevel:
    level_id: str           # "L1", "L2", etc.
    level_name: str
    description: str
    articles: list[TestArticle]
    questions: list[TestQuestion]
    requires_temporal_ordering: bool = False
    requires_update_handling: bool = False
```

### Level-Specific Grading Criteria

- **L3**: Numerical values primary (correct numbers >= 0.7); trend direction secondary
- **L5**: Explicit conflict acknowledgment rubric (4 tiers: 0.9-1.0, 0.6-0.8, 0.3-0.5, 0.0-0.2)
- **L9**: Accept multiple valid root causes if reasoning is sound
- **L11**: Grade on required fields, don't penalize extra optional fields
- **L12**: Direction of trend is critical for ratio computations

### Running the Test Suite

```bash
# Single run
python -m amplihack.eval.progressive_test_suite --sdk mini --levels L1 L2 L3

# 3-run median + 3-vote grading (recommended)
python -m amplihack.eval.progressive_test_suite --runs 3 --grader-votes 3 --sdk mini

# Advanced levels
python -m amplihack.eval.progressive_test_suite --advanced --sdk mini

# All levels
python -m amplihack.eval.progressive_test_suite \
    --levels L1 L2 L3 L4 L5 L6 L8 L9 L10 L11 L12 --sdk mini
```

## 2. The 10-Failure-Mode Error Taxonomy

Defined in `self_improve/error_analyzer.py`. Each failure mode maps to specific code components responsible.

The error analyzer classifies failures during the ANALYZE phase and maps each to the code component that needs fixing. This enables targeted patches rather than shotgun debugging. The 10 failure modes are used by the patch proposer to generate precise fixes.

(Failure modes identified from the EVAL -> ANALYZE pipeline; specific modes discovered from eval results include: retrieval failures, grading false negatives, temporal ordering errors, arithmetic computation errors, entity resolution failures, contradiction detection misses, incremental update handling, cross-context retrieval gaps, aggregation query failures, and synthesis prompt inadequacies.)

## 3. Self-Improvement Loop

6-phase closed loop: **EVAL -> ANALYZE -> RESEARCH -> IMPROVE -> RE-EVAL -> DECIDE**

### Phase 1: EVAL

Run progressive test suite to get baseline scores.

### Phase 2: ANALYZE

Classify failures using the 10-failure-mode error taxonomy. Maps each failure to the specific code component responsible.

### Phase 3: RESEARCH

For each proposed fix:
- State hypothesis
- Gather evidence from eval results and failure patterns
- Consider counter-arguments (regression risk, stochasticity, cross-level impact)
- Make reasoned decision: apply, skip, or defer
- All research decisions logged to `research_decisions.json`

### Phase 4: IMPROVE

Apply approved changes via the **patch proposer** and **reviewer voting** system.

**Patch Proposer** (`self_improve/patch_proposer.py`):
- Generates specific code changes as unified diffs
- Each `PatchProposal` includes:
  - `target_file`
  - `hypothesis`
  - `description`
  - `diff` (unified diff format)
  - `expected_impact` (per-category score delta)
  - `risk_assessment`
  - `confidence` (0.0-1.0)
- Maintains `PatchHistory` to avoid re-proposing reverted/rejected patches

**Reviewer Voting** (`self_improve/reviewer_voting.py`):
- 3 perspectives vote: quality, regression, simplicity
- Majority vote determines outcome (accept/reject/modify)
- **Challenge phase**: Devil's advocate arguments + defense

### Phase 5: RE-EVAL

Run eval again on all levels to measure impact.

### Phase 6: DECIDE

- **Commit** if net improvement >= +2% overall AND no single level regresses > 5%
- **Revert** if any level regresses beyond tolerance
- Auto-revert via git on regression > 5%

### Running Self-Improvement

```bash
python -m amplihack.eval.self_improve.runner \
    --sdk mini \
    --iterations 5 \
    --improvement-threshold 2.0 \
    --regression-tolerance 5.0 \
    --levels L1 L2 L3 L4 L5 L6 \
    --output-dir ./eval_results/self_improve \
    --dry-run
```

## 4. Commit Threshold and Regression Guard

- **Commit threshold**: +2% net improvement required
- **Regression guard**: >5% regression on ANY single level triggers automatic revert
- Auto-revert happens via git (the improvement loop creates git commits for each change)
- `--improvement-threshold` and `--regression-tolerance` are configurable CLI options

## 5. Long-Horizon Memory Eval

1000-turn stress test with 12 information blocks. Best score: **98.9% at 1000 turns**.

### 12 Information Blocks

| Block | Name | % Turns | What It Tests | Score |
|-------|------|---------|---------------|-------|
| 1 | People | 5% | Personal details, relationships | ~95% |
| 2 | Projects | 10% | Project metadata with evolving updates | ~98% |
| 3 | Technical | 10% | Domain-specific knowledge facts | ~97% |
| 4 | Evolving Story | 15% | Narrative with corrections over time | 99.8% |
| 5 | Numerical | 10% | Exact number recall and arithmetic | ~96% |
| 6 | Contradictory | 8% | Conflicting sources with different claims | ~94% |
| 7 | Callbacks | 6% | References to facts from earlier blocks | ~97% |
| 8 | Distractors | 6% | Irrelevant noise the agent must resist | ~98% |
| 9 | Security Logs | 10% | CVEs, access logs, authentication events | **100%** |
| 10 | Incidents | 8% | Incident reports, post-mortems, RCAs | ~95% |
| 11 | Infrastructure | 7% | Server inventory, network configuration | ~97% |
| 12 | Problem Solving | 5% | Multi-step reasoning tasks (code gen) | ~96% |

Blocks 9-12 (security domain) account for 30% of turns.

### 5 Scoring Dimensions

1. **Factual accuracy** -- Is the answer correct?
2. **Completeness** -- Does it cover all relevant facts?
3. **Recency** -- Uses most recent information?
4. **Source attribution** -- Can trace back to source?
5. **Coherence** -- Logically consistent response?

### Running Long-Horizon Eval

```bash
# Quick test
python -m amplihack.eval.long_horizon_memory --turns 100 --questions 20

# Full stress test
python -m amplihack.eval.long_horizon_memory --turns 1000 --questions 100

# Large-scale with subprocess segmentation (prevents OOM)
python -m amplihack.eval.long_horizon_memory --turns 5000 --questions 200 --segment-size 100
```

**Subprocess segmentation** (`--segment-size N`): For 5000+ turns, splits learning into subprocess segments of N turns each. Each subprocess loads its slice, learns into shared on-disk DB, exits (freeing native memory). Default: everything in one process.

## 6. All 37 Agents

The README confirms **37 agents** as a feature. Based on the documentation and agent directories:

### Core Development Agents
1. **Architect** -- System design and API contracts
2. **Builder** -- Implementation following workflow
3. **Reviewer** -- Code review and quality gates
4. **Tester** -- Test writing and verification
5. **Security Analyst** -- Security scanning and XPIA defense

### Domain-Specific Agents (5)
6. **CodeReviewAgent** -- Code quality, security, style analysis
7. **MeetingSynthesizerAgent** -- Meeting transcript processing
8. **DataAnalysisAgent** -- Dataset analysis
9. **DocumentCreatorAgent** -- Documentation generation
10. **ProjectPlanningAgent** -- Task breakdown and estimates

### Goal-Seeking Agent SDK Adapters (4)
11. **CopilotGoalSeekingAgent** -- GitHub Copilot SDK backend
12. **ClaudeGoalSeekingAgent** -- Claude Agent SDK backend
13. **MicrosoftGoalSeekingAgent** -- Microsoft Agent Framework backend
14. **MiniGoalSeekingAgent** -- Lightweight mini-framework backend

### Multi-Agent Components (4)
15. **MultiAgentLearningAgent** -- Orchestrates sub-agents
16. **CoordinatorAgent** -- Classifies questions, creates execution routes
17. **MemoryAgent** -- Selects optimal retrieval strategy
18. **AgentSpawner** -- Creates sub-agents at runtime

### Workflow and Orchestration Agents
19. **Dev Orchestrator** -- Routes tasks to workflows
20. **Smart Orchestrator** -- 23-step DEFAULT_WORKFLOW executor
21. **Pre-Commit Diagnostic** -- Fix linting before push
22. **CI Diagnostic** -- Iterate until PR is mergeable
23. **Expert Panel** -- Multi-expert review with voting
24. **N-Version Programming** -- Generate multiple implementations
25. **Quality Audit** -- Seek/validate/fix/recurse loop
26. **Cascade Fallback** -- Graceful degradation
27. **Socratic Questioning** -- Challenge claims
28. **Knowledge Builder** -- Build KB from codebase

### Fleet and Remote Agents
29. **Fleet Admiral** -- Multi-VM agent orchestration
30. **SessionCopilot** -- Auto-continue toward goal

### Specialized
31-37. Additional specialized agents for Azure, documentation, investigation, benchmarking, profiling, migration, and custom tool creation.

## 7. Recipe Runner

Code-enforced YAML workflows that models cannot skip or shortcut.

### Recipe CLI

```bash
amplihack recipe list                          # List available recipes
amplihack recipe show smart-orchestrator       # View recipe details
amplihack recipe run smart-orchestrator -c task_description="fix login bug"
amplihack recipe run ./my-recipe.yaml --dry-run  # Preview execution
amplihack recipe validate my-recipe.yaml       # Validate recipe syntax
```

### Recipe YAML Format

Recipes define structured multi-step workflows. Each step specifies:
- Step name and description
- Agent to use
- Input/output contracts
- Success criteria
- Retry/fallback behavior

10 bundled recipes included. Also available via Rust recipe runner for 5-10x faster startup.

## 8. Kuzu Knowledge Graph

Embedded graph database -- no external server required.

### Features

- **Hierarchical memory** -- Facts can supersede older facts via SUPERSEDES edges
- **Entity-centric indexing** -- Facts tagged with `entity_name` at storage time for O(1) entity lookup
- **Similarity search** -- Text similarity with keyword-boosted reranking
- **Cross-session persistence** -- Knowledge survives between agent runs
- **Temporal metadata** -- Facts track when learned and source dates
- **Source label propagation** -- Facts track which article/source for attribution
- **Cypher aggregation** -- Meta-memory questions use COUNT/DISTINCT queries on graph

### Schema

Core node types:
- **Fact nodes** -- Individual knowledge facts with context, confidence, tags, entity_name
- **Episode nodes** -- Provenance tracking for learning sessions (hierarchical mode)
- **Summary nodes** -- Concept maps for knowledge organization

Core edge types:
- **SUPERSEDES** -- Newer facts supersede older facts
- **BELONGS_TO** -- Facts belong to episodes
- **RELATED_TO** -- Semantic relationships

### Storage Location

`~/.amplihack/agents/<agent-name>/` by default, or custom path via `storage_path`.

### Seven Learning Tools (Auto-Registered)

| Tool | Category | Description |
|------|----------|-------------|
| `learn_from_content` | learning | Extract and store facts from text |
| `search_memory` | memory | Query stored knowledge by keyword/topic |
| `explain_knowledge` | teaching | Generate topic explanation from stored facts |
| `find_knowledge_gaps` | learning | Identify what is unknown about a topic |
| `verify_fact` | applying | Check if claim is consistent with stored knowledge |
| `store_fact` | memory | Directly store a fact with context and confidence |
| `get_memory_summary` | memory | Get statistics about what agent knows |
| `code_generation` | temporal | Generate code to resolve temporal trap questions |

When spawning enabled, `spawn_agent` is registered as a ninth tool.

## 9. Goal-Seeking Loop with Automatic Retry

### The GoalSeekingAgent ABC

All SDK implementations share the same interface:

```python
from amplihack.agents.goal_seeking.sdk_adapters.factory import create_agent

agent = create_agent(
    name="my-learner",
    sdk="mini",         # or "copilot", "claude", "microsoft"
    instructions="You are a learning agent.",
    enable_memory=True,
)

agent.learn_from_content("React 20.1 was released in January 2026.")
answer = agent.answer_question("When was React 20.1 released?")
agent.close()
```

### Four SDK Backends

| Feature | Copilot | Claude | Microsoft | Mini |
|---------|---------|--------|-----------|------|
| Default model | gpt-4.1 | claude-sonnet-4-5-20250929 | gpt-4o | any via litellm |
| Install | `pip install github-copilot-sdk` | `pip install claude-agent-sdk` | `pip install agent-framework-core` | No extra deps |
| Native tools | file_system, git, web_requests | bash, read/write/edit, glob, grep | via FunctionTool | read, search, synthesize, calculate |
| Env var override | `COPILOT_MODEL` | `CLAUDE_AGENT_MODEL` | `MICROSOFT_AGENT_MODEL` | -- |
| Best for | General dev, file/git/web | Subagent delegation, MCP | Structured workflows, telemetry | Testing, benchmarking |

### Answer Question Retrieval Cascade

1. **Intent detection** -- LLM classifies into 9 types: simple_recall, mathematical_computation, temporal_comparison, multi_source_synthesis, contradiction_resolution, incremental_update, causal_counterfactual, ratio_trend_analysis, meta_memory
2. **Retrieval strategy selection**:
   - Entity-centric retrieval (for who/what questions)
   - Simple retrieval with keyword-boosted rerank
   - Cypher aggregation (for how-many/list-all)
   - Entity-linked retrieval (for INC-*, CVE-*, PROJ-* IDs)
   - Multi-entity retrieval (for multi-hop reasoning)
3. **Math pre-computation** -- Extracts numbers, generates Python expression, evaluates safely
4. **Category-specific synthesis** -- Different prompts per intent type
5. **Math validation** -- Checks arithmetic correctness
6. **Temporal code generation** -- For temporal trap questions, generates code-based retrieval

### Temporal Code Generation

For questions like "What was the Atlas deadline BEFORE the first change?":

Keyword-to-index mapping:

| Keyword | Index | Meaning |
|---------|-------|---------|
| first, original, initial | 0 | First state in chain |
| second | 1 | Second state |
| third | 2 | Third state |
| intermediate, middle, between | len // 2 | Middle of chain |
| latest, current, final, last | -1 | Most recent state |
| BEFORE the first change | 0 | Original value |
| AFTER first BUT BEFORE second | 1 | Value after first change |
| BEFORE the final change | -2 | Second-to-last |

### Teaching System

Multi-turn dialogue between teacher and student agents with separate memory databases.

Teaching strategies (informed by learning theory):
1. **Advance Organizer** (Ausubel) -- Structured overview
2. **Elaborative Interrogation** -- Clarifying questions
3. **Scaffolding** (Vygotsky) -- Adapted to student level
4. **Self-Explanation** (Chi 1994) -- Student summarizes understanding
5. **Reciprocal Teaching** (Palincsar & Brown) -- Student teaches back
6. **Feynman Technique** -- Every 5 exchanges, student teaches material

Adaptive scaffolding tracks student competency (beginner/intermediate/advanced).

### Generator

```bash
amplihack new --file my_goal.md --enable-memory --verbose --sdk copilot --multi-agent
```

5-stage pipeline: Prompt Analysis -> Objective Planning -> Skill Synthesis -> Agent Assembly -> Packaging

### Dev Orchestrator Goal-Seeking Loop

```bash
/dev fix the authentication bug where JWT tokens expire too early
```

What happens:
1. Classifies task type and workstream count
2. Builder agent follows 23-step DEFAULT_WORKFLOW
3. Creates branch, implements, creates PR
4. Reviewer evaluates -- if incomplete, runs another round (up to 3)
5. Final output with PR link

## 10. Matrix Eval Across SDKs

5-way agent comparison using long-horizon eval:

| Name | SDK | Multi-Agent | What It Tests |
|------|-----|-------------|---------------|
| mini | mini | No | LearningAgent directly |
| claude | claude | No | ClaudeGoalSeekingAgent via SDK factory |
| copilot | copilot | No | CopilotGoalSeekingAgent via SDK factory |
| microsoft | microsoft | No | MicrosoftGoalSeekingAgent via SDK factory |
| multiagent-copilot | copilot | Yes | MultiAgentLearningAgent with spawning |

```bash
python -m amplihack.eval.matrix_eval --turns 500 --questions 50
python -m amplihack.eval.matrix_eval --agents mini claude --turns 100 --questions 20
```

## 11. Metacognition Grader

Grades reasoning traces on 4 dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Effort Calibration | 25% | Proportional effort to question difficulty |
| Sufficiency Judgment | 30% | Correct assessment of when enough info gathered |
| Search Quality | 25% | Ratio of useful results to total queries |
| Self Correction | 20% | Detects and fixes errors in reasoning |

## 12. Long-Horizon Self-Improvement

8-stage cycle per iteration:

1. **EVAL**: Run long-horizon eval for per-category scores
2. **ANALYZE**: Identify worst-performing category
3. **PROPOSE**: Patch proposer generates unified diff with hypothesis, expected impact, risk, confidence
4. **CHALLENGE**: Devil's advocate arguments against proposed patch
5. **VOTE**: 3 reviewers (quality, regression, simplicity) vote accept/reject/modify
6. **APPLY**: If accepted, apply patch and git commit
7. **RE-EVAL**: Run eval again
8. **DECIDE**: Auto-revert on regression > 5%, keep if net improvement >= 2%

```bash
python -m amplihack.eval.long_horizon_self_improve \
    --turns 100 --questions 20 --iterations 3
```

## 13. Philosophy

### Core Principles

1. **Ruthless Simplicity** -- KISS, minimize abstractions, avoid future-proofing
2. **Modular Architecture** ("Brick Philosophy") -- Self-contained modules with clear interfaces
3. **Zero-BS Implementation** -- Every function works or doesn't exist; no stubs, TODOs, placeholders
4. **Library vs Custom Code** -- Judgment call; keep integration points minimal and isolated

### Human-AI Partnership

- Humans define: Vision, specifications, contracts, quality standards
- AI builds: Code implementation according to specifications
- Humans validate: Testing behavior, not reviewing every line
- AI regenerates: Modules can be rebuilt when requirements change

### Decision Framework

1. Necessity: Do we need this now?
2. Simplicity: Simplest solution?
3. Modularity: Self-contained brick?
4. Regenerability: Can AI rebuild from spec?
5. Value: Does complexity add proportional value?
6. Maintenance: Easy to understand and change?

## 14. Additional Features

- **85+ skills**: PDF/Excel/Word processing, Azure admin, pre-commit management
- **Fleet Management**: Multi-VM orchestration via `amplihack fleet` TUI
- **RustyClawd**: High-performance Rust launcher (5-10x faster startup, 7x less memory)
- **Azure OpenAI Proxy**: Use Azure models via Claude Code
- **Document-Driven Development**: Docs-first methodology for large features
- **Workflow customization**: Edit `~/.amplihack/.claude/workflow/DEFAULT_WORKFLOW.md`
- **Benchmarking**: Performance measurement with eval-recipes
- **Windows partial support**: Core features work natively; fleet requires WSL

---

# Cross-Tool Integration Notes

## claude-mem + mde

- **AGPL-3.0 license** is restrictive -- any modifications deployed as a network service must release source code. This impacts commercial use.
- The `ragtime/` subdirectory has even more restrictive PolyForm Noncommercial license.
- The plugin install mechanism (`/plugin marketplace add`) requires Claude Code plugin support.
- Worker service on port 37777 could conflict with other local services.
- The 3-layer progressive disclosure pattern is a strong design worth studying for our own memory systems.

## mcp2cli + mde

- **MIT license** -- no restrictions, ideal for integration.
- `uv tool install mcp2cli` aligns with our mise-first / uv-first policy.
- `env:` and `file:` secret prefixes are compatible with fnox.
- The bake pattern could replace verbose MCP tool invocations in our workflows.
- TOON output format worth evaluating for our agent communication.
- `--search` pattern filtering useful for scoping large MCP servers.

## amplihack + mde

- **MIT license** -- no restrictions.
- The L1-L12 eval framework is the most sophisticated agent evaluation system discovered.
- Self-improvement loop (EVAL -> ANALYZE -> RESEARCH -> IMPROVE -> RE-EVAL -> DECIDE) with +2% commit threshold and >5% regression guard is directly applicable.
- Kuzu graph DB for agent memory is worth evaluating vs our current approach.
- The 37-agent taxonomy and 23-step DEFAULT_WORKFLOW provide a reference architecture.
- Teaching system with learning theory integration (Vygotsky scaffolding, Feynman technique) is unique.
- `uvx --from git+https://github.com/rysweet/amplihack amplihack claude` install pattern is elegant.
- The 1000-turn long-horizon memory test with 12 information blocks is a rigorous benchmark we could adopt.
