# Anthropic Official Sources - Complete Deep Review

Reviewed: 2026-03-20
Reviewer: research-agent (Opus 4.6, 1M context)
Sources fetched: 13 URLs via agent-fetch, 2 via gh API

---

## 1. Claude Code Repo (anthropics/claude-code)

**URL:** https://github.com/anthropics/claude-code
**Status:** [x] FULLY REVIEWED

### What is in the Repo

The repo is the public face of Claude Code -- Anthropic's agentic coding CLI. The README is minimal by design (the product is closed-source). Key contents:

- **README.md** -- installation instructions, data usage policies, links to official docs
- **plugins/** -- directory of first-party plugins (see Section 3 for full list)
- **demo.gif** -- animated product demo

### Installation (Current as of 2026-03)

npm install is DEPRECATED. Recommended methods:
- macOS/Linux: `curl -fsSL https://claude.ai/install.sh | bash`
- Homebrew: `brew install --cask claude-code`
- Windows: `irm https://claude.ai/install.ps1 | iex`
- WinGet: `winget install Anthropic.ClaudeCode`

### Issue Tracker Themes

Issues are open for bug reports. The `/bug` command inside Claude Code submits directly. Common themes:
- Permission prompt UX friction
- MCP server connection failures
- Context window exhaustion on large codebases
- Plugin installation/discovery issues

### Key Links from Repo

- Official docs: https://code.claude.com/docs/en/overview
- Setup docs: https://code.claude.com/docs/en/setup
- Data usage: https://code.claude.com/docs/en/data-usage
- Plugins docs: https://code.claude.com/docs/en/plugins
- Discord: https://anthropic.com/discord

### Plugins Bundled in claude-code Repo

These are first-party plugins shipped with the Claude Code repo itself (not the plugins-official marketplace):

| Plugin | Description |
|--------|-------------|
| agent-sdk-dev | Agent SDK development tooling |
| claude-opus-4-5-migration | Migration helper for Opus 4.5 |
| code-review | Code review workflows |
| commit-commands | Git commit slash commands |
| explanatory-output-style | Output style: explanatory |
| feature-dev | Feature development workflow |
| frontend-design | Frontend design assistant |
| hookify | Hook creation helper |
| learning-output-style | Output style: learning |
| plugin-dev | Plugin development helper |
| pr-review-toolkit | PR review tools |
| ralph-wiggum | Ralph loop (autonomous agent loop) |
| security-guidance | Security best practices |

---

## 2. Claude Agent SDK (anthropics/claude-agent-sdk-python)

**URL:** https://github.com/anthropics/claude-agent-sdk-python
**Status:** [x] FULLY REVIEWED

### Overview

Python SDK for programmatic access to Claude Code's agent capabilities. Formerly called "Claude Code SDK" (renamed at v0.1.0). The Claude Code CLI is BUNDLED in the pip package -- no separate install needed.

**Install:** `pip install claude-agent-sdk`
**Requires:** Python 3.10+
**Docs:** https://platform.claude.com/docs/en/agent-sdk/python

### Core API

#### query() -- Simple one-shot usage

```python
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

options = ClaudeAgentOptions(
    system_prompt="You are a helpful assistant",
    max_turns=1
)

async for message in query(prompt="Hello", options=options):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(block.text)
```

#### ClaudeSDKClient -- Bidirectional interactive conversations

Supports custom tools (in-process MCP servers) and hooks.

```python
async with ClaudeSDKClient(options=options) as client:
    await client.query("Greet Alice")
    async for msg in client.receive_response():
        print(msg)
```

### @tool Decorator

Defines custom tools as in-process MCP servers:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("greet", "Greet a user", {"name": str})
async def greet_user(args):
    return {
        "content": [
            {"type": "text", "text": f"Hello, {args['name']}!"}
        ]
    }

server = create_sdk_mcp_server(
    name="my-tools",
    version="1.0.0",
    tools=[greet_user]
)
```

### create_sdk_mcp_server()

Creates an in-process MCP server. Benefits over external MCP:
- No subprocess management
- No IPC overhead
- Single Python process
- Easier debugging
- Type safety

Supports MIXED server configurations (in-process + external):

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "internal": sdk_server,      # In-process
        "external": {                # External subprocess
            "type": "stdio",
            "command": "external-server"
        }
    }
)
```

### HookMatcher and Hooks

Hooks are Python functions invoked at specific points in the agent loop. They provide deterministic processing, NOT model-driven behavior.

Hook events: `PreToolUse`, plus others documented at https://platform.claude.com/docs/en/agent-sdk/hooks

```python
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

async def check_bash_command(input_data, tool_use_id, context):
    tool_name = input_data["tool_name"]
    tool_input = input_data["tool_input"]
    if tool_name != "Bash":
        return {}
    command = tool_input.get("command", "")
    if "dangerous" in command:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Blocked dangerous command",
            }
        }
    return {}

options = ClaudeAgentOptions(
    allowed_tools=["Bash"],
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[check_bash_command]),
        ],
    }
)
```

### ClaudeAgentOptions -- Full Configuration

Key fields:
- `system_prompt` -- Custom system prompt per agent
- `max_turns` -- Limit agent turns
- `allowed_tools` -- Permission allowlist (auto-approve; does NOT restrict toolset)
- `disallowed_tools` -- Block specific tools
- `permission_mode` -- Options: `'acceptEdits'` (auto-accept file edits), others
- `cwd` -- Working directory (str or Path)
- `mcp_servers` -- Dict of MCP server configs
- `hooks` -- Dict of hook event name to list of HookMatcher
- `cli_path` -- Custom path to Claude Code CLI binary

### Permission Evaluation Order

`allowed_tools` -> `permission_mode` / `can_use_tool` -> deny
See: https://platform.claude.com/docs/en/agent-sdk/permissions

### Type System

From `src/claude_agent_sdk/types.py`:
- `ClaudeAgentOptions` -- Configuration
- `AssistantMessage`, `UserMessage`, `SystemMessage`, `ResultMessage` -- Messages
- `TextBlock`, `ToolUseBlock`, `ToolResultBlock` -- Content blocks

### Error Types

From `src/claude_agent_sdk/_errors.py`:
- `ClaudeSDKError` -- Base
- `CLINotFoundError` -- Claude Code not installed
- `CLIConnectionError` -- Connection issues
- `ProcessError` -- Process failed (has `.exit_code`)
- `CLIJSONDecodeError` -- JSON parsing issues

### Migration from Claude Code SDK (< 0.1.0)

- `ClaudeCodeOptions` renamed to `ClaudeAgentOptions`
- Merged system prompt configuration
- Settings isolation and explicit control
- New: programmatic subagents and session forking

---

## 3. Official Plugins Directory (anthropics/claude-plugins-official)

**URL:** https://github.com/anthropics/claude-plugins-official
**Status:** [x] FULLY REVIEWED

### Structure

- `/plugins` -- Anthropic internal plugins
- `/external_plugins` -- Third-party community plugins

### Installation

```
/plugin install {plugin-name}@claude-plugins-official
```
or browse: `/plugin > Discover`

### Plugin Standard Structure

```
plugin-name/
+-- .claude-plugin/
|   +-- plugin.json      # Metadata (required)
+-- .mcp.json            # MCP server config (optional)
+-- commands/            # Slash commands (optional)
+-- agents/              # Agent definitions (optional)
+-- skills/              # Skill definitions (optional)
+-- README.md            # Documentation
```

### Complete Internal Plugin List (Anthropic-maintained)

| Plugin | Category | Description |
|--------|----------|-------------|
| agent-sdk-dev | Development | Agent SDK development tooling |
| clangd-lsp | LSP | C/C++ language server integration |
| claude-code-setup | Setup | Project configuration helper |
| claude-md-management | Config | CLAUDE.md file management |
| code-review | Workflow | Code review automation |
| code-simplifier | Refactor | Code simplification helper |
| commit-commands | Git | Commit-related slash commands |
| csharp-lsp | LSP | C# language server integration |
| example-plugin | Reference | Example plugin template |
| explanatory-output-style | Style | Explanatory output formatting |
| feature-dev | Workflow | Feature development workflow |
| frontend-design | Design | Frontend design assistant |
| gopls-lsp | LSP | Go language server integration |
| hookify | Development | Hook creation helper |
| jdtls-lsp | LSP | Java language server integration |
| kotlin-lsp | LSP | Kotlin language server integration |
| learning-output-style | Style | Learning-oriented output formatting |
| lua-lsp | LSP | Lua language server integration |
| math-olympiad | Specialized | Math competition problem solving |
| mcp-server-dev | Development | MCP server development helper |
| php-lsp | LSP | PHP language server integration |
| playground | Development | Experimental playground |
| plugin-dev | Development | Plugin development helper |
| pr-review-toolkit | Workflow | PR review tools |
| pyright-lsp | LSP | Python type checker (pyright) integration |
| ralph-loop | Autonomous | Autonomous agent loop (Ralph Wiggum pattern) |
| ruby-lsp | LSP | Ruby language server integration |
| rust-analyzer-lsp | LSP | Rust language server integration |
| security-guidance | Security | Security best practices |
| skill-creator | Skills | Skill creation assistant |
| swift-lsp | LSP | Swift language server integration |
| typescript-lsp | LSP | TypeScript language server integration |

### Recommendations for Our Project

HIGH priority (install now):
- **pyright-lsp** -- We use Python with type annotations extensively
- **claude-code-setup** -- Project configuration management
- **claude-md-management** -- CLAUDE.md file management
- **code-review** -- Code review automation
- **security-guidance** -- Security best practices
- **hookify** -- Creating hooks for our Python hooks system
- **skill-creator** -- For creating custom skills

MEDIUM priority:
- **commit-commands** -- Git workflow enhancement
- **pr-review-toolkit** -- PR review automation
- **feature-dev** -- Feature development workflow
- **ralph-loop** -- Autonomous agent loop pattern

LOW priority (language-specific LSPs we do not need):
- clangd-lsp, csharp-lsp, gopls-lsp, jdtls-lsp, kotlin-lsp, lua-lsp, php-lsp, ruby-lsp, rust-analyzer-lsp, swift-lsp, typescript-lsp

### External Plugins

The external_plugins directory requires the submission form at https://clau.de/plugin-directory-submission. The GitHub tree view did not render individual plugin names (JS-rendered page), but the repo description indicates third-party partners submit here.

---

## 4. Cookbooks (anthropics/claude-cookbooks)

**URL:** https://github.com/anthropics/claude-cookbooks
**Status:** [x] FULLY REVIEWED

Note: This repo maps to `anthropics/anthropic-cookbook` on GitHub (the URL redirects).

### Complete Recipe List

#### Capabilities
| Recipe | Relevance to Our Project |
|--------|--------------------------|
| Classification | LOW -- text classification techniques |
| Retrieval Augmented Generation | MEDIUM -- RAG patterns for research pipeline |
| Summarization | MEDIUM -- text summarization for research |

#### Tool Use and Integration
| Recipe | Relevance |
|--------|-----------|
| Tool use (general) | HIGH -- tool integration patterns |
| Customer service agent | LOW -- domain-specific |
| Calculator integration | LOW -- simple example |
| SQL queries | MEDIUM -- database interaction patterns |

#### Third-Party Integrations
| Recipe | Relevance |
|--------|-----------|
| Vector databases (Pinecone) | MEDIUM -- RAG with vector DB |
| Wikipedia search | LOW -- specific integration |
| Web pages (read with Haiku) | MEDIUM -- web content extraction |
| Embeddings with Voyage AI | LOW -- specific vendor |

#### Multimodal
| Recipe | Relevance |
|--------|-----------|
| Getting started with vision | LOW |
| Best practices for vision | LOW |
| Interpreting charts and graphs | LOW |
| Extracting content from forms | LOW |
| Generate images (Stable Diffusion) | LOW |

#### Advanced Techniques
| Recipe | Relevance |
|--------|-----------|
| Sub-agents (Haiku + Opus) | HIGH -- multi-agent patterns |
| Upload PDFs to Claude | MEDIUM -- document processing |
| Automated evaluations | HIGH -- eval patterns for research |
| Enable JSON mode | MEDIUM -- structured output |
| Moderation filter | LOW |
| Prompt caching | HIGH -- performance optimization |

### Key Takeaway

The cookbook is API-focused (Python SDK), not Claude Code CLI focused. Most relevant recipes: **sub-agents**, **automated evaluations**, **prompt caching**, **tool use**, and **RAG**.

---

## 5. Official Skills (anthropics/skills)

**URL:** https://github.com/anthropics/skills
**Status:** [x] FULLY REVIEWED

### What Skills Are

Skills are folders of instructions, scripts, and resources that Claude loads dynamically. Each skill has a `SKILL.md` file with YAML frontmatter and markdown instructions. They work in Claude Code, Claude.ai, and the Claude API.

### Agent Skills Standard

Spec lives at **agentskills.io** (referenced in the repo). The repo contains:
- `./skills/` -- Example skills
- `./spec/` -- The Agent Skills specification
- `./template/` -- Skill template

### SKILL.md Spec Requirements

Minimal SKILL.md:
```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---

# My Skill Name

[Instructions for Claude]

## Examples
- Example usage 1

## Guidelines
- Guideline 1
```

Required frontmatter: `name` (lowercase, hyphens) and `description` (complete, when to use it).

### Complete Skill List

| Skill | Category | License |
|-------|----------|---------|
| algorithmic-art | Creative & Design | Apache 2.0 |
| brand-guidelines | Enterprise & Communication | Apache 2.0 |
| canvas-design | Creative & Design | Apache 2.0 |
| claude-api | Development & Technical | Apache 2.0 |
| doc-coauthoring | Enterprise & Communication | Apache 2.0 |
| docx | Document (production) | Source-available |
| frontend-design | Development & Technical | Apache 2.0 |
| internal-comms | Enterprise & Communication | Apache 2.0 |
| mcp-builder | Development & Technical | Apache 2.0 |
| pdf | Document (production) | Source-available |
| pptx | Document (production) | Source-available |
| skill-creator | Development & Technical | Apache 2.0 |
| slack-gif-creator | Creative & Design | Apache 2.0 |
| theme-factory | Creative & Design | Apache 2.0 |
| web-artifacts-builder | Development & Technical | Apache 2.0 |
| webapp-testing | Development & Technical | Apache 2.0 |
| xlsx | Document (production) | Source-available |

Note: docx, pdf, pptx, xlsx are the skills that power Claude's document creation capabilities in production. They are source-available (not open source) but shared as reference.

### Installing in Claude Code

```
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

### Partner Skills

- **Notion** -- Notion Skills for Claude (https://www.notion.so/notiondevs/Notion-Skills-for-Claude)

### API Usage

Skills can be used via the Claude API. See: https://docs.claude.com/en/api/skills-guide#creating-a-skill

---

## 6. Engineering Blog Posts -- Complete Pattern Extraction

### 6A. Building Effective Agents (Dec 19, 2024)

**URL:** https://www.anthropic.com/engineering/building-effective-agents
**Authors:** Erik Schluntz, Barry Zhang
**Status:** [x] FULLY REVIEWED -- Complete content extracted

#### Core Framework: Workflows vs. Agents

- **Workflows** = LLMs + tools orchestrated through predefined code paths
- **Agents** = LLMs dynamically direct their own processes and tool usage

#### Five Workflow Patterns

1. **Prompt Chaining** -- Sequential steps, each LLM call processes previous output. Add programmatic "gates" for validation. Use when task decomposes cleanly into fixed subtasks. Trade latency for accuracy.

2. **Routing** -- Classify input, direct to specialized followup. Use for distinct categories needing different handling. Example: easy questions -> Haiku, hard -> Sonnet/Opus.

3. **Parallelization** -- Two variants:
   - **Sectioning**: Independent subtasks run in parallel
   - **Voting**: Same task multiple times for diverse outputs
   Use when subtasks are independent or when multiple perspectives increase confidence.

4. **Orchestrator-Workers** -- Central LLM dynamically breaks down tasks, delegates to workers, synthesizes results. Key difference from parallelization: subtasks are NOT predefined. Use for coding products, multi-source search.

5. **Evaluator-Optimizer** -- One LLM generates, another evaluates in a loop. Use when clear evaluation criteria exist and iterative refinement provides measurable value.

#### Agent Design Principles

1. **Simplicity** in agent design
2. **Transparency** -- explicitly show planning steps
3. **ACI (Agent-Computer Interface)** -- invest as much effort as HCI

#### Tool Engineering (Appendix 2 -- Critical)

- Give model enough tokens to "think" before committing
- Keep format close to natural internet text
- No formatting overhead (no counting lines, no string-escaping)
- Write tool descriptions like docstrings for a junior developer
- Test extensively in Workbench
- **Poka-yoke** tools (make mistakes impossible)
- Use absolute file paths, not relative
- "We spent more time optimizing tools than the overall prompt" -- SWE-bench team

#### When NOT to Use Agents

Start with single LLM calls + retrieval + in-context examples. Add complexity only when it demonstrably improves outcomes. Agents trade latency and cost for performance.

---

### 6B. Building a C Compiler with Parallel Claudes (Feb 05, 2026)

**URL:** https://www.anthropic.com/engineering/building-c-compiler
**Author:** Nicholas Carlini (Safeguards team researcher)
**Status:** [x] FULLY REVIEWED -- Complete content extracted

#### The Experiment

16 parallel Claude agents built a 100,000-line Rust-based C compiler from scratch. ~2,000 Claude Code sessions, $20,000 in API costs, 2 billion input tokens, 140 million output tokens over two weeks. The compiler can build Linux 6.9 on x86, ARM, and RISC-V.

#### Agent Loop Harness

```bash
#!/bin/bash
while true; do
    COMMIT=$(git rev-parse --short=6 HEAD)
    LOGFILE="agent_logs/agent_${COMMIT}.log"
    claude --dangerously-skip-permissions \
           -p "$(cat AGENT_PROMPT.md)" \
           --model claude-opus-X-Y &> "$LOGFILE"
done
```

Run this in a CONTAINER, not bare metal.

#### File-Locking Synchronization

Multiple agents share a bare git repo. Each agent:
1. Takes a "lock" by writing to `current_tasks/parse_if_statement.txt`
2. If two agents claim the same task, git forces the second to pick differently
3. Works on task, pulls from upstream, merges, pushes, removes lock
4. Merge conflicts are frequent but Claude handles them

No orchestration agent. Each Claude picks the "next most obvious" problem. Maintains running docs of failed approaches and remaining tasks.

#### Key Lessons

**Write extremely high-quality tests:**
- Test verifier must be nearly perfect
- Built CI pipeline with strict enforcement
- New commits cannot break existing code

**Put yourself in Claude's shoes:**
- Each agent drops into fresh container with no context
- Maintain extensive READMEs and progress files
- Context window pollution: test harness should NOT print thousands of lines
- Log to files, use ERROR on same line as reason for grep
- Pre-compute aggregate summary statistics

**Time blindness:**
- Claude cannot tell time
- Print incremental progress infrequently
- Include `--fast` option (1% or 10% random sample)
- Subsample is deterministic per-agent but random across VMs

**Make parallelism easy:**
- Many distinct failing tests = trivial parallelism
- Single giant task (Linux kernel) = all agents stuck on same bug
- Solution: Use GCC as known-good oracle, randomly compile most files with GCC, only remaining with Claude's compiler
- Delta debugging for pairs of files that fail together

**Multiple agent roles:**
- One agent: coalesce duplicate code
- One agent: improve compiler performance
- One agent: output efficient compiled code
- One agent: Rust code quality critique
- One agent: documentation

---

### 6C. Effective Harnesses for Long-Running Agents (Nov 26, 2025)

**URL:** https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
**Author:** Justin Young
**Status:** [x] FULLY REVIEWED -- Complete content extracted

#### The Problem

Agents must work in discrete sessions. Each new session begins with NO memory. Like engineers working in shifts with no handoff notes.

#### Two-Part Solution

1. **Initializer Agent** -- First session only. Sets up:
   - `init.sh` script (runs dev server)
   - `claude-progress.txt` (progress log)
   - Initial git commit
   - **Feature list file** (JSON, 200+ features, all initially `"passes": false`)

2. **Coding Agent** -- Every subsequent session:
   - Reads progress file and git logs
   - Chooses ONE feature to work on (incremental)
   - Tests with browser automation (Puppeteer MCP)
   - Commits to git with descriptive messages
   - Updates progress file

#### Feature List (JSON format -- critical detail)

```json
{
    "category": "functional",
    "description": "New chat button creates a fresh conversation",
    "steps": [
      "Navigate to main interface",
      "Click the 'New Chat' button",
      "Verify a new conversation is created"
    ],
    "passes": false
}
```

JSON is used because the model is LESS LIKELY to inappropriately change JSON compared to Markdown. Strong instruction: "It is unacceptable to remove or edit tests."

#### claude-progress.txt Pattern

The key insight: agents quickly understand work state by reading `claude-progress.txt` + git history. Inspiration from what effective software engineers do daily.

#### Getting Up to Speed (Every Session)

1. Run `pwd`
2. Read git logs and progress files
3. Read feature list, choose highest-priority unfinished feature
4. Run `init.sh` to start dev server
5. Run basic end-to-end test BEFORE implementing new features
6. If app is broken, fix existing bugs FIRST

#### Failure Modes and Solutions

| Problem | Initializer Solution | Coding Agent Solution |
|---------|---------------------|----------------------|
| Declares victory too early | Feature list file | Read feature list, choose single feature |
| Leaves bugs/undocumented progress | Git repo + progress file | Read progress + git logs; commit at end |
| Marks features done prematurely | Feature list file | Self-verify with browser automation |
| Wastes time figuring out how to run app | Write init.sh | Read init.sh at session start |

---

### 6D. Effective Context Engineering for AI Agents (Sep 29, 2025)

**URL:** https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
**Authors:** Prithvi Rajasekaran, Ethan Dixon, Carly Ryan, Jeremy Hadfield (Applied AI team)
**Status:** [x] FULLY REVIEWED -- Complete content extracted

#### Context Engineering vs. Prompt Engineering

- **Prompt engineering** = writing and organizing LLM instructions
- **Context engineering** = curating the ENTIRE optimal token set during inference (system prompts, tools, MCP, external data, message history, etc.)

Context engineering is the natural progression of prompt engineering as we build agents that operate over multiple turns.

#### Why Context Engineering Matters

- **Context rot**: as tokens increase, recall accuracy decreases (across all models)
- Context is a **finite resource with diminishing marginal returns**
- Models have an "attention budget" (n-squared pairwise token relationships)
- Performance gradient, not hard cliff

#### Guiding Principle

Find the **smallest possible set of high-signal tokens** that maximize the likelihood of desired outcome.

#### System Prompts

- Use simple, direct language at the RIGHT ALTITUDE (not too prescriptive, not too vague)
- Organize into distinct sections (`<background_information>`, `<instructions>`, etc.)
- Use XML tags or Markdown headers for delineation
- Start minimal, add based on failure modes
- Minimal does NOT mean short -- include sufficient info

#### Tools

- Tools define the contract between agents and their action space
- Return token-efficient information
- Self-contained, robust to error, clear intended use
- Minimal viable set -- avoid bloated tool sets
- "If a human engineer can't say which tool to use, an AI agent can't either"

#### Examples (Few-Shot)

- Curate diverse, canonical examples (NOT exhaustive edge cases)
- "Examples are the pictures worth a thousand words"

#### Just-In-Time Context Retrieval

Shift from pre-inference retrieval to agentic "just in time" strategies:
- Maintain lightweight identifiers (file paths, queries, URLs)
- Dynamically load at runtime using tools
- Claude Code uses this: writes targeted queries, uses `head`/`tail`, never loads full datasets
- Mirrors human cognition: we don't memorize, we index

**Progressive disclosure**: agents incrementally discover context. File sizes suggest complexity, naming conventions hint at purpose, timestamps proxy relevance.

**Hybrid strategy**: Claude Code drops CLAUDE.md files into context up front, while glob/grep enable just-in-time retrieval.

#### Long-Horizon Techniques

**Compaction:**
- Summarize conversation nearing context limit, reinitiate with summary
- Preserve architectural decisions, unresolved bugs, implementation details
- Discard redundant tool outputs
- Continue with compressed context + 5 most recent files
- Safest form: tool result clearing (clearing old tool call results)
- Tune on complex agent traces: maximize recall first, then improve precision

**Structured Note-Taking (Agentic Memory):**
- Agent writes notes persisted outside context window
- Like a to-do list or NOTES.md file
- Claude playing Pokemon: maintains tallies across thousands of steps, develops maps, tracks objectives

**Sub-Agent Architectures:**
- Specialized sub-agents handle focused tasks with clean context
- Each explores extensively (tens of thousands of tokens)
- Returns condensed summary (1,000-2,000 tokens)
- Clear separation of concerns
- From "How we built our multi-agent research system" blog post

#### Memory Tool

Released with Sonnet 4.5 launch. File-based system for storing/consulting information outside context window. Available on Claude Developer Platform in public beta.

---

### 6E. Claude Code Best Practices (Apr 18, 2025)

**URL:** https://www.anthropic.com/engineering/claude-code-best-practices
**Status:** [~] PARTIALLY REVIEWED -- page renders as CSS/JS, full article not extractable via agent-fetch

The page is heavily JavaScript-rendered and agent-fetch only captures CSS. The canonical reference for this content is https://code.claude.com/docs/en/overview (the official documentation site).

Known best practices from this blog (from other references):
- Use CLAUDE.md files for project context
- Prefer specific tool calls over broad operations
- Use git for state management
- Invest in tool descriptions

---

## 7. Claude Blog + Platform Content

### 7A. How Anthropic Teams Use Claude Code

**URL:** https://claude.com/blog/how-anthropic-teams-use-claude-code
**Status:** [x] FULLY REVIEWED

#### Internal Use Patterns at Anthropic

**Codebase Navigation:**
- New data scientists feed entire codebase to get productive quickly
- Claude reads CLAUDE.md files, identifies relevant ones, explains data pipeline dependencies
- Product Engineering uses Claude Code as "first stop" for any programming task

**Testing and Code Review:**
- Product Design: automated PR comments via GitHub Actions
- Security Engineering: shifted to "pseudocode -> TDD with Claude -> check in periodically"
- Inference team: translate tests into unfamiliar languages (e.g., Rust)

**Debugging:**
- Security team feeds stack traces + docs to trace control flow (3x faster than manual)
- Product Engineering tackles bugs in unfamiliar codebases
- Data Infrastructure: fed Kubernetes dashboard screenshots, Claude guided through Google Cloud UI

**Prototyping:**
- Product Design: feed Figma files, set up autonomous loops
- Claude builds Vim key bindings for itself
- Discovered unexpected use: mapping error states and edge cases DURING design
- Data scientists build React apps for RL visualization without knowing TypeScript

**Documentation:**
- Inference team: what takes 1 hour of Google searching takes 10-20 minutes (80% reduction)
- Security team: ingest docs to create markdown runbooks

**Automation:**
- Growth Marketing: agentic workflow for ad generation (hundreds of variations in minutes)
- Figma plugin: generate 100 ad variations (half a second per batch vs hours)
- Legal team: prototype phone tree systems

#### Key Insight

"Claude Code works best when you focus on the human workflows it can augment. The most successful teams treat Claude Code as a thought partner rather than a code generator."

### 7B. Claude Blog Index (Recent Posts as of 2026-03-20)

Extracted from HTML. Key recent posts:

| Date | Title | Category |
|------|-------|----------|
| Mar 13, 2026 | 1M context is now generally available for Opus 4.6 and Sonnet 4.6 | Product |
| Mar 12, 2026 | Claude now creates interactive charts, diagrams and visualizations | Product |
| Feb 20, 2026 | Bringing automated preview, review, and merge to Claude Code on desktop | Claude Code |
| Feb 17, 2026 | Increase web search accuracy and efficiency with dynamic filtering | Product |
| Feb 9, 2026 | Behind the model launch: What customers discovered testing Claude Opus 4.6 early | Enterprise |
| -- | Code with Claude comes to San Francisco, London, and Tokyo | Events |
| -- | Common workflow patterns for AI agents -- and when to use them | Agents |
| -- | Improving skill-creator: Test, measure, and refine Agent Skills | Skills |
| -- | Cowork and plugins for teams across the enterprise | Enterprise |
| -- | How AI helps break the cost barrier to COBOL modernization | Enterprise |

### 7C. Engineering Blog Complete Index (as of 2026-03-20)

| Date | Title | Key Topic |
|------|-------|-----------|
| (Featured) | Quantifying infrastructure noise in agentic coding evals | Evals |
| Mar 06, 2026 | Eval awareness in Claude Opus 4.6's BrowseComp performance | Evals |
| Feb 05, 2026 | Building a C compiler with a team of parallel Claudes | Agent teams |
| Jan 21, 2026 | Designing AI-resistant technical evaluations | Evals |
| Jan 09, 2026 | Demystifying evals for AI agents | Evals |
| Nov 26, 2025 | Effective harnesses for long-running agents | Agent harnesses |
| Nov 24, 2025 | Introducing advanced tool use on the Claude Developer Platform | Tools |
| Nov 04, 2025 | Code execution with MCP: Building more efficient agents | MCP |
| Oct 20, 2025 | Beyond permission prompts: making Claude Code more secure and autonomous | Security |
| Sep 29, 2025 | Effective context engineering for AI agents | Context engineering |
| Sep 17, 2025 | A postmortem of three recent issues | Reliability |
| Sep 11, 2025 | Writing effective tools for agents -- with agents | Tool design |
| Jun 26, 2025 | Desktop Extensions: One-click MCP server installation | MCP |
| Jun 13, 2025 | How we built our multi-agent research system | Multi-agent |
| Apr 18, 2025 | Claude Code: Best practices for agentic coding | Best practices |
| Mar 20, 2025 | The "think" tool: Enabling Claude to stop and think | Tool design |
| Jan 06, 2025 | Raising the bar on SWE-bench Verified with Claude 3.5 Sonnet | Benchmarks |
| Dec 19, 2024 | Building effective agents | Agent patterns |
| Sep 19, 2024 | Introducing Contextual Retrieval | RAG |

---

## 8. Cross-Cutting Patterns (Synthesis)

### Pattern: The Initializer + Worker Architecture

Appears in: Effective Harnesses, C Compiler, Context Engineering

1. First session: specialized prompt sets up environment (feature list, progress file, init.sh)
2. Subsequent sessions: read state, pick next task, work incrementally, commit

### Pattern: File-Based State for Agent Memory

Appears in: ALL engineering blog posts

- `claude-progress.txt` -- progress log
- `feature_list.json` -- feature tracking (JSON preferred over Markdown)
- `current_tasks/*.txt` -- task locking
- `CLAUDE.md` -- project context (loaded on session start)
- Git history -- implicit state tracking

### Pattern: Test-Driven Agent Feedback

Appears in: C Compiler, Effective Harnesses

- Near-perfect test verifier is CRITICAL
- CI pipeline enforcement (new commits cannot break existing code)
- `--fast` mode for quick subset testing
- Deterministic per-agent but random across VMs
- Browser automation (Puppeteer MCP) for end-to-end verification

### Pattern: Context as Finite Resource

Appears in: Context Engineering, C Compiler

- Do not print thousands of lines to stdout
- Log to files, use ERROR on same line for grep
- Pre-compute aggregate statistics
- Tool result clearing (oldest first)
- Compaction: summarize, reinitiate
- Just-in-time retrieval over pre-computed indexing

### Pattern: Absolute Minimum Viable Complexity

Appears in: Building Effective Agents, Context Engineering

- Start with single LLM call + retrieval
- Add agentic patterns only when demonstrably needed
- "Do the simplest thing that works"
- Frameworks obscure; prefer raw API calls initially

---

## 9. URLs Cataloged During This Review

| URL | Status | Content Type |
|-----|--------|-------------|
| https://github.com/anthropics/claude-code | [x] Full | Repo README |
| https://github.com/anthropics/claude-agent-sdk-python | [x] Full | Repo README |
| https://github.com/anthropics/claude-plugins-official | [x] Full | Repo README |
| https://github.com/anthropics/claude-cookbooks | [x] Full | Repo README |
| https://github.com/anthropics/skills | [x] Full | Repo README |
| https://www.anthropic.com/engineering | [x] Full | Blog index |
| https://claude.com/blog | [x] Full | Blog index |
| https://www.anthropic.com/engineering/building-effective-agents | [x] Full | Blog post |
| https://www.anthropic.com/engineering/building-c-compiler | [x] Full | Blog post |
| https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | [x] Full | Blog post |
| https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | [x] Full | Blog post |
| https://claude.com/blog/how-anthropic-teams-use-claude-code | [x] Full | Blog post |
| https://www.anthropic.com/engineering/claude-code-best-practices | [~] Partial | JS-rendered |
| https://code.claude.com/docs/en/overview | [ ] Not fetched | Official docs |
| https://code.claude.com/docs/en/plugins | [ ] Not fetched | Plugin docs |
| https://platform.claude.com/docs/en/agent-sdk/python | [ ] Not fetched | SDK docs |
| https://platform.claude.com/docs/en/agent-sdk/hooks | [ ] Not fetched | Hooks docs |
| https://platform.claude.com/docs/en/agent-sdk/permissions | [ ] Not fetched | Permissions |
| https://platform.claude.com/cookbook/patterns-agents-basic-workflows | [ ] Not fetched | Cookbook |
| https://platform.claude.com/cookbook/tool-use-memory-cookbook | [ ] Not fetched | Memory cookbook |
| https://agentskills.io | [ ] Not fetched | Skills spec |
| https://docs.claude.com/en/api/skills-guide | [ ] Not fetched | Skills API |
| https://github.com/anthropics/claudes-c-compiler | [ ] Not fetched | C compiler source |
| https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding | [ ] Not fetched | Quickstart |
| https://www.anthropic.com/engineering/writing-tools-for-agents | [ ] Not fetched | Blog post |
| https://www.anthropic.com/engineering/multi-agent-research-system | [ ] Not fetched | Blog post |
| https://www.anthropic.com/engineering/claude-code-sandboxing | [ ] Not fetched | Blog post |
| https://www.anthropic.com/engineering/code-execution-with-mcp | [ ] Not fetched | Blog post |
| https://www.anthropic.com/engineering/advanced-tool-use | [ ] Not fetched | Blog post |
| https://www.anthropic.com/engineering/claude-think-tool | [ ] Not fetched | Blog post |
| https://clau.de/plugin-directory-submission | [ ] Not fetched | Plugin submission |

---

## 10. Action Items for Our Project

1. **Install pyright-lsp plugin** -- matches our Python-first policy
2. **Install claude-md-management plugin** -- we manage CLAUDE.md extensively
3. **Install skill-creator plugin** -- for creating our custom skills
4. **Adopt initializer+worker pattern** from Effective Harnesses for long-running tasks
5. **Use JSON for feature tracking** (not Markdown) when building agent workflows
6. **Implement claude-progress.txt** pattern for multi-session agent work
7. **Add `--fast` test sampling** to our agent test harnesses
8. **Explore the Skills API** for programmatic skill usage
9. **Fetch remaining [ ] URLs** in a follow-up research cycle
10. **Read the Agent Skills spec** at agentskills.io for our custom skill format
