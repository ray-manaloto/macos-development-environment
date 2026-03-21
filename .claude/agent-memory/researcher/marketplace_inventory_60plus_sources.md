---
name: Complete Skills Marketplace Inventory (60+ sources)
description: Comprehensive catalog of Claude Code skill/plugin marketplaces, registries, CLIs, and installation methods. Tiers 1-8 from official (11.1K stars) to personal collections.
type: reference
---

# Skills Marketplace Inventory Reference

**Last Updated:** 2026-03-21
**Total Sources:** 60+
**Discovery Method:** GitHub API + npm registry search + direct repo verification

## Quick Navigation

### Need to Find Skills?
- **Quick:** `npx skills search` (Vercel's skills.sh - official)
- **Browse:** GitHub awesome-claude-code (29.4K, curated list)
- **Multi-tool:** Use skillkit, skillfile, or agent-skills-cli
- **Explore:** Try plum TUI to see 750+ from 12 marketplaces

### Need to Install Skills?
- **Individual:** `npx skills add <name>`
- **Declarative (team):** Use skillfile + version control
- **Multi-tool:** skillkit translates across 40+ AI tools

### Need Domain-Specific?
- SAP: github.com/secondsky/sap-skills (155 stars, 35 skills)
- Elixir: github.com/georgeguimaraes/claude-code-elixir (130 stars)
- Shopware: github.com/shopwareLabs/ai-coding-tools
- Notion: github.com/tommy-ca/notion-skills

---

## Tier Reference

| Tier | Purpose | Count | Top Example | Best For |
|------|---------|-------|-------------|----------|
| **1** | Official / 1K+ stars | 3 | skills.sh (11.1K) | Primary marketplace |
| **2** | High-value (100-1K) | 12 | skillkit (617) | Production use |
| **3** | Emerging (10-100) | 25 | plum (11), skillfile (79) | Specialized needs |
| **4-6** | Community (< 10) | 15+ | Personal collections | Niche communities |
| **7-8** | Experimental | 5+ | squidbay (Bitcoin) | R&D, future models |

---

## Install Commands Quick Reference

```bash
# Official
npx skills search <query>
npx skills add <skill>

# Multi-tool bridges
npx skillkit
npx skillfile search
npx agent-skills-cli

# Aggregators
npx @itsdevcoffee/plum           # 750+ from 12 marketplaces (TUI)
npx lazyclaude                   # Visualize your Claude setup

# Package ecosystem
npm search "claude skill"
npm search "@elizaos/plugin-agent-skills"
```

---

## Key GitHub URLs (Top 15)

1. **github.com/vercel-labs/skills** (11.1K ⭐) — Official CLI + web
2. **github.com/hesreallyhim/awesome-claude-code** (29.4K ⭐) — Curated list
3. **github.com/jeremylongshore/claude-code-plugins-plus-skills** (1.67K ⭐) — 1367 skills + CCPI
4. **github.com/rohitg00/skillkit** (617 ⭐) — 40+ tools translator
5. **github.com/gmickel/gmickel-claude-marketplace** (547 ⭐) — Flow-Next, multi-model
6. **github.com/mhattingpete/claude-skills-marketplace** (478 ⭐) — SWE workflows
7. **github.com/Prat011/awesome-llm-skills** (1.02K ⭐) — Claude + Codex + Gemini
8. **github.com/anthropics/skills** (— ⭐) — Official Anthropic
9. **github.com/anthropics/life-sciences** (271 ⭐) — Official domain
10. **github.com/eljulians/skillfile** (79 ⭐) — 110K+ skills declarative
11. **github.com/Karanjot786/agent-skills-cli** (58 ⭐) — 40K+ skills CLI
12. **github.com/itsdevcoffee/plum** (11 ⭐) — Multi-marketplace TUI (powerful!)
13. **github.com/nextlevelbuilder/skillx** (36 ⭐) — Semantic search + ratings
14. **github.com/mertbuilds/claudemarketplaces.com** (72 ⭐) — Web directory
15. **github.com/secondsky/sap-skills** (155 ⭐) — 35 SAP skills

---

## Newly Discovered (2026-03-21 research)

Not in "What we already know" list from user:
1. **plum** — Multi-marketplace TUI (750+ from 12 sources)
2. **skillfile** — Declarative + 110K+ indexed
3. **skillkit** — 40+ tool translator
4. **SkillX.sh** — Semantic search + leaderboard
5. **agent-skills-cli** — SkillsMP bridge (40K+ skills)
6. **flins** — Universal installer
7. **claude-code-registry** — New community registry (2026)
8. **20+ domain-specific** marketplaces (SAP, Shopware, Elixir, Smalltalk, etc.)
9. **Decentralized models** (squidbay Bitcoin Lightning, clawmart trust-based)
10. **TUI visualizers** (lazyclaude, plum)

---

## Installation Complexity Score

| Tool | Ease | Speed | Best Use Case |
|------|------|-------|---------------|
| skills.sh | ⭐⭐⭐⭐⭐ | <1min | Discovery |
| plum TUI | ⭐⭐⭐⭐⭐ | ~2min | Exploration |
| skillkit | ⭐⭐⭐⭐ | ~5min | Multi-tool |
| skillfile | ⭐⭐⭐ | ~10min | Team projects |
| Manual clone | ⭐⭐ | 15+min | Deep customization |

---

## Performance Stats

| Metric | Leader | Value |
|--------|--------|-------|
| Stars (all) | awesome-claude-code | 29.4K |
| Stars (CLI) | skills.sh | 11.1K |
| Skills indexed | skillfile | 110K+ |
| Tool compatibility | skillkit | 40+ tools |
| Multi-marketplace | plum | 12 marketplaces |
| Domain focus | sap-skills | 35 SAP-specific |

---

## Critical Files for Deep Dive

1. **Full inventory:** `docs/research/trail/findings/finding-all-skill-marketplaces.yaml` (YAML provenance)
2. **Deep review:** `docs/research/trail/deep-reviews/complete-skills-marketplace-inventory-2026-03-21.md`
3. **Source catalog:** `docs/research/source-catalog.md` (60+ URLs logged, updated)

---

## Gaps Still Unfilled

- ❌ Centralized API across all 12 marketplaces
- ❌ Dependency resolution (skill A requires B)
- ❌ Version pinning (like npm lock files)
- ❌ Automatic skill validation/testing
- ❌ Performance benchmarking standard

**Next research:** Monitor emerging solutions in these gaps quarterly.

---

## Usage Tips

1. **Start here:** skills.sh for 90% of use cases
2. **Team projects:** skillfile for declarative management
3. **Exploration mode:** plum TUI to see all options
4. **Multi-tool:** skillkit if using Claude + Cursor + Copilot
5. **Specialized:** Look for domain-specific marketplace (20+ available)

