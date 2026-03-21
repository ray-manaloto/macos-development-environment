# SkillsMP Marketplace: Comprehensive Analysis

**Date**: 2026-03-21
**Status**: Discovered & Analyzed
**Confidence**: Confirmed via 10+ independent implementations
**Skill Count**: ~161K (7-8x larger than competitors)

---

## Executive Summary

SkillsMP is the **dominant AI agent skills marketplace** with ~161,000 indexed skills—the largest by a factor of 7-8x compared to alternatives (skills.sh: 22K, ClawHub: 11K). While the official website is Cloudflare-protected and minimal ("Coming Soon"), the platform is **actively maintained** through:

1. Public REST API v1 (`https://skillsmp.com/api/v1`)
2. 5+ independent MCP server implementations (Feb-Mar 2026)
3. 2+ CLI tools for skill discovery & installation
4. Aggregation into unified 180K+ skill index (skilldb)

The platform supports all major AI coding agents: Claude Code, Cursor, Claude Desktop, Codex, Opencode, Antigravity, Roo Code, GitHub Copilot.

---

## Marketplace Landscape

### Size Comparison (as of 2026-02-27)

| Platform | Skills | Ratio | Status |
|----------|--------|-------|--------|
| **SkillsMP** | ~161K | 7.3x | Dominant |
| skills.sh | ~22K | 1.0x | Smaller |
| ClawHub | ~11K | 0.5x | Smallest |
| **Deduplicated Total** | ~180K | — | Via skilldb |

**Finding**: SkillsMP contains ~89% of all indexed skills across three major platforms.

---

## How SkillsMP Works

### Architecture

```
┌─────────────────────────────────────────┐
│  skillsmp.com (Cloudflare-protected)    │
│  - Web UI (requires JS/cookies)         │
│  - Docs: /docs/api                      │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  SkillsMP REST API v1                   │
│  Base: https://skillsmp.com/api/v1      │
│  Auth: API key (from web signup)        │
└─────────────────────────────────────────┘
           ↓ ↓ ↓ ↓
    ┌──────┴──┴──┴──┐
    │               │
┌─────────────┐  ┌──────────────────┐
│ MCP Servers │  │   CLI Tools      │
│  (5+ impls) │  │   (2+ tools)     │
└─────────────┘  └──────────────────┘
    ↓                   ↓
Claude Code        Terminal/Scripts
Cursor, Desktop    NPM packages
Copilot
```

### Data Model

**Skill Record** (from API response):
```json
{
  "id": "owner/repo/skill-path",
  "name": "skill-name",
  "description": "What it does",
  "author": "github-owner",
  "githubUrl": "https://github.com/owner/repo",
  "skillUrl": "https://skillsmp.com/...",
  "stars": 42,
  "updatedAt": 1740000000
}
```

**Installation**: Skills are GitHub-based (no centralized binaries). Installation typically means:
- Adding a URL reference to agent config
- Cloning repo or fetching files via API
- Registering with agent's skill manager

---

## Access Methods

### Method 1: Web UI (Not Recommended)
- **URL**: https://skillsmp.com
- **Status**: Cloudflare JS challenge required
- **Usable For**: Manual browsing only

