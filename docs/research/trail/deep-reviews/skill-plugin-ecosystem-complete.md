# Claude Code Skill & Plugin Ecosystem -- Definitive Catalog

Deep review date: 2026-03-20
Sources fetched via agent-fetch from 8 repositories.

---

## Table of Contents

1. [awesome-claude-plugins (ComposioHQ)](#1-awesome-claude-plugins-composiohq)
2. [awesome-claude-skills (ComposioHQ)](#2-awesome-claude-skills-composiohq)
3. [personal-os-skills (ArtemXTech)](#3-personal-os-skills-artemxtech)
4. [amans-skills (amanaiproduct)](#4-amans-skills-amanaiproduct)
5. [hermes-agent (NousResearch)](#5-hermes-agent-nousresearch)
6. [martinemde/dotfiles](#6-martinemde-dotfiles)
7. [gitagent (open-gitagent)](#7-gitagent-open-gitagent)
8. [CLI-Anything (HKUDS)](#8-cli-anything-hkuds)
9. [Cross-Cutting Patterns](#9-cross-cutting-patterns)
10. [Relevance to MDE Project](#10-relevance-to-mde-project)

---

## 1. awesome-claude-plugins (ComposioHQ)

**URL:** https://github.com/ComposioHQ/awesome-claude-plugins
**License:** MIT
**Purpose:** Curated catalog of production-ready Claude Code plugins.

### Plugin Structure Standard

Every plugin in this repo follows the official Claude Code plugin layout:

```
plugin-name/
  .claude-plugin/
    plugin.json        # Plugin metadata
  skills/              # SKILL.md definitions (optional)
  commands/            # Slash command .md files (optional)
  agents/              # Agent definitions (optional)
  hooks/               # Event hooks as hooks.json (optional)
```

Installation: `claude --plugin-dir ./plugin-name` or load multiple with repeated `--plugin-dir` flags.

### Complete Plugin Catalog

#### Integrations

| Plugin | Description |
|--------|-------------|
| **connect-apps** | Connect Claude to 500+ SaaS apps via Composio. Send emails, create issues, post to Slack, update databases. Handles OAuth and auth flows. Setup via `/connect-apps:setup` with a free Composio API key. |

#### Frontend & Design

| Plugin | Description |
|--------|-------------|
| **frontend-design** | Production-grade UI -- avoids generic "AI slop" with bold typography, unique color palettes, creative layouts. |
| **artifacts-builder** | Multi-component HTML artifacts using React, Tailwind CSS, shadcn/ui. |
| **theme-factory** | Applies professional font/color themes to artifacts (slides, docs, reports, HTML landing pages). 10 pre-set themes. |
| **canvas-design** | Visual art in PNG and PDF using design philosophy and aesthetic principles for posters and static pieces. |
| **senior-frontend** | React/Next.js/TypeScript patterns with bundle analysis, component generation, accessibility best practices. |
| **frontend-developer** | Frontend development specialist agent for modern web interfaces. |

#### Git & Version Control

| Plugin | Description |
|--------|-------------|
| **commit** | Smart git commits using conventional commit format with meaningful messages and emojis. |
| **create-pr** | Automates PR creation with templates, descriptions, and labels. |
| **pr-review** | Comprehensive PR reviews with feedback on code quality, security, best practices. |
| **changelog-generator** | Creates user-facing changelogs from git commits -- transforms technical commits into customer-friendly release notes. |
| **ship** | Complete PR workflow: lint, test, review, deploy -- commit to production in one command. |

#### Code Quality & Testing

| Plugin | Description |
|--------|-------------|
| **code-review** | Comprehensive code review with best practices, patterns, improvement suggestions. |
| **test-writer-fixer** | Auto-write and fix unit tests. Supports Jest, Vitest, Pytest, and more. |
| **debugger** | Advanced debugging assistant for complex bugs. |
| **bug-fix** | Analyzes stack traces and code to identify and fix bugs. |

#### Backend & Architecture

| Plugin | Description |
|--------|-------------|
| **backend-architect** | Backend architecture patterns, API design, database schemas, system design. |
| **mcp-builder** | Guides creation of high-quality MCP servers for integrating external APIs/services with LLMs. |
| **agent-sdk-dev** | Claude Agent SDK development helper for building custom AI agents. |

#### DevOps & Performance

| Plugin | Description |
|--------|-------------|
| **perf** | Performance analysis and optimization -- identify bottlenecks and improve speed. |
| **audit-project** | Full project audit: code quality, dependencies, security, best practices. |
| **aws-cost-saver** | (External: prajapatimehul) 173 checks across EC2, RDS, S3, Lambda. ML-powered recommendations with real AWS API pricing. |
| **Manifest** | (External: mnfst) Real-time cost observability for OpenClaw agents -- track tokens, costs, messages, model usage. Self-hosted, OTLP ingestion, 28+ LLM models. |

#### Documentation & Security

| Plugin | Description |
|--------|-------------|
| **documentation-generator** | Generate READMEs, API docs, and guides from code. |
| **security-guidance** | Security best practices, vulnerability detection, OWASP guidelines, secure coding. |

#### Developer Productivity

| Plugin | Description |
|--------|-------------|
| **developer-growth-analysis** | Analyzes Claude Code chat history to identify coding patterns, dev gaps, curate personalized learning resources. |
| **skill-bus** | The skill for connecting skills -- wire context, conditions, and other skills into any skill invocation declaratively. Zero dependencies. |
| **context-mode** | (External: mksglu) Process large outputs in sandboxed subprocesses, keeping only summaries in context window. 98% context savings across 21 benchmarked scenarios. |

#### Image Generation

| Plugin | Description |
|--------|-------------|
| **nano-banana** | (External: Ibrahim-3d) Google Gemini image generation. Text-to-image, text-guided editing, style transfer, 4K output, search grounding, multi-reference composition via `/genimage`. |

### Key Plugins Deep Dive

#### connect-apps
- Uses Composio under the hood for auth/API integration
- Supports Gmail, Slack, GitHub, Notion, and 500+ services
- Setup: clone repo, run `claude --plugin-dir ./connect-apps`, then `/connect-apps:setup`
- Requires free API key from platform.composio.dev

#### audit-project
- Full-spectrum project audit covering code quality, dependency health, security posture, best practices
- Produces actionable audit reports

#### skill-bus
- Meta-skill: wires context, conditions, and other skills into any skill invocation
- Declarative configuration -- no modification of target skills needed
- Zero dependencies

---

## 2. awesome-claude-skills (ComposioHQ)

**URL:** https://github.com/ComposioHQ/awesome-claude-skills
**License:** Apache 2.0
**Purpose:** Curated list of Claude Skills for Claude.ai, Claude Code, and Claude API.

### Skill Structure Standard

```
skill-name/
  SKILL.md          # Required: YAML frontmatter + instructions
  scripts/          # Optional: helper scripts
  templates/        # Optional: document templates
  resources/        # Optional: reference files
```

SKILL.md frontmatter:
```yaml
---
name: my-skill-name
description: A clear description of what this skill does.
---
```

Installation for Claude Code: copy skill folder to `~/.config/claude-code/skills/`.

### Complete Skill Catalog

#### Document Processing

| Skill | Source | Description |
|-------|--------|-------------|
| **docx** | anthropics/skills | Create, edit, analyze Word docs with tracked changes, comments, formatting. |
| **pdf** | anthropics/skills | Extract text, tables, metadata, merge & annotate PDFs. |
| **pptx** | anthropics/skills | Read, generate, adjust slides, layouts, templates. |
| **xlsx** | anthropics/skills | Spreadsheet manipulation: formulas, charts, data transformations. |
| **Markdown to EPUB Converter** | smerchek/claude-epub-skill | Converts markdown/chat summaries into professional EPUB ebooks. |

#### Development & Code Tools

| Skill | Source | Description |
|-------|--------|-------------|
| **artifacts-builder** | anthropics/skills | Multi-component claude.ai HTML artifacts (React, Tailwind, shadcn/ui). |
| **aws-skills** | zxkane/aws-skills | AWS CDK best practices, cost optimization MCP servers, serverless/event-driven patterns. |
| **Changelog Generator** | ComposioHQ | User-facing changelogs from git commits. |
| **Claude Code Terminal Title** | bluzername | Dynamic terminal window titles describing current work. |
| **D3.js Visualization** | chrisvoncsefalvay | D3 charts and interactive data visualizations. |
| **FFUF Web Fuzzing** | jthack | Integrates ffuf web fuzzer for vulnerability analysis. |
| **finishing-a-development-branch** | obra/superpowers | Guides completion of dev work with clear options and workflow handling. |
| **iOS Simulator** | conorluddy | Claude interacts with iOS Simulator for testing/debugging. |
| **jules** | sanjay3290 | Delegate coding tasks to Google Jules AI agent for async bug fixes, docs, tests, features on GitHub repos. |
| **LangSmith Fetch** | ComposioHQ/OthmanAdi | Debug LangChain/LangGraph agents by fetching execution traces from LangSmith Studio. First AI observability skill. |
| **MCP Builder** | ComposioHQ | Guides creation of MCP servers (Python or TypeScript). |
| **move-code-quality-skill** | 1NickPappas | Analyzes Move language packages against Move Book Code Quality Checklist. |
| **Playwright Browser Automation** | lackeyjb | Model-invoked Playwright automation for testing/validating web apps. |
| **prompt-engineering** | NeoLabHQ/context-engineering-kit | Prompt engineering techniques including Anthropic best practices. |
| **pypict-claude-skill** | omkamal | PICT pairwise combinatorial testing for requirements or code. |
| **reddit-fetch** | ykdojo | Fetches Reddit content via Gemini CLI when WebFetch returns 403. |
| **Skill Creator** | ComposioHQ | Guidance for creating effective Claude Skills. |
| **Skill Seekers** | yusufkaraaslan | Converts any documentation website into a Claude skill in minutes. |
| **software-architecture** | NeoLabHQ/context-engineering-kit | Clean Architecture, SOLID principles, comprehensive design patterns. |
| **subagent-driven-development** | NeoLabHQ/context-engineering-kit | Dispatches independent subagents for individual tasks with code review checkpoints between iterations. |
| **test-driven-development** | obra/superpowers | Use before writing implementation code. |
| **using-git-worktrees** | obra/superpowers | Creates isolated git worktrees with smart directory selection and safety verification. |
| **Connect** | ComposioHQ | Connect Claude to 1000+ apps (Gmail, Slack, GitHub, Notion, etc.). |
| **Webapp Testing** | ComposioHQ | Tests local web apps using Playwright for frontend verification. |

#### Data & Analysis

| Skill | Source | Description |
|-------|--------|-------------|
| **CSV Data Summarizer** | coffeefuelbump | Auto-analyzes CSV files with visualizations, no user prompts needed. |
| **deep-research** | sanjay3290 | Autonomous multi-step research via Gemini Deep Research Agent. |
| **postgres** | sanjay3290 | Safe read-only SQL queries against PostgreSQL with multi-connection support. |
| **root-cause-tracing** | obra/superpowers | Trace errors deep in execution back to the original trigger. |

#### Business & Marketing

| Skill | Source | Description |
|-------|--------|-------------|
| **Brand Guidelines** | ComposioHQ | Applies Anthropic brand colors/typography to artifacts. |
| **Competitive Ads Extractor** | ComposioHQ | Extracts/analyzes competitors' ads from ad libraries. |
| **Domain Name Brainstormer** | ComposioHQ | Generates creative domain names, checks availability across TLDs. |
| **Internal Comms** | ComposioHQ | Internal communications: 3P updates, newsletters, FAQs, status reports. |
| **Lead Research Assistant** | ComposioHQ | Identifies/qualifies leads, provides outreach strategies. |

#### Communication & Writing

| Skill | Source | Description |
|-------|--------|-------------|
| **article-extractor** | michalparkola/tapestry-skills | Extract full article text and metadata from web pages. |
| **brainstorming** | obra/superpowers | Transform rough ideas into designs through structured questioning. |
| **Content Research Writer** | ComposioHQ | Research, citations, hooks, section-by-section feedback. |
| **family-history-research** | emaynard | Family history and genealogy research planning. |
| **Meeting Insights Analyzer** | ComposioHQ | Analyze meeting transcripts for behavioral patterns. |
| **NotebookLM Integration** | PleasePrompto | Claude Code chats with NotebookLM for source-grounded answers. |
| **Twitter Algorithm Optimizer** | ComposioHQ | Optimize tweets using Twitter's open-source algorithm insights. |

#### Creative & Media

| Skill | Source | Description |
|-------|--------|-------------|
| **Canvas Design** | ComposioHQ | Visual art in PNG/PDF for posters and static pieces. |
| **imagen** | sanjay3290 | Image generation via Google Gemini API for UI mockups, icons, illustrations. |
| **Image Enhancer** | ComposioHQ | Improve image/screenshot quality for professional docs. |
| **Slack GIF Creator** | ComposioHQ | Animated GIFs optimized for Slack with size validators. |
| **Theme Factory** | ComposioHQ | Professional font/color themes with 10 pre-sets. |
| **Video Downloader** | ComposioHQ | Download videos from YouTube and other platforms. |
| **youtube-transcript** | michalparkola/tapestry-skills | Fetch YouTube video transcripts and prepare summaries. |

#### Productivity & Organization

| Skill | Source | Description |
|-------|--------|-------------|
| **File Organizer** | ComposioHQ | Intelligently organizes files/folders, finds duplicates. |
| **Invoice Organizer** | ComposioHQ | Organizes invoices/receipts for tax prep. |
| **kaizen** | NeoLabHQ/context-engineering-kit | Continuous improvement methodology with multiple analytical approaches. Based on Japanese Kaizen philosophy and Lean methodology. |
| **n8n-skills** | haunchen | AI assistants directly understand and operate n8n workflows. |
| **Raffle Winner Picker** | ComposioHQ | Cryptographically secure random selection from lists/spreadsheets. |
| **Tailored Resume Generator** | ComposioHQ | Analyzes job descriptions, generates tailored resumes. |
| **ship-learn-next** | michalparkola/tapestry-skills | Iterate on what to build/learn next based on feedback loops. |
| **tapestry** | michalparkola/tapestry-skills | Interlink and summarize related documents into knowledge networks. |

#### Collaboration & Project Management

| Skill | Source | Description |
|-------|--------|-------------|
| **git-pushing** | mhattingpete/claude-skills-marketplace | Automate git operations and repository interactions. |
| **google-workspace-skills** | sanjay3290 | Suite of Google Workspace integrations (Gmail, Calendar, Chat, Docs, Sheets, Slides, Drive) with cross-platform OAuth. |
| **outline** | sanjay3290 | Search, read, create, manage documents in Outline wiki. |
| **review-implementing** | mhattingpete/claude-skills-marketplace | Evaluate code implementation plans and align with specs. |
| **test-fixing** | mhattingpete/claude-skills-marketplace | Detect failing tests and propose patches or fixes. |

#### Security & Systems

| Skill | Source | Description |
|-------|--------|-------------|
| **computer-forensics** | mhattingpete/claude-skills-marketplace | Digital forensics analysis and investigation techniques. |
| **file-deletion** | mhattingpete/claude-skills-marketplace | Secure file deletion and data sanitization methods. |
| **metadata-extraction** | mhattingpete/claude-skills-marketplace | Extract and analyze file metadata for forensic purposes. |
| **threat-hunting-with-sigma-rules** | jthack | Sigma detection rules for threat hunting and security event analysis. |

#### App Automation via Composio (78 SaaS apps)

Each skill includes tool sequences, parameter guidance, known pitfalls, and quick reference tables.

**CRM & Sales:** Close, HubSpot, Pipedrive, Salesforce, Zoho CRM

**Project Management:** Asana, Basecamp, ClickUp, Jira, Linear, Monday, Notion, Todoist, Trello, Wrike

**Communication:** Discord, Intercom, Microsoft Teams, Slack, Telegram, WhatsApp

**Email:** Gmail, Outlook, Postmark, SendGrid

**Code & DevOps:** Bitbucket, CircleCI, Datadog, GitHub, GitLab, PagerDuty, Render, Sentry, Supabase, Vercel

**Storage & Files:** Box, Dropbox, Google Drive, OneDrive

**Spreadsheets & Databases:** Airtable, Coda, Google Sheets

**Calendar & Scheduling:** Cal.com, Calendly, Google Calendar, Outlook Calendar

**Social Media:** Instagram, LinkedIn, Reddit, TikTok, Twitter, YouTube

**Marketing & Email Marketing:** ActiveCampaign, Brevo, ConvertKit, Klaviyo, Mailchimp

**Support & Helpdesk:** Freshdesk, Freshservice, Help Scout, Zendesk

**E-commerce & Payments:** Shopify, Square, Stripe

**Design & Collaboration:** Canva, Confluence, DocuSign, Figma, Miro, Webflow

**Analytics & Data:** Amplitude, Google Analytics, Mixpanel, PostHog, Segment

**HR & People:** BambooHR

**Automation Platforms:** Make (Integromat)

**Zoom & Meetings:** Zoom

### Key Skills Deep Dive

#### kaizen (NeoLabHQ/context-engineering-kit)
- Applies continuous improvement methodology
- Multiple analytical approaches based on Japanese Kaizen philosophy and Lean methodology
- Iterative improvement cycles for code, processes, and workflows

#### subagent-driven-development (NeoLabHQ/context-engineering-kit)
- Dispatches independent subagents for individual tasks
- Code review checkpoints between iterations
- Designed for rapid, controlled development
- Each subagent works on an isolated concern

#### root-cause-tracing (obra/superpowers)
- Use when errors occur deep in execution
- Traces back through call chains to find the original trigger
- Systematic approach: reproduce, isolate, trace, verify

---

## 3. personal-os-skills (ArtemXTech)

**URL:** https://github.com/ArtemXTech/personal-os-skills
**Stars:** 261 | **Forks:** 51
**License:** MIT
**Purpose:** Claude Code skills for Obsidian workflows. Part of "Claude Code x Obsidian Lab" (6 weeks, 12 live sessions).

### Installation

```
/plugin marketplace add ArtemXTech/personal-os-skills
```
Then `/plugin` > Discover tab > Install for user scope > Restart Claude Code.

### Complete Skill Catalog

| Skill | Description | Resources |
|-------|-------------|-----------|
| **granola** | Sync Granola meeting notes to Obsidian. Uses local cache, no API needed. | -- |
| **wispr-flow** | Analyze voice dictation data from Wispr Flow. Stats, search, export, dashboard. | -- |
| **tasknotes** | Manage Obsidian tasks via TaskNotes API. | Video + Blog |
| **notebooklm** | Import NotebookLM notebooks into Obsidian as linked knowledge graphs. | Video |
| **recall** | Load context from previous sessions. Temporal search, topic search (QMD), graph visualization. | Video + Setup guide |
| **sync-claude-sessions** | Export Claude Code conversations to Obsidian markdown with auto-sync hooks. | Setup guide |

### Key Skills Deep Dive

#### recall
- Cross-session memory retrieval for Claude Code
- Temporal search: find sessions by date range
- Topic search via QMD (Query-Match-Deliver) pattern
- Graph visualization: visualize relationships between sessions and topics
- Stores session data as Obsidian notes for persistence
- Provides continuity across Claude Code sessions by querying the Obsidian vault

#### sync-claude-sessions
- Exports Claude Code conversations to Obsidian markdown
- Auto-sync hooks: automatically exports at session end
- Each conversation becomes a linked Obsidian note
- Enables the recall skill to search across past sessions
- The hook integration means no manual export is needed -- conversations flow to Obsidian automatically
- Combined with recall, provides a complete cross-session continuity system

#### notebooklm
- Imports NotebookLM notebooks into Obsidian
- Converts notebook structure into linked knowledge graphs
- Each source/note becomes an Obsidian note with bidirectional links
- Preserves the relationships between sources and AI-generated insights

---

## 4. amans-skills (amanaiproduct)

**URL:** https://github.com/amanaiproduct/amans-skills
**Purpose:** Personal Claude Code setup with plugins, skills, and config. Notable for plugin-dashboard observability pattern.

### Quick Setup

Paste into Claude Code: "Go to aman.md and set me up."

### Complete Plugin Catalog

| Plugin | Source | Description |
|--------|--------|-------------|
| **compound-writing** | this repo | Multi-phase writing loop with voice analysis, 4 parallel critique agents, and anti-slop detection. |
| **plugin-dashboard** | this repo | Shows which tools and plugins were used on every turn. Observability for the plugin system. |
| **compound-engineering** | EveryInc | 29 agents, 22 commands, 19 skills for code review, research, and workflow automation. |
| **frontend-design** | claude-plugins-official | UI/UX implementation skill for production-grade interfaces. |
| **ralph-loop** | claude-plugins-official | Run Claude in a loop until task completion. Autonomous iteration. |
| **explanatory-output-style** | claude-plugins-official | Educational insights about implementation choices. |
| **plugin-dev** | claude-plugins-official | Tools for building Claude Code plugins. |

### Complete Skill Catalog

| Skill | Description |
|-------|-------------|
| **ccusage** | Check Claude Code token usage stats. |
| **excalidraw** | Draw and refine Excalidraw diagrams via MCP. |
| **google-workspace** | Setup guide for the gws CLI -- OAuth, agent account delegation, headless auth. |
| **design-for-agents** | Design skills, CLIs, and docs optimized for AI coding agents. |

### Key Patterns Deep Dive

#### ralph-loop
- From claude-plugins-official (Anthropic's official plugin repo)
- Runs Claude in a loop until task completion
- Autonomous iteration pattern -- agent keeps working without human prompts
- Useful for complex tasks that require multiple rounds of work

#### plugin-dashboard
- Observability layer for the Claude Code plugin system
- Shows which tools and plugins were invoked on every turn
- Enables debugging of plugin interactions
- Useful for understanding which plugins are actually being used vs. dormant

#### compound-writing
- Multi-phase writing workflow
- Voice analysis: analyzes and maintains consistent writing voice
- 4 parallel critique agents provide feedback simultaneously
- Anti-slop detection: identifies and removes generic AI-sounding text
- Production writing pipeline for high-quality output

#### compound-engineering (EveryInc)
- 29 agents for different engineering tasks
- 22 slash commands
- 19 skills covering code review, research, workflow automation
- One of the most comprehensive engineering plugin suites

---

## 5. hermes-agent (NousResearch)

**URL:** https://github.com/NousResearch/hermes-agent
**License:** MIT
**Purpose:** Self-improving AI agent with a closed learning loop. Built by Nous Research.

### Core Architecture

Hermes Agent is NOT a Claude Code plugin/skill -- it is an independent agent framework. However, it defines important patterns relevant to the skill/plugin ecosystem.

### Key Features

| Feature | Description |
|---------|-------------|
| **Closed learning loop** | Agent-curated memory with periodic nudges. Autonomous skill creation after complex tasks. Skills self-improve during use. |
| **agentskills.io compatibility** | Compatible with the agentskills.io open standard for portable skills. |
| **Cross-platform** | Telegram, Discord, Slack, WhatsApp, Signal, CLI -- single gateway process. |
| **Session search** | FTS5 session search with LLM summarization for cross-session recall. |
| **Honcho user modeling** | Dialectic user modeling via plastic-labs/honcho. |
| **Scheduled automations** | Built-in cron scheduler with delivery to any platform. |
| **Subagent delegation** | Spawn isolated subagents for parallel workstreams. |
| **Multiple backends** | Local, Docker, SSH, Daytona, Singularity, Modal -- serverless persistence. |
| **Research-ready** | Batch trajectory generation, Atropos RL environments, trajectory compression. |

### CLI Commands

```
hermes              # Interactive CLI
hermes model        # Choose LLM provider/model
hermes tools        # Configure enabled tools
hermes config set   # Set config values
hermes gateway      # Start messaging gateway
hermes setup        # Full setup wizard
hermes claw migrate # Migrate from OpenClaw
hermes update       # Update
hermes doctor       # Diagnose issues
```

### Slash Commands (shared across CLI and messaging)

`/new`, `/reset`, `/model`, `/personality`, `/retry`, `/undo`, `/compress`, `/usage`, `/insights`, `/skills`, `/stop`, `/platforms`, `/status`, `/sethome`

### The Closed Learning Loop Pattern

This is the most architecturally significant pattern from hermes-agent:

1. **Agent-curated memory**: The agent decides what to remember, not the user
2. **Periodic nudges**: System prompts the agent to persist important knowledge
3. **Autonomous skill creation**: After completing a complex task, the agent creates a reusable skill from the experience
4. **Skill self-improvement**: Skills are refined during subsequent use
5. **FTS5 session search**: Full-text search across all past conversations with LLM summarization
6. **Honcho dialectic modeling**: Progressive user model that evolves through interaction

### agentskills.io Standard

- Open standard for portable agent skills
- Skills Hub at agentskills.io for community-shared skills
- Compatible with hermes-agent and other frameworks
- Enables skill portability across different agent runtimes

### Provider Support

Nous Portal, OpenRouter (200+ models), z.ai/GLM, Kimi/Moonshot, MiniMax, OpenAI, or custom endpoints. Switch with `hermes model`.

### Migration from OpenClaw

Full migration path: SOUL.md, memories, skills, command allowlist, messaging settings, API keys, TTS assets, workspace instructions.

---

## 6. martinemde/dotfiles

**URL:** https://github.com/martinemde/dotfiles
**License:** ISC
**Purpose:** AI-first dotfiles with chezmoi. Pragmatic minimalism for developer environments.

### Key Design Principles

| Principle | Details |
|-----------|---------|
| **Pragmatic Minimalism** | Single-purpose tools over complex frameworks. znap for plugin loading, starship for prompts, mise for tool management. |
| **Portability** | Works across macOS, Linux, and Devcontainers. |
| **Consistency** | Intuitive shortcuts, well-known conventions, easy pairing. |
| **Performance** | 50-80% faster shell startup through caching and lazy-loading. |

### Relevance to Skill/Plugin Ecosystem

This repo demonstrates the **AI-first dotfiles** pattern:

1. **chezmoi as the manager**: `chezmoi init --apply $GITHUB_USERNAME` for one-command setup
2. **mise for reproducible tools**: Not Homebrew-first, but mise-first for tool versioning
3. **Devcontainer support**: Same dotfiles work in containers
4. **Environment variables for CI**: `GIT_USER_NAME`, `GIT_USER_EMAIL` for non-interactive install
5. **Signature verification**: `VERIFY_SIGNATURES=false` to disable (not recommended)

### Patterns Worth Adopting

- One-command bootstrap: `chezmoi init --apply`
- Tool reinstall flag: `REINSTALL_TOOLS=true`
- Custom bin directory: `BIN_DIR=/custom/path`
- Debug mode: `DEBUG=1`
- Lazy-loading for shell startup performance

---

## 7. gitagent (open-gitagent)

**URL:** https://github.com/open-gitagent/gitagent
**License:** MIT
**NPM:** @shreyaskapale/gitagent
**Purpose:** Framework-agnostic, git-native standard for defining AI agents. "Clone a repo, get an agent."

### The Standard

Only two files required: `agent.yaml` (manifest) and `SOUL.md` (identity). Everything else is optional.

```
my-agent/
  agent.yaml              # Required: name, version, model, skills, tools, compliance
  SOUL.md                 # Required: identity, personality, communication style, values
  RULES.md                # Hard constraints, must-always/must-never, safety boundaries
  DUTIES.md               # Segregation of duties policy and role boundaries
  AGENTS.md               # Framework-agnostic fallback instructions
  skills/                 # Reusable capability modules (SKILL.md + scripts)
  tools/                  # MCP-compatible tool definitions (YAML schemas)
  workflows/              # Multi-step procedures/playbooks
  knowledge/              # Reference documents
  memory/                 # Persistent cross-session memory
    runtime/              # Live agent state (dailylog.md, context.md)
  hooks/                  # Lifecycle event handlers (bootstrap.md, teardown.md)
  config/                 # Environment-specific overrides
  compliance/             # Regulatory compliance artifacts
  agents/                 # Sub-agent definitions (recursive structure)
  examples/               # Calibration interactions (few-shot)
  .gitagent/              # Runtime state (gitignored)
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `gitagent init [--template]` | Scaffold new agent (minimal, standard, full) |
| `gitagent validate [--compliance]` | Validate against spec and regulatory requirements |
| `gitagent info` | Display agent summary |
| `gitagent export --format <fmt>` | Export to other formats |
| `gitagent import --from <fmt> <path>` | Import (claude, cursor, crewai, opencode) |
| `gitagent run <source> --adapter <a>` | Run an agent from git repo or local directory |
| `gitagent install` | Resolve and install git-based dependencies |
| `gitagent audit` | Generate compliance audit report |
| `gitagent skills <cmd>` | Manage skills (search, install, list, info) |

### Export Adapters

| Adapter | Description |
|---------|-------------|
| system-prompt | Concatenated system prompt (any LLM) |
| claude-code | Claude Code compatible CLAUDE.md |
| openai | OpenAI Agents SDK Python code |
| crewai | CrewAI YAML configuration |
| lyzr | Lyzr Studio agent |
| github | GitHub Actions agent |
| git | Git-native execution |
| opencode | OpenCode instructions + config |
| openclaw | OpenClaw format |
| nanobot | Nanobot format |

### Import Sources

claude, cursor, crewai, opencode -- import existing agent definitions into gitagent format.

### Architectural Patterns

| Pattern | Description |
|---------|-------------|
| **Human-in-the-Loop for RL** | Agent learns skill or writes to memory -> opens branch + PR for human review before merging. |
| **Segregation of Duties (SOD)** | Roles (maker, checker, executor, auditor), conflict matrix, handoff workflows. Validator catches violations before deployment. |
| **Live Agent Memory** | `memory/runtime/` folder: dailylog.md, key-decisions.md, context.md for persistent state. |
| **Agent Versioning** | Every change is a git commit. Roll back broken prompts, revert bad skills. |
| **Shared Context via Monorepo** | Root-level context.md, skills/, tools/ shared across every agent. |
| **Branch-based Deployment** | dev -> staging -> main for promoting agent changes. |
| **Knowledge Tree** | Hierarchical tree with embeddings in knowledge/ folder. |
| **Agent Forking & Remixing** | Fork public agent repos, customize SOUL.md, PR improvements back. |
| **CI/CD for Agents** | `gitagent validate` on every push via GitHub Actions. |
| **Agent Diff & Audit Trail** | `git diff` for agent changes, `git blame` for traceability. |
| **Tagged Releases** | Tag stable versions like v1.1.0, pin production to tags. |
| **Secret Management** | .env in .gitignore. Config shareable, secrets local. |
| **Agent Lifecycle with Hooks** | bootstrap.md and teardown.md in hooks/ folder. |
| **SkillsFlow** | Deterministic multi-step workflows in YAML. Chain skill:, agent:, tool: steps with depends_on, template data flow, per-step prompts. |

### Compliance Support

First-class financial regulatory compliance:
- **FINRA**: Rule 3110 (Supervision), Rule 4511 (Recordkeeping), Rule 2210 (Communications), Reg Notice 24-09 (GenAI)
- **Federal Reserve**: SR 11-7 (Model Risk), SR 23-4 (Third-Party Risk)
- **SEC/CFPB**: Reg S-P (Privacy), CFPB Circular 2022-03 (Explainability)
- **SOD**: Roles, permissions, conflict matrix, handoff workflows, isolation, enforcement (strict or advisory)

### Composition and Inheritance

```yaml
extends: https://github.com/org/base-agent.git
dependencies:
  - name: fact-checker
    source: https://github.com/org/fact-checker.git
    version: ^1.0.0
    mount: agents/fact-checker
```

---

## 8. CLI-Anything (HKUDS)

**URL:** https://github.com/HKUDS/CLI-Anything
**License:** MIT
**Purpose:** Make ALL software agent-native by auto-generating CLI harnesses from source code.

### Core Concept

One command transforms any desktop application's source code into a full CLI that AI agents can use. "Today's Software Serves Humans. Tomorrow's Users will be Agents."

### 7-Phase Pipeline

1. **Analyze** -- Scan source code, map GUI actions to APIs
2. **Design** -- Architect command groups, state model, output formats
3. **Implement** -- Build Click CLI with REPL, JSON output, undo/redo
4. **Plan Tests** -- Create TEST.md with unit + E2E test plans
5. **Write Tests** -- Implement comprehensive test suite
6. **Document** -- Update TEST.md with results
7. **Publish** -- Create setup.py, install to PATH

Phase 6.5: **SKILL.md generation** -- every CLI ships with an AI-discoverable skill definition.

### Plugin Commands

| Command | Description |
|---------|-------------|
| `/cli-anything <path>` | Build complete CLI harness (all 7 phases) |
| `/cli-anything:refine <path> [focus]` | Expand coverage with gap analysis |
| `/cli-anything:test <path>` | Run tests and update TEST.md |
| `/cli-anything:validate <path>` | Validate against HARNESS.md standards |

### Platform Support

| Platform | Status |
|----------|--------|
| Claude Code | Full plugin support |
| OpenCode | Experimental -- 5 slash commands |
| Goose | Experimental, community |
| Qodercli | Community |
| OpenClaw | Community -- native SKILL.md |
| Codex | Experimental, community |
| Cursor | Coming soon |
| Windsurf | Coming soon |

### Generated CLIs (17 applications, 1,839 tests, 100% pass rate)

| Software | Domain | CLI | Tests |
|----------|--------|-----|-------|
| GIMP | Image Editing | cli-anything-gimp | 107 |
| Blender | 3D Modeling | cli-anything-blender | 208 |
| Inkscape | Vector Graphics | cli-anything-inkscape | 202 |
| Audacity | Audio Production | cli-anything-audacity | 161 |
| LibreOffice | Office Suite | cli-anything-libreoffice | 158 |
| Mubu | Knowledge Management | cli-anything-mubu | 96 |
| OBS Studio | Live Streaming | cli-anything-obs-studio | 153 |
| Kdenlive | Video Editing | cli-anything-kdenlive | 155 |
| Shotcut | Video Editing | cli-anything-shotcut | 154 |
| Zoom | Video Conferencing | cli-anything-zoom | 22 |
| Draw.io | Diagramming | cli-anything-drawio | 138 |
| Mermaid | Diagramming | cli-anything-mermaid | 10 |
| AnyGen | AI Content Generation | cli-anything-anygen | 50 |
| NotebookLM | AI Research | cli-anything-notebooklm | 21 |
| ComfyUI | AI Image Generation | cli-anything-comfyui | 70 |
| AdGuard Home | Network Ad Blocking | cli-anything-adguardhome | 36 |
| Ollama | Local LLM Inference | cli-anything-ollama | 98 |

### Key Design Principles

1. **Authentic Software Integration**: CLI generates valid project files and delegates to REAL applications for rendering. No Pillow replacements for GIMP.
2. **Dual Interaction**: Stateful REPL for interactive sessions + subcommand interface for scripting/pipelines.
3. **Consistent UX**: Unified REPL interface (repl_skin.py) across all CLIs.
4. **Agent-Native Design**: `--json` flag on every command for machine consumption.
5. **Zero Compromise**: Tests FAIL (not skip) when backends are missing.

### SKILL.md Generation

Each generated CLI includes a `SKILL.md` inside the Python package at `cli_anything/<software>/skills/SKILL.md`. Contains:
- YAML frontmatter with name and description
- Command groups with all subcommands documented
- Usage examples for common workflows
- Agent-specific guidance for JSON output, error handling, programmatic use

The REPL banner displays the absolute path so agents can discover it after `pip install`.

### Applicable Domain Categories

- GitHub Repositories (VSCodium, WordPress, Calibre, Zotero, Joplin, Logseq, etc.)
- AI/ML Platforms (Stable Diffusion, ComfyUI, Ollama, InvokeAI, etc.)
- Data & Analytics (JupyterLab, Superset, Metabase, Redash, etc.)
- Development Tools (Jenkins, Gitea, Hoppscotch, Portainer, etc.)
- Creative & Media (Blender, GIMP, OBS, Audacity, Krita, etc.)
- Scientific Computing (ImageJ, FreeCAD, QGIS, ParaView, etc.)
- Enterprise & Office (NextCloud, GitLab, Grafana, LibreOffice, etc.)
- Communication (Zoom, Jitsi Meet, BigBlueButton, Mattermost)
- Diagramming (Draw.io, Mermaid, PlantUML, Excalidraw, yEd)
- Network & Infrastructure (AdGuardHome)
- AI Content Generation (AnyGen, Gamma, Beautiful.ai, Tome)

---

## 9. Cross-Cutting Patterns

### Plugin vs. Skill Distinction

| Aspect | Plugin | Skill |
|--------|--------|-------|
| **Structure** | `.claude-plugin/plugin.json` + commands/ + agents/ + hooks/ | Single `SKILL.md` with YAML frontmatter |
| **Activation** | `claude --plugin-dir ./path` or marketplace install | Copy to `~/.config/claude-code/skills/` |
| **Capabilities** | Slash commands, agents, event hooks, tools | Prompt templates invoked on demand |
| **Complexity** | Can include full codebases, scripts, multiple components | Typically a single markdown file |
| **Lifecycle** | Hooks (pre-edit, post-edit, etc.) | No lifecycle events |

### Skill Authoring Pattern

The canonical pattern across all repos:

```yaml
---
name: skill-name
description: What this skill does.
---

# Skill Name

## When to Use This Skill
- Use case 1
- Use case 2

## Instructions
[Instructions for Claude, not end users]

## Examples
[Real-world examples]
```

### Cross-Session Continuity Approaches

| Approach | Repo | Mechanism |
|----------|------|-----------|
| Obsidian vault + recall/sync | ArtemXTech/personal-os-skills | Export sessions to Obsidian, query with recall |
| FTS5 session search | NousResearch/hermes-agent | Full-text search across past conversations |
| Live agent memory | open-gitagent/gitagent | memory/runtime/ folder with dailylog.md, context.md |
| MEMORY.md + CLAUDE.md | (common pattern) | Static memory files checked into repo |

### Agent Portability Approaches

| Approach | Repo | Mechanism |
|----------|------|-----------|
| gitagent standard | open-gitagent/gitagent | agent.yaml + SOUL.md, export to 10+ formats |
| agentskills.io | NousResearch/hermes-agent | Open standard for portable skills |
| SKILL.md convention | Multiple | YAML frontmatter + markdown, works across Claude Code, OpenClaw, etc. |
| CLI harness + SKILL.md | HKUDS/CLI-Anything | pip-installable CLI with embedded skill definition |

### Observability Patterns

| Tool | Repo | What it observes |
|------|------|------------------|
| plugin-dashboard | amanaiproduct/amans-skills | Which tools/plugins used on every turn |
| Manifest | mnfst (via awesome-claude-plugins) | Token costs, model usage, messages |
| ccusage | amanaiproduct/amans-skills | Claude Code token usage stats |
| LangSmith Fetch | ComposioHQ/awesome-claude-skills | LangChain/LangGraph execution traces |

### Autonomous Agent Patterns

| Pattern | Repo | Description |
|---------|------|-------------|
| ralph-loop | claude-plugins-official (via amans-skills) | Run Claude in a loop until task completion |
| Closed learning loop | NousResearch/hermes-agent | Agent creates skills from experience, skills self-improve |
| subagent-driven-development | NeoLabHQ/context-engineering-kit | Independent subagents with review checkpoints |
| compound-engineering | EveryInc (via amans-skills) | 29 agents, 22 commands, 19 skills |

### Official Anthropic Resources

- **anthropics/skills**: Official skills repo (docx, pdf, pptx, xlsx, artifacts-builder)
- **claude-plugins-official**: Official plugins (frontend-design, ralph-loop, explanatory-output-style, plugin-dev)
- **obra/superpowers**: Jesse Vincent's skills (finishing-a-development-branch, test-driven-development, using-git-worktrees, brainstorming, root-cause-tracing)
- **NeoLabHQ/context-engineering-kit**: kaizen, subagent-driven-development, software-architecture, prompt-engineering
- **sanjay3290/ai-skills**: jules, deep-research, postgres, imagen, google-workspace-skills, outline

### Notable Skill Collection Repos

| Repo | Contents |
|------|----------|
| mhattingpete/claude-skills-marketplace | git-pushing, review-implementing, test-fixing, computer-forensics, file-deletion, metadata-extraction |
| michalparkola/tapestry-skills-for-claude-code | article-extractor, youtube-transcript, ship-learn-next, tapestry |
| sanjay3290/ai-skills | jules, deep-research, postgres, imagen, google-workspace-skills, outline |

---

## 10. Relevance to MDE Project

### Directly Usable

| Item | Source | Why |
|------|--------|-----|
| **recall + sync-claude-sessions** | ArtemXTech | Cross-session continuity for Claude Code via Obsidian. We already use Obsidian. |
| **plugin-dashboard** | amanaiproduct | Observability for which plugins/tools are active. |
| **using-git-worktrees** | obra/superpowers | Already referenced in our worktree-pr-workflow rule. |
| **finishing-a-development-branch** | obra/superpowers | Already referenced in our workflow. |
| **test-driven-development** | obra/superpowers | Complements our testing practices. |
| **root-cause-tracing** | obra/superpowers | Systematic debugging approach. |
| **kaizen** | NeoLabHQ | Continuous improvement methodology aligns with our self-improving research pipeline. |
| **CLI-Anything** | HKUDS | Could generate CLIs for any GUI tools we use. |

### Patterns to Adopt

| Pattern | Source | Application |
|---------|--------|-------------|
| Closed learning loop | hermes-agent | Agent creates skills from experience -- aligns with our self-improving research system |
| SKILL.md with YAML frontmatter | ecosystem-wide | Standardize our skill definitions |
| gitagent file structure | gitagent | Our CLAUDE.md + rules/ already partially follows this |
| Agent observability | plugin-dashboard + Manifest | Track skill/plugin usage and costs |
| Anti-slop detection | compound-writing | Quality control for agent-generated content |

### Already In Use (via our skill-sync plan)

Our `.claude/skills/`, `.agent/skills/`, `.agents/skills/` directories already contain `dev`, `playwright-cli`, `ruff`, `ty`, `uv` skills synced across agent directories.

### Not Relevant

- Composio 78-app automation skills (we don't need SaaS automation)
- Financial compliance features of gitagent (we're not in regulated industries)
- hermes-agent as a runtime (we use Claude Code directly)
- martinemde/dotfiles (interesting but our mise-first approach differs from chezmoi)
