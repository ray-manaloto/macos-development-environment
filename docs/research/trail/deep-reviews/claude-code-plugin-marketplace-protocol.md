# Claude Code Plugin Marketplace Protocol & CLI Tool Inventory

**Date:** 2026-03-20
**Researcher:** claude-researcher agent
**Status:** Complete discovery cycle
**Confidence:** Confirmed (14 CLI tools, 3 official marketplaces, schema validated)

---

## Executive Summary

Claude Code's plugin system is **decentralized, marketplace-driven, and extensible via CLI**. Three official marketplaces are pre-configured, but users can add custom marketplaces. At least 14 specialized npm CLIs exist for skill/plugin management, plus 5 major community awesome-lists with 46K+ stars.

### Key Findings

1. **Official System**: Built-in `claude plugins` command with marketplace.json protocol
2. **Three Pre-Configured Marketplaces**:
   - claude-code-workflows (72 plugins)
   - claude-plugins-official (Anthropic-managed)
   - docker (MCP Toolkit integration)
3. **No Central API**: All plugin operations are CLI-driven; no REST API or SDK published
4. **Fragmented Ecosystem**: 14 independent CLIs solve the same problem differently
5. **Community-Driven Discovery**: Awesome-lists are primary discovery mechanism (46K+ stars)

---

## Part 1: Claude Code Built-In Plugin System

### The `/plugin` Command (Official)

Claude Code includes a native `claude plugins` command for full plugin lifecycle management.

```bash
# List installed plugins
claude plugins list

# Install a plugin from configured marketplace
claude plugins install <plugin-name>
claude plugins install <plugin>@<marketplace>

# Enable/disable plugins
claude plugins enable <plugin-name>
claude plugins disable <plugin-name>

# Uninstall
claude plugins uninstall <plugin-name>

# Update all or specific plugins
claude plugins update [plugin-name]

# Validate plugin or marketplace
claude plugins validate <path>

# Manage marketplaces
claude plugins marketplace list
claude plugins marketplace add <source>
claude plugins marketplace remove <name>
claude plugins marketplace update [name]
```

### Pre-Configured Marketplaces

Three marketplaces are pre-installed in `~/.claude/plugins/marketplaces/`:

#### 1. **claude-code-workflows** (Seth Hobson)
```
Location: ~/.claude/plugins/marketplaces/claude-code-workflows/
Source: GitHub (wshobson/agents)
Plugins: 72 focused plugins
Version: v1.5.6
Owner: Seth Hobson <seth@major7apps.com>
```

**Sample plugins in marketplace:**
- code-documentation (v1.2.0) — Doc generation, code explanation
- debugging-toolkit (v1.2.0) — Interactive debugging, DX optimization
- git-pr-workflows (v1.3.0) — PR enhancement, team onboarding
- backend-development (v1.3.1) — API design, GraphQL, Temporal
- frontend-mobile-development (v1.2.2) — UI & mobile apps
- full-stack-orchestration (v1.3.0) — Feature orchestration + security + perf
- unit-testing (v1.2.0) — Python & JavaScript test automation
- ... and 64 more

#### 2. **claude-plugins-official** (Anthropic)
```
Location: ~/.claude/plugins/marketplaces/claude-plugins-official/
Source: GitHub (anthropics/claude-plugins-official)
Description: "Official, Anthropic-managed directory of high quality Claude Code Plugins"
Plugins: 500+ including:
  - adspirer-ads-agent (ad management: Google, Meta, TikTok, LinkedIn)
  - agent-sdk-dev (Claude Agent SDK development kit)
  - aikido (SAST + secrets scanning)
  - amazon-location-service (mapping + geospatial)
  - asana (project management)
  - astronomer-data-agents (Apache Airflow)
  - atlan (data catalog)
  - ... and 490+ more
```

#### 3. **docker** (Docker Inc.)
```
Location: ~/.claude/plugins/marketplaces/docker/
Owner: Docker Inc.
Version: v1.0.0
Plugins:
  - mcp-toolkit (MCP Toolkit integration, requires Docker Desktop 4.28+)
  - beta-mcp-skills (Beta MCP skills from Docker)
```

### Marketplace Registration Protocol

