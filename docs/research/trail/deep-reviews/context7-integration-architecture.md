# Context7 Integration Architecture for Claude Code

> Deep review of Context7's three integration layers (MCP server, plugin, CLI skills),
> their overlap, and the mise-managed ctx7 CLI setup.
> Sources: github.com/upstash/context7, context7 marketplace plugin cache,
> ~/.claude/ global config, configs/mcp-servers.mcp.json.
> Reviewed: 2026-03-23.

## Table of Contents

1. [Integration Layers Overview](#integration-layers-overview)
2. [Layer 1: MCP Server](#layer-1-mcp-server)
3. [Layer 2: Claude Code Plugin](#layer-2-claude-code-plugin)
4. [Layer 3: Standalone CLI Skills](#layer-3-standalone-cli-skills)
5. [Overlap Analysis](#overlap-analysis)
6. [Setup Completed](#setup-completed)
7. [Key Architectural Decisions](#key-architectural-decisions)

---

## Integration Layers Overview

Context7 provides three distinct integration paths for Claude Code, each with
different capabilities and trade-offs:

| Layer | Mechanism | What It Provides | Installed? |
|-------|-----------|-----------------|------------|
| MCP Server | `@upstash/context7-mcp` via stdio | `resolve-library-id` + `query-docs` MCP tools | Yes (pre-existing) |
| Plugin | `context7-plugin` from marketplace | MCP skill + `/docs` command + `docs-researcher` agent | Yes (pre-existing) |
| CLI Skills | `ctx7` binary (mise-managed) | `context7-cli` + `find-docs` skills | Yes (newly installed) |

## Layer 1: MCP Server

**Config chain:** `configs/mcp-servers.mcp.json` → `scripts/mcp/mde-mcp-context7`
→ `mde_mcp_run_node_tool "@upstash/context7-mcp"` → `~/.claude.json` (global MCP config)

The MCP server exposes two tools to Claude:

- **`resolve-library-id`** — takes `libraryName` + `query`, returns ranked matches
  with library IDs (format: `/org/project`), benchmark scores, and version lists.
- **`query-docs`** — takes `libraryId` + `query`, returns code snippets and info
  snippets from indexed documentation.

**Setup path:** `scripts/setup-mcp-servers.sh` reads `configs/mcp-servers.mcp.json`,
normalizes via Python, symlinks wrappers to `~/.local/bin/`, and writes to
`~/Library/Application Support/Claude/claude_desktop_config.json` (Claude Desktop)
and `~/.claude.json` (Claude Code).

The wrapper script (`scripts/mcp/mde-mcp-context7`) sources `mde-mcp-common.sh`
for secret loading and delegates to `mde_mcp_run_node_tool`.

## Layer 2: Claude Code Plugin

**Source:** `upstash/context7` repo at `plugins/claude/context7/`
**Installed via:** Claude Code plugin marketplace (`context7-marketplace`)
**Cache location:** `~/.claude/plugins/cache/context7-marketplace/context7-plugin/1.0.0/`

The plugin bundles:

### 2a. Skill: `context7-mcp`

Identical content (SHA `49e037db`) to the standalone `skills/context7-mcp/SKILL.md`
in the repo root. Guides Claude to use the MCP tools in a 4-step workflow:
resolve → select → fetch → use.

### 2b. Command: `/context7:docs`

Located at `commands/docs.md`. Provides a user-invocable slash command for manual
documentation queries (e.g., `/context7:docs next.js app router`).

### 2c. Agent: `docs-researcher`

Located at `agents/docs-researcher.md`. A lightweight subagent for fetching library
documentation without cluttering the main conversation context. Available as
`context7-plugin:docs-researcher` in the agent type list.

### 2d. MCP Config

The plugin's `.mcp.json` points to the hosted Context7 MCP endpoint:
```json
{
  "context7": {
    "url": "https://mcp.context7.com/mcp"
  }
}
```

This is a **separate MCP connection** from the local stdio server in Layer 1.
The plugin uses the hosted HTTP endpoint, while our `mde-mcp-context7` runs
the npm package locally via stdio. Both provide the same two tools.

### 2e. Global Files from `npx ctx7 setup`

Running `npx ctx7 setup --claude --yes` also installed:

- `~/.claude/rules/context7.md` — `alwaysApply: true` rule telling Claude to use
  Context7 MCP for any library/framework question. This is a global rule that
  applies to all projects.
- `~/.claude/skills/context7-mcp/SKILL.md` — duplicate of the plugin's skill,
  installed at user-global scope.

## Layer 3: Standalone CLI Skills

These skills are in the upstash/context7 repo's `skills/` directory but are
**NOT included in the plugin**. They were installed separately via:

```bash
npx ctx7 skills install /upstash/context7 context7-cli --claude
npx ctx7 skills install /upstash/context7 find-docs --claude
```

Both installed to the project's `.claude/skills/` directory.

### 3a. Skill: `context7-cli`

**Files:** `SKILL.md` + `references/docs.md` + `references/skills.md` + `references/setup.md`

Covers three CLI functions:
- **Documentation** — `ctx7 library <name> <query>` then `ctx7 docs <id> <query>`
- **Skills management** — install, search, suggest, list, remove, generate
- **Setup** — configure MCP for Claude Code / Cursor / OpenCode

Key details: library IDs require `/` prefix, `skills generate` requires login,
`CONTEXT7_API_KEY` env var skips interactive auth.

### 3b. Skill: `find-docs`

**Files:** `SKILL.md` only (self-contained, 6.3KB)

The most comprehensive docs-lookup skill. Adds over the MCP skill:
- **Query quality guidance** — good vs. bad query examples
- **Version-specific IDs** — `/org/project/version` format with selection process
- **Result field descriptions** — benchmark score, source reputation, code snippets count
- **Quota error handling** — explicit instructions for "Monthly quota reached" errors
- **Rate limiting** — max 3 attempts per question, then use best result
- **Authentication options** — `CONTEXT7_API_KEY` env var or `ctx7 login` OAuth

## Overlap Analysis

| Capability | MCP Server | Plugin | context7-cli | find-docs |
|-----------|-----------|--------|-------------|-----------|
| Resolve library ID | Tool | Skill guides tool use | CLI command | CLI command |
| Query docs | Tool | Skill guides tool use | CLI command | CLI command (rich) |
| Version-specific docs | Via tool params | Mentioned | Documented | Detailed workflow |
| Quota error handling | N/A | N/A | N/A | Explicit fallback |
| Skills management | N/A | N/A | Full CLI reference | N/A |
| Slash command | N/A | `/context7:docs` | N/A | N/A |
| Subagent | N/A | `docs-researcher` | N/A | N/A |

**Redundancy notes:**
- The MCP skill exists in 3 places: plugin, global `~/.claude/skills/`, and
  project `.claude/skills/` (if installed via ctx7). The plugin and global copies
  are identical. The project copy was not installed (we only installed cli + find-docs).
- `find-docs` and `context7-mcp` both guide docs lookup, but find-docs uses the
  CLI binary while context7-mcp uses MCP tools. find-docs is strictly more detailed.
- The local stdio MCP server and the plugin's hosted HTTP MCP endpoint both provide
  the same two tools. Claude Code may see duplicate tool names.

## Setup Completed

| Component | Status | Location |
|-----------|--------|----------|
| `npm:ctx7` in mise | Declared (pending first `mise install`) | `.chezmoisource/dot_config/mise/config.toml.tmpl` line 121 |
| `context7-cli` skill | Installed | `.claude/skills/context7-cli/` (4 files) |
| `find-docs` skill | Installed | `.claude/skills/find-docs/SKILL.md` |
| MCP server | Pre-existing | `scripts/mcp/mde-mcp-context7` → `@upstash/context7-mcp` |
| Plugin | Pre-existing | `~/.claude/plugins/cache/context7-marketplace/` |
| OAuth login | Complete | `npx ctx7 setup --claude --yes` (2026-03-23) |
| Global rule | Installed by setup | `~/.claude/rules/context7.md` (alwaysApply) |
| npx cache | Cleaned | No residual `ctx7` in `~/.npm/_npx/` |
| Provenance record | Written | `docs/research/trail/findings/finding-context7-cli-setup.yaml` |

## Key Architectural Decisions

1. **Mise ownership over npx** — ctx7 CLI declared as `"npm:ctx7" = "latest"` in
   the chezmoi-managed mise config. Uses bun backend via global
   `[settings.npm] package_manager = "bun"`. No manual npm/npx install.

2. **Project-scoped skills** — context7-cli and find-docs installed to project's
   `.claude/skills/` (git-tracked) rather than user-global `~/.claude/skills/`.
   This ensures they're shared via the repo.

3. **Complementary layers** — MCP server provides the raw tools, plugin provides
   automatic triggering + slash command + subagent, CLI skills provide detailed
   usage guidance and skills management. All three layers coexist.

4. **Duplicate MCP endpoints** — Both the local stdio server (`mde-mcp-context7`)
   and the plugin's hosted endpoint (`https://mcp.context7.com/mcp`) are active.
   This may cause duplicate tool names. Monitor for conflicts; consider disabling
   one if issues arise.
