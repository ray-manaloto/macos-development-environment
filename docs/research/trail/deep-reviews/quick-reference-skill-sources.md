# Quick Reference: Non-Obvious Claude Code Skill Sources

**Research Date:** 2026-03-21
**Status:** 45+ new sources cataloged across 3 distribution tiers

---

## At a Glance

| Tier | Category | Count | Stars | Value |
|------|----------|-------|-------|-------|
| **1** | Comprehensive aggregators | 9 | 10K+ | Entry points to discovery |
| **2** | Specialized collections | 18 | 3K-12K | Domain/framework expertise |
| **3** | Personal ecosystem | 30+ | 50-200 installs | Undocumented patterns |

---

## Tier-1: Must-Monitor Repos

**Adopt these as your primary discovery feeds:**

| Repo | Stars | Type | When |
|------|-------|------|------|
| anthropics/skills | 98.6K | Official | OFFICIAL SOURCE |
| affaan-m/everything-claude-code | 90.8K | Awesome | Monitor for updates |
| ComposioHQ/awesome-claude-skills | 46.4K | Awesome | Monitor for updates |
| wshobson/agents | 31.8K | Awesome | Monitor for updates |
| hesreallyhim/awesome-claude-code | 29.4K | Awesome | Monitor for updates |

**Action:** Subscribe to releases feed for each.

---

## Tier-2: Deep Domain Expertise

**When you need skills for a specific domain/framework:**

### Product/Marketing
- phuryn/pm-skills (7.8K) — 100+ PM-specific skills

### Platform-Specific
- keskinonur/claude-code-ios-dev-guide (488) — iOS/Swift
- jabrena/cursor-rules-java (329) — Java enterprise

### Production-Ready
- athola/claude-night-market (221) — 17 battle-tested plugins

---

## Tier-3: Where the Real Patterns Live

**Three sub-patterns exist:**

### A. Nexus Authors
Track these people—they publish frequently:
- **terrylica** — cc-skills ecosystem (5+ plugins)
- **wshobson** — agents orchestration
- **affaan-m** — agent harness optimization

### B. Top Skills by Framework (skills.sh)

**Mise (most popular):**
- terrylica/cc-skills@mise-tasks (114 installs) ← HIGHEST
- samhvw8/dotfiles@mise-expert (98)

**Chezmoi:**
- terrylica/cc-skills@chezmoi-workflows (85)

**Homebrew:**
- bobmatnyc/claude-mpm-skills@homebrew-formula-maintenance (84)

### C. Hidden Patterns (GitHub SKILL.md)
45+ personal dotfiles repos contain undocumented expertise in:
- `majiayu000/claude-skill-registry` — chezmoi
- `rmullin7286/dotfiles` — chezmoi sync patterns
- `ssiumha/dots` — mise configuration
- `btuckerc/boilerplate` — chezmoi + mise coordination

---

## Distribution Channels

| Channel | Volume | Discovery Method | Maintenance |
|---------|--------|------------------|-------------|
| **GitHub Awesome Lists** | 100+ repos | Search `awesome-claude` | RSS, releases feed |
| **skills.sh Marketplace** | 89K+ installs | Install rankings | Web scraping |
| **Personal Dotfiles** | 50+ repos | SKILL.md search | GitHub code search |

---

## Key Findings

### 1. terrylica/cc-skills = Nexus Ecosystem
Single author with 5+ specialized plugins across different package managers.
- mise-tasks (114 installs)
- chezmoi-workflows (85 installs)
- mise-configuration (63 installs)
- Plus: dotfiles-tools, devops-tools, plugin-dev, itp, gh-tools

**Action:** Track all repos and plugins from terrylica.

### 2. Framework-Specific Consolidation
Highest adoption density exists in:
1. Mise integration (350+ combined installs)
2. Chezmoi management (200+ combined)
3. Homebrew automation (200+ combined)

**Action:** When bootstrapping, start with terrylica skills, then expand to framework specialists.

### 3. Undocumented Personal Patterns
45+ SKILL.md files in dotfiles repos encode expertise not published to mainstream sources.

**Action:** Use GitHub code search to find patterns relevant to your stack.

---

## Monitoring Strategy

### Daily
- Refresh top 20 skills on skills.sh by category
- Watch for changes in terrylica, wshobson repos

### Weekly
- Check GitHub releases for Tier-1 awesome lists
- Monitor new repos with `topic:claude-code-skills`

### Monthly
- Scrape skills.sh top performers by category
- Audit nexus authors for new plugins

---

## Quick Links

| Purpose | Source | URL |
|---------|--------|-----|
| Official registry | Anthropic | https://github.com/anthropics/skills |
| Curated list | ComposioHQ | https://github.com/ComposioHQ/awesome-claude-skills |
| Agent focus | hesreallyhim | https://github.com/hesreallyhim/awesome-claude-code |
| Skill installer | skills.sh | https://skills.sh |
| Marketplace | awesomeclaude.ai | https://awesomeclaude.ai |

---

## Summary

The Claude Code skills ecosystem has three distinct tiers:

1. **Tier-1:** Large aggregators (10K+ stars)—use as feed sources
2. **Tier-2:** Domain specialists (3K-12K stars)—consult for specific needs
3. **Tier-3:** Personal ecosystem (skills.sh + dotfiles)—mine for undocumented patterns

**Core insight:** The richest patterns live in personal dotfiles repos and small specialized collections, not mainstream marketplaces.