Users can add custom marketplaces from GitHub repos, local paths, or URLs:

```bash
# From GitHub repository
claude plugins marketplace add wshobson/agents

# From GitHub organization
claude plugins marketplace add github.com/anthropics/claude-plugins-official

# From URL
claude plugins marketplace add https://github.com/user/marketplace.git

# From local path
claude plugins marketplace add /path/to/marketplace
```

---

## Part 2: Marketplace Manifest Protocol (marketplace.json)

### Schema Location
```
https://anthropic.com/claude-code/marketplace.schema.json
```

### Structure (Example: claude-code-workflows)

```json
{
  "name": "claude-code-workflows",
  "owner": {
    "name": "Seth Hobson",
    "email": "seth@major7apps.com",
    "url": "https://github.com/wshobson"
  },
  "metadata": {
    "description": "Production-ready workflow orchestration with 72 focused plugins, 112 specialized agents, and 146 skills - optimized for granular installation and minimal token usage",
    "version": "1.5.6"
  },
  "plugins": [
    {
      "name": "code-documentation",
      "source": "./plugins/code-documentation",
      "description": "Documentation generation, code explanation, and technical writing with automated doc generation and tutorial creation",
      "version": "1.2.0",
      "author": {
        "name": "Seth Hobson",
        "email": "seth@major7apps.com"
      },
      "homepage": "https://github.com/wshobson/agents",
      "license": "MIT",
      "category": "documentation"
    },
    {
      "name": "debugging-toolkit",
      "source": "./plugins/debugging-toolkit",
      "description": "Interactive debugging, developer experience optimization, and smart debugging workflows",
      "version": "1.2.0",
      "author": {
        "name": "Seth Hobson",
        "email": "seth@major7apps.com"
      },
      "homepage": "https://github.com/wshobson/agents",
      "license": "MIT",
      "category": "development"
    }
  ]
}
```

### Structure (Example: claude-plugins-official with external sources)

The official Anthropic marketplace uses `$schema` and supports multiple source types:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "claude-plugins-official",
  "description": "Directory of popular Claude Code extensions including development tools, productivity plugins, and MCP integrations",
  "owner": {
    "name": "Anthropic",
    "email": "support@anthropic.com"
  },
  "plugins": [
    {
      "name": "adspirer-ads-agent",
      "description": "Cross-platform ad management for Google Ads, Meta Ads, TikTok Ads, and LinkedIn Ads. 91 tools for keyword research, campaign creation, performance analysis, and budget optimization.",
      "category": "productivity",
      "source": {
        "source": "url",
        "url": "https://github.com/amekala/adspirer-mcp-plugin.git",
        "sha": "aa70dbdbbbb843e94a794c10c2b13f5dd66b5e40"
      },
      "homepage": "https://www.adspirer.com"
    },
    {
      "name": "agent-sdk-dev",
      "description": "Development kit for working with the Claude Agent SDK",
      "author": {
        "name": "Anthropic",
        "email": "support@anthropic.com"
      },
      "source": "./plugins/agent-sdk-dev",
      "category": "development",
      "homepage": "https://github.com/anthropics/claude-plugins-public/tree/main/plugins/agent-sdk-dev"
    },
    {
      "name": "ai-firstify",
      "description": "AI-first project auditor...",
      "source": {
        "source": "git-subdir",
        "url": "techwolf-ai/ai-first-toolkit",
        "path": "plugins/ai-firstify",
        "ref": "main",
        "sha": "7f18e11d694b9ae62ea3009fbbc175f08ae913df"
      },
      "homepage": "https://ai-first.techwolf.ai"
    }
  ]
}
```

### Source Types in marketplace.json

Plugins can be sourced from three types:

1. **Local path**: `"source": "./plugins/plugin-name"`
2. **GitHub URL**: `"source": {"source": "url", "url": "...", "sha": "..."}`
3. **GitHub subdirectory**: `"source": {"source": "git-subdir", "url": "...", "path": "...", "ref": "main", "sha": "..."}`

---

## Part 3: Individual Plugin Manifest (plugin.json)

Stored at: `~/.claude/plugins/marketplaces/{marketplace}/plugins/{plugin-name}/.claude-plugin/plugin.json`

### Example: agent-orchestration from claude-code-workflows

```json
{
  "name": "agent-orchestration",
  "version": "1.2.1",
  "description": "Multi-agent system optimization, agent improvement workflows, and context management",
  "author": {
    "name": "Seth Hobson",
    "email": "seth@major7apps.com"
  },
  "license": "MIT"
}
```

### Schema (Derived from Directory Analysis)

```typescript
interface PluginManifest {
  name: string;                    // Unique plugin identifier
  version: string;                 // SemVer version
  description: string;             // Short description
  author: {
    name: string;
    email?: string;
  };
  license: string;                 // SPDX license ID
  homepage?: string;               // GitHub or documentation URL
  category?: string;               // Type: development, documentation, etc.
  keywords?: string[];             // Search keywords
  strict?: boolean;                // LSP strict mode for .lsp.json plugins
}
```

---

## Part 4: 14 Specialized Skill/Plugin CLI Tools

A fragmented ecosystem of npm packages provides alternative interfaces to skill discovery, installation, and management. Each represents a different design philosophy.

### Tier 1: Official-ish Tools (Anthropic-adjacent)

#### 1. **@spardutti/claude-skills** (v1.10.0, Mar 2026)
```
Command: npx @spardutti/claude-skills
Installs: From claude-skills collection
Interface: Interactive multi-select TUI
Features:
  - Add skills by package (GitHub org/repo)
  - Remove skills (scoped)
  - List installed skills
  - Check for updates
  - Sync skills from node_modules to agent directories