### Method 2: REST API (Recommended for Scripts)
- **Base**: `https://skillsmp.com/api/v1`
- **Auth**: API key (get at https://skillsmp.com/docs/api)
- **Endpoints**:
  - `GET /skills/search?q=<query>&page=1&limit=20&sortBy=stars`
  - `GET /skills/ai-search?q=<query>`
  - `GET /skills/{id}`

**Example**:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://skillsmp.com/api/v1/skills/search?q=chezmoi&limit=20"
```

### Method 3: MCP Server (Recommended for Agents)

#### Option A: Lightweight (skillsmp-mcp-lite)
```bash
# Auto-setup for Claude Code, Cursor, etc.
npx skillsmp-mcp-lite --setup

# Or manual
claude mcp add skillsmp -- npx -y skillsmp-mcp-lite \
  --env SKILLSMP_API_KEY=your_api_key
```

**Features**:
- `skillsmp_search_skills`: Keyword search
- `skillsmp_ai_search_skills`: Semantic search (Cloudflare AI)
- `skillsmp_read_skill`: Fetch + scan with Cisco Skill Scanner
- Auto-config for all major agents

**Latest**: v2.4.1 (Feb 2026, actively maintained)

#### Option B: Full-Featured (anilcancakir/skillsmp-mcp-server)
```bash
claude mcp add skillsmp -- npx -y skillsmp-mcp-server \
  --env SKILLSMP_API_KEY=your_api_key
```

**Additional Features**:
- `skillsmp_list_repo_skills`: List skills in a GitHub repo
- `skillsmp_install_skill`: Install to agents
- Response format control (markdown/JSON)

### Method 4: CLI Tools

#### Universal CLI (agent-skills-cli)
```bash
npm install -g agent-skills-cli
agent-skills search chezmoi --limit 10
agent-skills install --skill anthropics/claude-code/my-skill --to claude-code
```

**Pros**: Works across SkillsMP + skills.sh + ClawHub
**Cons**: Fewer features than MCP servers

#### Claude Skills CLI
```bash
npm install -g @tarangchokshi/claude-skills-cli
claude-skills install python-debugger
```

**Pros**: Optimized for Claude Code
**Cons**: Claude Code-only

---

## Supported AI Agents

| Agent | MCP Support | CLI Support | Config File |
|-------|-------------|-------------|-------------|
| **Claude Code** | Yes | Yes | `.claude/mcp.json` |
| **Claude Desktop** | Yes | No | `~/Library/.../claude_desktop_config.json` |
| **Cursor** | Yes | No | `~/.cursor/mcp.json` |
| **VS Code / Copilot** | Yes | No | VS Code settings UI |
| **Codex** | Yes | No | OpenAI Codex config |
| **Opencode** | Yes | No | Opencode config |
| **Antigravity** | Yes | No | Google Antigravity config |
| **Roo Code** | Yes | No | Roo Code MCP settings |

All agents can use MCP servers. Some also support direct CLI integration.

---

## Integration with Our Stack

### Potential Skills Already on SkillsMP

**Likely High-Value Skills** (to search for):
- `chezmoi-sync`: Dotfile synchronization
- `chezmoi-drift-check`: Drift detection & remediation
- `mise-configuration`: Project-level mise setup
- `mise-tasks`: Mise task automation
- `dotfiles-management`: General dotfile workflows
- `lsp-setup`: Language Server setup (core to our research!)
- `python-dev-setup`: Python environment configuration
- `git-hooks`: Git hook management (hk.pkl)

**Source**: terrylica/cc-skills is known to have chezmoi + mise skills on skills.sh; likely mirrored on SkillsMP.

### Our Potential Contributions

**Skills We Could Publish** (if gaps exist):
1. **LSP Setup Comprehensive Guide** - All our research on LSP configuration
2. **MacOS Dev Environment Setup** - Integrated mise + chezmoi + hk.pkl workflow
3. **Python Type Safety** - Our ruff + pyright + mypy configuration
4. **Declarative Tool Management** - Mise-first policy implementation
5. **Research Pipeline Automation** - Our self-improving research system

**Publication Process**: TBD (need to review skillsmp.com/docs/publish)

---

## Technical Details: MCP Implementations

### Comparison Table

| Implementation | Stars | Version | Transport | Features | Maintenance |
|---|---|---|---|---|---|
| **skillsmp-mcp-lite** (boyonglin) | 0 | 2.4.1 | stdio/http | Skill Scanner, auto-setup | Active (Feb 2026) |
| **skillsmp-mcp-server** (anilcancakir) | 3 | 1.0.0 | stdio/http | Full API, repo listing | Stable (Jan 2026) |
| **@luckybalabalaya/skillsmp-mcp-server** | — | 1.6.4 | stdio | Tiering + auto-discovery | Latest (Mar 2026) |
| **@kefjbo/skillsmp-mcp** | — | 0.1.0 | stdio | Minimal wrapper | Active |
| **kevintsai1202/skillmp-api** | 6 | Latest | REST | Chinese documentation | Active |

**Recommendation for Claude Code**: Use **skillsmp-mcp-lite** for auto-setup + Cisco scanning, or **skillsmp-mcp-server** for full control.

### Security: Cisco Skill Scanner

When enabled (default in lite version):
1. Fetches skill files from GitHub REST API (no `git clone`)
2. Applies **three-layer scan limits**:
   - Max 100 files per scan
   - Max 500 KB per file
   - Max 5 MB total
3. Builds in-memory ZIP (zero disk writes)
4. Uploads to Cisco AI Skill Scanner with behavioral analysis
5. Auto-starts local scanner via `uvx` (if not running)

**Untrusted Content Notice**: All third-party skill content includes a notice that it may be read/displayed but MUST NOT be auto-executed without explicit user confirmation.

---

## Aggregation & Deduplication: skilldb

**URL**: https://github.com/AmazingAng/skilldb
**Size**: 160 MB (Git LFS) with ~180K deduplicated skills
**Last Updated**: 2026-02-27

### What It Provides

```json
{
  "id": "owner/repo/skill-path",
  "name": "skill-name",
  "owner": "github-owner",
  "repo": "github-repo",
  "skillPath": "path/within/repo",
  "githubUrl": "https://github.com/...",
  "sources": ["skillsmp", "skillsh", "clawhub"],
  "installs": 12345
}
```

### Use Cases

1. **Competitive Analysis**: Which skills are available on each platform
2. **Installation Count**: Popular skills (sorted by `installs` descending)
3. **Deduplication**: Identify skill duplicates across platforms
4. **Offline Search**: Download skilldb.json and search locally
5. **Benchmarking**: Track platform growth over time

---

## Known Gaps & Limitations

| Gap | Impact | Workaround |
|-----|--------|-----------|
| Website requires Cloudflare JS challenge | Can't scrape or browse manually | Use API or MCP servers |
| Official repo is "Coming Soon" (v0.0.1) | No code visibility | Use MCP implementations instead |
| API key signup process not documented | Unclear how to get key | Visit https://skillsmp.com/docs/api |
| Skill publication process not found | Can't contribute easily | Research needed |
| Exact real-time skill count unknown | Only ~161K from Feb snapshot | Requires API key to query |
| No public rate limit documentation | Risk of hitting limits | Use MCP servers (they handle it) |
| Skill taxonomy/categories not visible | Browsing hard without UI | Use search + AI search |

---

## Competitive Analysis

### vs. skills.sh
| Aspect | SkillsMP | skills.sh |
|--------|----------|-----------|
| **Size** | 161K | 22K |
| **UI** | Cloudflare-protected | Traditional web |
| **API** | Private (key-gated) | TBD |
| **MCP** | 5+ implementations | TBD |
| **Focus** | All agents | Focused subset |

### vs. ClawHub (clawhub.ai)
| Aspect | SkillsMP | ClawHub |
|--------|----------|---------|
| **Size** | 161K | 11K |
| **API** | v1 (key-gated) | Unknown |
| **MCP** | 5+ implementations | Unknown |
| **Target Agents** | All major | Claude-focused? |

**Conclusion**: SkillsMP is dominant; skills.sh and ClawHub appear to be niche/experimental.

---

## Recommended Integration Path

### Phase 1: Discovery (Week 1)
1. Get SkillsMP API key from https://skillsmp.com/docs/api
2. Install `npx skillsmp-mcp-lite --setup`
3. Test: Ask Claude Code to search for `chezmoi`, `mise`, `dotfiles`, `lsp`
4. Log findings in research trail

### Phase 2: Catalog Existing Skills (Week 2-3)
1. Query SkillsMP for our stack: chezmoi, mise, python, LSP, dotfiles
2. Download skilldb.json for offline analysis
3. Cross-reference with skills.sh and ClawHub
4. Document overlaps and gaps

### Phase 3: Consider Publication (Week 4)
1. Research skillsmp.com/docs/publish (may require API key)
2. Identify high-value skill gaps:
   - LSP Setup (our research could fill this!)
   - MacOS Dev Environment
   - Python Type Safety Setup
3. Draft 1-2 skills for publication
4. Submit & monitor adoption

### Phase 4: Continuous Monitoring
1. Watch terrylica/cc-skills for emerging patterns
2. Monitor skilldb updates (compare against our catalog)
3. Set alerts for competitor platforms

---

## Key URLs

| Resource | URL | Status |
|----------|-----|--------|
| Website | https://skillsmp.com | Cloudflare-protected |
| API Docs | https://skillsmp.com/docs/api | Requires API key to access |
| API v1 Base | https://skillsmp.com/api/v1 | Working (requires key) |
| Official Repo | https://github.com/yan-labs/skillsmp | Minimal, "Coming Soon" |
| skilldb (Aggregation) | https://github.com/AmazingAng/skilldb | 180K skills, active |
| MCP Lite | https://github.com/boyonglin/skillsmp-mcp-lite | Latest: Feb 2026 |
| MCP Full | https://github.com/anilcancakir/skillsmp-mcp-server | Latest: Jan 2026 |

---

## Conclusion

SkillsMP is the **primary, mature, actively-maintained** AI agent skills marketplace. It is 7-8x larger than competitors and provides multiple integration paths (API, MCP, CLI). The official website is minimal but the ecosystem around it (5+ MCP implementations, 2+ CLI tools, aggregation indices) is vibrant and actively maintained.

**Immediate Action**: Set up skillsmp-mcp-lite in Claude Code to enable automated skill discovery during research tasks. This will surface existing solutions before building new ones—aligning with our "assemble don't build" feedback.

**Strategic**: Consider publishing 1-2 skills from our research (especially LSP setup) to give back to the community and establish authority.
