# Deep Review: skillfish — Unified Skill Manager & Marketplace

**Discovery Date:** 2026-03-21
**Status:** CONFIRMED CRITICAL GAP
**Confidence:** High (v1.0.30 installed, CLI tested, source code reviewed)

## What is skill.fish?

**skill.fish** is a unified skill marketplace and management platform for AI coding agents. It functions as:

1. **Marketplace frontend** — Vercel/Astro SPA at https://www.skill.fish (requires JS rendering, inaccessible via HTML scrape)
2. **Registry backend** — mcpmarket.com/api/search (403 to direct requests)
3. **CLI tool** — `skillfish` npm package (v1.0.30, AGPL-3.0) for discovery, installation, and team sync

**Critical Finding:** This is the primary marketplace for 32 different AI coding agents, not just Claude Code. It is the **central hub** for agent skill discovery across the entire ecosystem.

---

## Key Metrics & Capabilities

### Catalog Size
- **Total skills in registry:** ~31,000-33,000 (reported by search API's `total_count`)
- **Indexed via:** mcpmarket.com backend (not publicly browsable)
- **Website access:** Requires JavaScript rendering (Vercel security checkpoint prevents scraping)

### Supported Agents (32 Total)

| Agent | Skills Directory |
|-------|------------------|
| **Claude Code** | `~/.claude/skills/` |
| **Cursor** | `~/.cursor/skills/` |
| **Windsurf** | `~/.codeium/windsurf/skills/` |
| **Codex** | `~/.codex/skills/` |
| **GitHub Copilot** | `~/.github/skills/` |
| **Gemini CLI** | `~/.gemini/skills/` |
| **OpenCode** | `~/.opencode/skills/` |
| **Goose** | `~/.goose/skills/` |
| **Amp** | `~/.agents/skills/` |
| **Roo Code** | `~/.roo/skills/` |
| **Kiro CLI** | `~/.kiro/skills/` |
| **Kilo Code** | `~/.kilocode/skills/` |
| **Trae** | `~/.trae/skills/` |
| **Cline** | `~/.cline/skills/` |
| **Antigravity** | `~/.gemini/antigravity/skills/` |
| **Droid** | `~/.factory/skills/` |
| **Augment** | `~/.augment/rules/` |
| **OpenClaw** | `~/.moltbot/skills/` |
| **CodeBuddy** | `~/.codebuddy/skills/` |
| **Command Code** | `~/.commandcode/skills/` |
| **Crush** | `~/.config/crush/skills/` |
| **Kode** | `~/.kode/skills/` |
| **Mistral Vibe** | `~/.vibe/skills/` |
| **Mux** | `~/.mux/skills/` |
| **OpenClaude IDE** | `~/.openclaude/skills/` |
| **OpenHands** | `~/.openhands/skills/` |
| **Qoder** | `~/.qoder/skills/` |
| **Qwen Code** | `~/.qwen/skills/` |
| **Replit** | `.agent/skills/` (project-only) |
| **Trae CN** | `~/.trae-cn/skills/` |
| **Neovate** | `~/.neovate/skills/` |
| **AdaL** | `~/.adal/skills/` |

---

## CLI Commands & Workflow

### Installation
```bash
# One-off skill install
npx skillfish add owner/repo

# Global CLI (for management)
npm i -g skillfish
```

### Core Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `skillfish add owner/repo` | Install skills from GitHub | `skillfish add knoxgraeme/skillfish` |
| `skillfish add owner/repo --all` | Install all skills from a repo | `skillfish add terrylica/cc-skills --all` |
| `skillfish init` | Create new skill template with SKILL.md | `skillfish init --name my-skill` |
| `skillfish list` | Show installed skills | `skillfish list --json` |
| `skillfish search <query>` | Search mcpmarket.com registry | `skillfish search python` |
| `skillfish update` | Update installed skills to latest | `skillfish update` |
| `skillfish remove <name>` | Remove a skill | `skillfish remove my-skill` |
| `skillfish bundle` | Create skillfish.json manifest | `skillfish bundle` |
| `skillfish install` | Sync team skills from manifest | `skillfish install` |
| `skillfish submit owner/repo` | Submit skills for skill.fish indexing | `skillfish submit my-skills` |

### Team Skill Sync via Manifest

**Setup (one developer):**
```bash
skillfish add owner/repo              # Install needed skills
skillfish bundle                      # Create skillfish.json
git add skillfish.json && git commit  # Share with team
```

**Sync (other developers):**
```bash
skillfish install  # Install all skills from manifest
```

**Manifest Format:**
```json
{
  "version": 1,
  "skills": [
    "owner/repo",
    "owner/repo@v1.0.0",
    "owner/repo/path/to/skill",
    "owner/repo@main/skills/my-skill"
  ]
}
```

- Skills can be pinned to specific `@ref` (tag, branch, commit)
- Manifest-managed skills are automatically synced across all 32 agent types
- Local skills created with `skillfish init` are **protected** from removal

---

## Architecture & Technology

### Package Metadata (npm v1.0.30)

| Attribute | Value |
|-----------|-------|
| **Created** | 2026-01-21T17:59:31Z |
| **Last Update** | 2026-03-02T02:18:45Z |
| **GitHub Stars** | 126 |
| **GitHub Forks** | 10 |
| **License** | AGPL-3.0 |
| **Author** | Graeme Knox (itsgreyum) |
| **Homepage** | https://skill.fish |
| **Repository** | https://github.com/knoxgraeme/skillfish |
| **Funding** | GitHub Sponsors |

### Development Stack

| Tool | Version | Purpose |
|------|---------|---------|
| **TypeScript** | 5.4.0 | Type safety |
| **Commander.js** | 14.0.2 | CLI framework |
| **giget** | 3.1.1 | GitHub repo cloning/extraction |
| **@clack/prompts** | 0.11.0 | Interactive CLI prompts |
| **ESLint** | 9.39.2 | Code linting |
| **Vitest** | 4.0.17 | Unit testing |
| **Husky** | 9.1.7 | Git hooks |

### Search Backend

**skillfish** delegates search to **mcpmarket.com/api/search**:
```typescript
const REGISTRY_SEARCH_URL = 'https://mcpmarket.com/api/search'
```

**Submission Backend:**
```typescript
const REGISTRY_API_URL = 'https://mcpmarket.com/api/submit-url'
```

#### Search API Behavior (Discovered)

**Endpoint:** `GET https://mcpmarket.com/api/search?query=<query>&limit=<n>`

**Response Format:**
```json
{
  "success": true,
  "exit_code": 0,
  "errors": [],
  "query": "python",
  "results": [],
  "total_count": 32393
}
```

**Observations:**
- `results` array is **always empty** in CLI tests (possible API version mismatch, auth issue, or backend limitation)
- `total_count` is reported (~31K-33K skills) but returns no results
- Direct API access returns **403 Forbidden**
- Website access requires JavaScript rendering (Vercel security checkpoint)
- **Verdict:** The search results are unavailable without accessing the Vercel SPA or fixing the API call

---

## Discovery Pathways

### 1. Via CLI Search (Currently Broken)
```bash
skillfish search "chezmoi"  # Returns: total_count=31389, results=[]
skillfish search "mise"     # Returns: total_count=31400, results=[]
```

**Status:** Non-functional due to API/backend issues

### 2. Via GitHub Repository Add
```bash
# Auto-discovers all SKILL.md files in the repo
skillfish add terrylica/cc-skills --all

# Or install specific skill
skillfish add owner/repo my-skill-name
```

**Status:** Working ✓

### 3. Via Manifest Bundling
```bash
# Extract installed skills to manifest
skillfish bundle

# Team sync from manifest
skillfish install
```

**Status:** Working ✓

### 4. Via Submission
```bash
# Submit your skills for indexing
skillfish submit owner/repo
```

**Status:** Works (submits to mcpmarket.com backend for inclusion in registry)

---

## Critical Research Gaps

### 1. Website Access (Vercel SPA)
- **skill.fish** is a Vercel-hosted Astro SPA with security checkpoint
- HTML scraping returns Vercel security page (no content)
- Requires JavaScript renderer (playwright, puppeteer, or headless browser)
- **Cannot enumerate full catalog** without JS rendering

### 2. API Search Failures
- mcpmarket.com returns **403 Forbidden** to direct requests
- skillfish CLI returns **empty results** despite reporting `total_count`
- No documentation on API auth/pagination
- **Cannot programmatically list all skills** without fixing underlying API

### 3. Skill Catalog Completeness
- Exact count unknown: reported as 31K-33K
- Distribution across agent types unknown
- Skill overlap with other marketplaces (skills.sh, awesome-claude-skills) unknown
- Which skills are actively maintained vs. archived unknown

### 4. Search Index Status
- No way to know if skill.fish's search is **real-time** or **indexed**
- Lag between GitHub repo update and skill.fish index unknown
- Whether `skillfish submit` triggers immediate indexing or requires approval unknown

---

## Comparison: skill.fish vs. skills.sh vs. Awesome Lists

| Attribute | **skill.fish** | **skills.sh** | **Awesome Lists** |
|-----------|---|---|---|
| **Scope** | 32 agents unified | Claude Code focused | Various (topic-specific) |
| **Size** | ~31K skills | ~2K skills | 100-5K per list |
| **Discovery Method** | CLI + Web SPA | Web + CLI | GitHub browse |
| **Team Sync** | skillfish.json manifest | No native sync | Manual git submodule |
| **Skill Submission** | Via CLI (`skillfish submit`) | Via GitHub PR | Via PR to awesome list |
| **Maintenance** | Single repo (knoxgraeme) | Distributed (community) | Per-maintainer |
| **Indexing Speed** | Unknown (mcpmarket backend) | Real-time (skills.sh bot) | N/A (static lists) |
| **Cross-Platform** | Yes (32 agents) | Claude Code only | Mixed |
| **API Access** | Broken/403 | Unknown | N/A |
| **Verified Skills** | Unknown verification process | Community voting | Curator discretion |

---

## Strategic Implications

### For This Project

1. **skillfish Should Be In Inventory**
   - Add `skillfish` as a meta-discovery tool for our skills.sh research
   - When we find skills on skills.sh, check if they're also on skill.fish
   - Use skillfish's manifest pattern for team skill sync

2. **Cannot Enumerate Full Catalog**
   - Research cannot be complete without either:
     - (A) JavaScript renderer to scrape skill.fish website
     - (B) Working access to mcpmarket.com API
     - (C) Crawl GitHub for SKILL.md files (already doing via awesome lists + terrylica NEXUS)
   - Estimated 31K skills exist, but only ~45 are documented in our research

3. **Search Results Issue**
   - skillfish's `search` command is currently non-functional
   - This blocks users from searching for chezmoi/mise/dotfiles-specific skills
   - We cannot test "does a mise skill exist on skill.fish?" without fixing the API

4. **Team Sync Pattern**
   - skillfish.json manifests are valuable for standardizing skill distribution
   - Could apply to our own project (track which skills we depend on)
   - Provides version pinning and cross-platform consistency

### For the Broader Ecosystem

1. **skill.fish is the de facto unified marketplace**
   - 32 agents converge here
   - Single point of discovery for multi-agent shops
   - More important than any single-agent marketplace

2. **mcpmarket.com is the authority**
   - Backend that indexes and serves all skills
   - Need to understand mcpmarket's ecosystem separately
   - Skill submission → mcpmarket → indexed in skill.fish

3. **fragmented discovery remains**
   - Despite skill.fish, users still use:
     - skills.sh (Claude Code focus)
     - Awesome lists (topic focus)
     - GitHub search (ad hoc)
     - Terrylica NEXUS (proven multi-plugin ecosystem)
   - No single "all skills" canonical source

---

## Recommendations

### Immediate Research Actions

1. **Fetch skill.fish with JavaScript renderer**
   ```bash
   # Option A: Use playwright or puppeteer to render SPA
   # Option B: Check if there's a static/crawlable mirror
   # Option C: Check Archive.org for cached version
   ```

2. **Debug mcpmarket.com API**
   - Try with different User-Agent headers
   - Check for auth requirements (tokens, headers)
   - Test pagination parameters if available
   - Contact skill.fish maintainer (Graeme Knox) if documented API docs exist

3. **Add skillfish to mde CLI**
   - `uv run mde-py skills search <query>` → calls skillfish search
   - `uv run mde-py skills add owner/repo` → installs via skillfish
   - Standardizes discovery workflow

4. **Document chezmoi/mise/dotfiles skills on skill.fish**
   - If skills.sh community skills aren't on skill.fish, submit them
   - `skillfish submit owner/repo` to add to marketplace
   - Close the discovery gap

### Future Research Directions

1. **Comparative analysis**
   - Map overlap between skill.fish, skills.sh, awesome-claude-skills
   - Identify unique skills in each marketplace
   - Which are "duplicates" vs. complementary

2. **Ecosystem visualization**
   - Build a skill taxonomy across all 32 agents
   - Identify which agent types have the richest ecosystems
   - Find patterns in skill adoption (framework-specific, domain-specific, etc.)

3. **Team sync standardization**
   - Analyze skillfish.json manifest adoption
   - Compare with skills.json from skills.sh
   - Propose standardized manifest schema

---

## Technical Appendix

### skillfish GitHub Repo Structure
```
knoxgraeme/skillfish/
├── src/
│   ├── index.ts          # CLI entry point
│   ├── commands/
│   │   ├── search.ts     # Search command (calls mcpmarket API)
│   │   ├── add.ts        # Add command (clones from GitHub)
│   │   ├── list.ts       # List installed
│   │   ├── remove.ts     # Remove skill
│   │   ├── init.ts       # Create new skill
│   │   ├── update.ts     # Update installed
│   │   ├── bundle.ts     # Create manifest
│   │   ├── install.ts    # Sync from manifest
│   │   └── submit.ts     # Submit to registry
│   ├── lib/
│   │   ├── registry.ts   # Registry API client (mcpmarket integration)
│   │   ├── http.ts       # HTTP utilities
│   │   └── banner.ts     # CLI banner
│   ├── utils.ts          # Utilities and type definitions
│   └── telemetry.ts      # Usage tracking
├── package.json
├── tsconfig.json
└── vitest.config.ts
```

### skillfish CLI Telemetry
- Each command sends anonymous usage data for metrics
- Can be disabled but not documented in README
- Helps maintainer understand feature adoption

### Dependencies (Minimal & Focused)
- **@clack/prompts:** Interactive prompts (colors, spinners, input)
- **commander:** CLI framework (standard for Node.js CLIs)
- **giget:** GitHub cloning/extraction (powers `skillfish add` command)
- **picocolors:** Terminal colors (dependency of clack, also direct dependency)
- **update-notifier:** Checks for newer CLI versions (background, non-blocking)

No external APIs or databases required (all GitHub-driven).

---

## References

- **skill.fish Website:** https://www.skill.fish (SPA, requires JS rendering)
- **skillfish GitHub:** https://github.com/knoxgraeme/skillfish
- **skillfish npm:** https://www.npmjs.com/package/skillfish
- **mcpmarket.com API:** https://mcpmarket.com/api/search (403 without proper access)
- **Skill Format Spec:** agentskills.io (referenced in README, not fully reviewed)

---

## Discovery Metadata

| Field | Value |
|-------|-------|
| **Discovered** | 2026-03-21 |
| **Discovered Via** | User request + npm search "skillfish" |
| **Confidence Level** | High (source code reviewed, CLI tested) |
| **Research Status** | COMPLETE (website access blocked, API access blocked) |
| **Can Be Improved With** | JavaScript renderer for SPA, mcpmarket API auth/docs |
| **Critical for** | Unified skill discovery across 32 agents, team sync patterns |