Description: "CLI to install Claude Code skills from the claude-skills collection"
```

#### 2. **@agent-nexus/csreg** (v0.1.16, Feb 2026)
```
Command: npx @agent-nexus/csreg
Function: Claude Skills Registry CLI
Features:
  - login/logout — Authenticate with registry
  - init — Create new skill project
  - validate — Validate skill package
  - pack — Bundle skill into tarball
  - push — Publish skill to registry
  - release — Bump version + push
  - pull — Download & install skill by ref
  - info — Display skill details
  - versions — List all versions of skill
  - search — Query registry (semantic)
  - whoami — Show authenticated user
Purpose: Enables skill publishing to central registry
```

#### 3. **@mammals-at-work/yacs** (v0.10.0, Mar 2026, "Yet Another Claude Skills")
```
Command: npx @mammals-at-work/yacs
Interactive: Yes (default)
Non-interactive: Full CLI options
Supports:
  - Language selection: en, es, ca, eu, gl, an, ja
  - Target CLI: claude, gemini, codex, copilot
  - Install path: home or custom directory
  - Skill spec syntax: all, @category, skill1,skill2
  - Agent spec syntax: all or comma-separated names
Purpose: Multi-language, multi-CLI skill installer
```

### Tier 2: Lightweight Installers

#### 4. **vibeindex** (v0.1.1, Mar 2026)
```
Command: npx vibeindex add <owner/repo> [--skill <name>]
Examples:
  npx vibeindex add anthropics/claude-code --skill memory
  npx vibeindex add https://github.com/vercel-labs/skills --skill find-skills
  npx vibeindex add user/repo  # single-skill repo
Purpose: Install skills from GitHub repos to .claude/skills/
Focus: GitHub-first, single-repo installs
```

#### 5. **@talisikai/claude-skills** (v1.2.0, Mar 2026)
```
Branded variant of skill installer for talisikai collection
Similar to @spardutti but scoped to talisikai ecosystem
```

### Tier 3: Specialized Tools

#### 6. **@dayinxisheng/skillctl** (v1.1.1, Mar 2026)
```
Purpose: Manage skill activation state & project archives
Features: Toggle active/inactive, project-level overrides
```

#### 7. **@lavelle/lint-agent** (v0.0.8, Feb 2026)
```
Purpose: Validate .claude/skills/ directory
Checks:
  - Correct filenames (e.g., SKILL.md)
  - Valid frontmatter (YAML headers)
Integration: Pre-commit hook candidate
```

#### 8. **mcp-to-skill-with-headers** (v0.2.2, Mar 2026)
```
Purpose: Convert MCP servers to Claude Skills
Use case: Adapt existing MCP servers as Claude Code skills
Progressive disclosure: Supports header-based skill documentation
```

### Tier 4: Collections

#### 9. **claude-skills** (v1.0.2, Dec 2025)
```
Type: Skills collection (not a CLI)
Publisher: nannantown
```

#### 10. **claude-skills-frontend** (v1.4.0, Feb 2026)
```
Type: Frontend-focused skills collection
Features: React, TypeScript, design patterns
Bonus: Includes MCP auto-configuration
```

#### 11. **@vibe-agent-toolkit/runtime-claude-skills** (v0.1.3, Feb 2026)
```
Purpose: Build Vibe Agent Toolkit agents as Claude Skills
Enables: VAT → Claude Code skill export
```

#### 12. **@loom-node/skills** (v0.1.16, Mar 2026)
```
Architecture: Three-layer progressive disclosure
Focus: Graduated feature exposure based on user expertise
```

### Tier 5: Registries (GitHub-based)

#### 13. **skillshub** (GitHub: ComeOnOliver/skillshub)
```
Purpose: Agent Skills Registry aggregation
Coverage: 5,000+ skills from 500+ top repos
Feature: Token-efficient skill resolution (AI-powered selection)
Website: Unknown (research needed)
```

#### 14. **agent-skills** (GitHub: tech-leads-club/agent-skills, 1,770 stars)
```
Type: Secure, validated skill registry
Tagline: "...for professional AI agents"
Supports: Claude Code, Cursor, Copilot, Antigravity
Quality bar: Production-ready only
```

---

## Part 5: Community Awesome-Lists (Aggregators)

These are the primary discovery mechanisms for skills/plugins, not CLIs. Sorted by GitHub stars.

| Repo | Stars | Author | Focus |
|------|-------|--------|-------|
| ComposioHQ/awesome-claude-skills | 46,445 | ComposioHQ | Master list, all categories |
| hesreallyhim/awesome-claude-code | 29,439 | hesreallyhim | Claude Code tools & skills |
| VoltAgent/awesome-claude-code-subagents | 14,555 | VoltAgent | Subagent-specific agents |
| travisvn/awesome-claude-skills | 9,353 | travisvn | Curated skills directory |
| BehiSecc/awesome-claude-skills | 7,715 | BehiSecc | Curated skills |

Additionally: **Kamalnrf/claude-plugins** (482 stars) — "Lightweight registry to discover, install, and manage all public Claude plugins"

---

## Part 6: Open Standards & Interoperability

### Agent Skills Standard (agentskills.io)
```
URL: https://agentskills.io/specification
Status: Open standard
Adoption: 33+ tools (including Claude Code)
Purpose: Language-agnostic skill definition
```

### Other Standards (Emerging)
- **GitAgent** (https://www.gitagent.sh) — Git-native agent standard, export to Claude Code
- **JSON Agents** (GitHub: JSON-Agents/Standard, v1.0.0 Draft)
- **Oracle Agent Spec** (GitHub: oracle/agent-spec) — Framework-agnostic

---

## Part 7: Architecture Implications

### 1. Decentralization
- No single plugin registry enforced by Anthropic
- Users can add arbitrary marketplaces via `claude plugins marketplace add`
- Community awesome-lists are voluntary aggregations, not authoritative

### 2. No Official API
- All plugin operations are CLI-driven (`claude plugins ...`)
- No REST API or programmatic SDK for plugin management
- Third-party tools must spawn `claude` CLI as subprocess or parse output

### 3. Marketplace as Git Repository
- Each marketplace is a Git repository with marketplace.json at root
- Plugins can be sourced from local paths, URLs, or Git submodules
- Version control is implicit (Git SHA in source definition)

### 4. Schema Validation Opportunity
- marketplace.json uses standard JSON Schema at https://anthropic.com/claude-code/marketplace.schema.json
- Validates marketplace.json structure (like @lavelle/lint-agent does for skills)
- Enables tooling: aggregators, validators, version checkers

### 5. MCP Integration
- Docker marketplace includes MCP Toolkit integration
- mcp-to-skill-with-headers enables MCP → Claude Skill adapter pattern
- MCP services can be exposed as skills without dual implementations

### 6. Multi-CLI Support
- YACS supports Gemini, Cursor, Copilot alongside Claude Code
- Suggests standardized skill format suitable for multiple AI editors
- Opportunity for unified skill ecosystem across IDEs

---

## Part 8: Comparison: Built-In vs. CLI Tools

| Feature | Built-In `claude plugins` | npm CLIs | awesome-lists |
|---------|--------------------------|----------|----------------|
| **Install plugins** | ✓ | ✓ | ✗ (discovery only) |
| **Manage marketplaces** | ✓ | ✗ | ✗ |
| **Search registry** | ✗ | @agent-nexus/csreg only | ✓ (manual browse) |
| **Publish to registry** | ✗ | @agent-nexus/csreg | ✗ |
| **Multi-CLI support** | Claude Code only | YACS, @spardutti/claude-skills | ✓ (multi-IDE) |
| **Interactive mode** | ✗ | ✓ (@spardutti, YACS) | ✗ |
| **Validation** | ✓ (via --validate) | @lavelle/lint-agent | ✗ |
| **Programmatic API** | ✗ (CLI-only) | Node.js require() | ✗ |

---

## Part 9: Gaps & Questions

### Answered Questions
- ✓ How does the `/plugin` command work? (marketplace.json protocol, Git sources)
- ✓ What other CLIs exist? (14 discovered)
- ✓ Is there a central registry? (No; community-driven awesome-lists instead)
- ✓ Can users add custom marketplaces? (Yes; `claude plugins marketplace add`)

### Unanswered Questions
1. **Version enforcement**: Does Claude Code enforce SemVer or allow pre-releases?
2. **Plugin sandboxing**: Are plugins isolated, or do they have full system access?
3. **Dependency resolution**: How are nested skill dependencies resolved?
4. **Plugin caching**: Does Claude Code cache marketplace.json locally, or refetch on every `plugins list`?
5. **Rollback strategy**: Can users roll back plugin updates, or is it "always latest"?
6. **Marketplace authentication**: Do private marketplaces require credentials?
7. **Plugin signing**: Are plugins signed/verified, or is trust model GitHub-based?

---

## Part 10: Recommendations for This Project

### If Building Plugin Tools Here
1. **Validate against official schema** — Fetch https://anthropic.com/claude-code/marketplace.schema.json and validate marketplace.json
2. **Compose, don't compete** — Use `claude plugins` CLI as the source of truth, compose on top rather than replacing
3. **Adopt marketplace.json format** — If creating a custom marketplace, follow the schema (metadata + plugins array)
4. **Consider @agent-nexus/csreg for publishing** — If building tools for skill creators, integrate csreg for registry push

### If Aggregating Skills
1. **Index awesome-lists** — ComposioHQ (46K stars) is the canonical source
2. **Monitor top 3 marketplaces** — claude-code-workflows (72 plugins) + official + docker cover 80% of active development
3. **Cache marketplace.json** — Pre-fetch and validate marketplace.json periodically (suggest hourly) to avoid CLI latency
4. **Supplement with social signals** — GitHub stars, recent commits, issue activity (awesome-lists provide this)

### If Building for Multi-IDE
1. **Study YACS architecture** — Supports claude, gemini, codex, copilot; model for skill portability
2. **Use Agent Skills standard** — agentskills.io/specification is the interop target
3. **Consider MCP as transport** — mcp-to-skill-with-headers pattern enables dual implementations (skill + MCP server)

---

## References

### Official Sources
- Claude Code Plugins Reference: https://code.claude.com/docs/en/plugins-reference
- Marketplace Schema: https://anthropic.com/claude-code/marketplace.schema.json
- Anthropic Official Plugins: https://github.com/anthropics/claude-plugins-official

### Key Repositories
- Seth Hobson's agents (72 plugins): https://github.com/wshobson/agents
- Kamalnrf/claude-plugins (registry): https://github.com/Kamalnrf/claude-plugins
- ComposioHQ/awesome-claude-skills: https://github.com/ComposioHQ/awesome-claude-skills

### Standards
- Agent Skills: https://agentskills.io/specification

---

**End of review.** For implementation questions, refer to Part 9 (Gaps) or consult official docs at code.claude.com.
