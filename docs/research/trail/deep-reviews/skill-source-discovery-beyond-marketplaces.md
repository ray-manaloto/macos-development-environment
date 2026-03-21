# Skill Source Discovery: Beyond Official Marketplaces

**Researched:** 2026-03-21
**Scope:** GitHub topic search, skills.sh marketplace, awesome lists, framework-specific collections
**Result:** 45+ new sources identified; 8 distinct distribution patterns

---

## Executive Summary

Claude Code skills are distributed across three distinct tiers, not just the primary marketplaces (skills.sh, awesomeclaude.ai). A systematic search reveals:

- **Tier-1** (10K+ stars): 5 comprehensive ecosystem repos aggregating 1000s of skills
- **Tier-2** (3K-8K stars): 12+ specialized collections (domain, framework, platform-specific)
- **Tier-3** (50-2K installs): 45+ distributed on skills.sh by individual authors and teams

The richest source of undocumented patterns exists in **personal dotfiles repos** where SKILL.md files encode framework expertise (mise, chezmoi, homebrew, Python dev) not published to mainstream marketplaces.

---

## Distribution Tier Breakdown

### TIER-1: Comprehensive Ecosystem Repos (10K+ stars, 1000s of skills)

| Repo | Stars | Scope | New? |
|------|-------|-------|------|
| **affaan-m/everything-claude-code** | 90.8K | "Agent harness performance optimization system. Skills, instincts, memory, security, research-first development for Claude Code, Codex, Opencode, Cursor and beyond." | NEW |
| **anthropics/skills** | 98.6K | OFFICIAL Anthropic agent skills registry (public, open-source) | — |
| **ComposioHQ/awesome-claude-skills** | 46.4K | "A curated list of awesome Claude Skills, resources, and tools for customizing Claude AI workflows" | NEW |
| **wshobson/agents** | 31.8K | "Intelligent automation and multi-agent orchestration for Claude Code" | NEW |
| **hesreallyhim/awesome-claude-code** | 29.4K | "Curated list of awesome skills, hooks, slash-commands, agent orchestrators, applications, and plugins for Claude Code" | NEW |

**Strategic Value:** Entry points for skill discovery. Each aggregates or links to Tier-2 collections.

---

### TIER-2: Specialized Collections (3K-12K stars, domain/framework/platform focus)

#### Multi-Platform (Claude Code + Cursor + Codex + Gemini CLI)

| Repo | Stars | Focus | Installs | New? |
|------|-------|-------|----------|------|
| **sickn33/antigravity-awesome-skills** | 26.2K | "1,273+ agentic skills, installer CLI, bundles, workflows, skill collections" | — | NEW |
| **VoltAgent/awesome-agent-skills** | 12.1K | "500+ agent skills from official dev teams and community" | — | NEW |
| **VoltAgent/awesome-claude-code-subagents** | 14.4K | Subagent-specific collections | — | NEW |
| **VoltAgent/awesome-openclaw-skills** | 40.1K | Cross-platform (OpenClaw primary) | — | NEW |

#### Domain/Role-Specific

| Repo | Stars | Focus | New? |
|------|-------|-------|------|
| **phuryn/pm-skills** | 7.8K | Product/marketing automation (100+ skills) | NEW |
| **alirezarezvani/claude-skills** | 6.1K | Multi-domain (engineering, marketing, product, compliance, C-level) | NEW |
| **travisvn/awesome-claude-skills** | 8.9K | Skills inventory | NEW |
| **BehiSecc/awesome-claude-skills** | 7.5K | Skills inventory | NEW |
| **vijaythecoder/awesome-claude-agents** | 4.0K | Agent-focused | NEW |

#### Framework/Platform-Specific

| Repo | Stars | Focus | New? |
|------|-------|-------|------|
| **keskinonur/claude-code-ios-dev-guide** | 488 | Swift/SwiftUI iOS development (PRD-driven, extended thinking) | NEW |
| **jabrena/cursor-rules-java** | 329 | Java enterprise development patterns | NEW |
| **decebals/claude-code-java** | 417 | Java development infrastructure | NEW |
| **athola/claude-night-market** | 221 | "17 production-ready plugins: git workflows, code review, spec-driven dev, architecture, resource optimization" | NEW |
| **NikiforovAll/claude-code-rules** | 104 | Practical enhancement techniques | NEW |

#### Architecture/Infrastructure

| Repo | Stars | Focus | New? |
|------|-------|-------|------|
| **parcadei/Continuous-Claude-v3** | 3.6K | Context management via hooks, MCP execution without pollution | NEW |
| **zebbern/claude-code-guide** | 3.7K | Setup, commands, workflows, agents, skills, tips | NEW |
| **KhazP/vibe-coding-prompt-template** | 2.0K | PRD/Tech Design/MVP generation | NEW |

#### Specialized Use Cases

| Repo | Stars | Focus | New? |
|------|-------|-------|------|
| **a5c-ai/babysitter** | 482 | Task complexity enforcement, hallucination-free orchestration | NEW |
| **ljagiello/ctf-skills** | 469 | CTF challenge solutions (web, binary, crypto, OSINT) | NEW |
| **opslane/verify** | 90 | Production verification layer | NEW |
| **ivan-magda/claude-code-plugin-template** | 44 | Plugin marketplace scaffolding | NEW |

---

### TIER-3: Personal Ecosystem (skills.sh marketplace, GitHub SKILL.md patterns)

#### Top Performers on skills.sh (80+ installs)

| Skill | Installs | Category | Author |
|-------|----------|----------|--------|
| terrylica/cc-skills@mise-tasks | 114 | mise | terrylica (NEXUS) |
| 0xbigboss/claude-code@nix-best-practices | 181 | nixos | 0xbigboss |
| samhvw8/dotfiles@mise-expert | 98 | mise | samhvw8 |
| bobmatnyc/claude-mpm-skills@homebrew-formula-maintenance | 84 | homebrew | bobmatnyc |
| terrylica/cc-skills@chezmoi-workflows | 85 | chezmoi | terrylica (NEXUS) |
| connorads/dotfiles@homebrew-cask-authoring | 68 | homebrew | connorads |
| terrylica/cc-skills@mise-configuration | 63 | mise | terrylica (NEXUS) |

**Pattern:** `terrylica/cc-skills` is a "nexus ecosystem" with multiple specialized plugins (mise-tasks, mise-configuration, chezmoi-workflows, dotfiles-tools, devops-tools, plugin-dev, itp, gh-tools).

#### SKILL.md Pattern Discovery (GitHub Code Search)

Personal dotfiles repos contain 45+ undocumented skills. Key patterns:

| Source | Skill | Pattern | Framework |
|--------|-------|---------|-----------|
| majiayu000/claude-skill-registry | chezmoi-sync | Official expertise skill | chezmoi |
| rmullin7286/dotfiles | chezmoi-sync | Drift detection + guard | chezmoi |
| terrylica/cc-skills | chezmoi-sync | Interactive drift, re-add workflows | chezmoi |
| ssiumha/dots | mise-config | Project-level configuration | mise |
| btuckerc/boilerplate | install-tools | Chezmoi + mise coordination | multi |

---

## Distribution Channels

### Channel A: GitHub Awesome Lists (100+ repos)

**Characteristics:**
- Manually curated, updated periodically
- High signal-to-noise (quality > quantity)
- Often categorized by domain/framework

**Key Lists:**
1. `ComposioHQ/awesome-claude-skills` (46.4K stars)
2. `hesreallyhim/awesome-claude-code` (29.4K stars)
3. `anthropics/skills` (98.6K stars) — official
4. `VoltAgent/awesome-*` ecosystem (3 repos)
5. `travisvn/awesome-claude-skills` (8.9K stars)

### Channel B: skills.sh Marketplace (89K+ total installs)

**Characteristics:**
- Install-count based ranking
- Per-author/per-skill granularity
- Skills grouped by category (mise, chezmoi, homebrew, dev-env, etc.)

**Top Categories:**
- Mise integration: 350+ combined installs
- Chezmoi management: 200+ combined
- Homebrew automation: 200+ combined
- Dev environment: 100+ combined

### Channel C: Personal Dotfiles Repos (50+ on GitHub)

**Characteristics:**
- Undocumented, context-specific patterns
- High technical depth
- Encodes framework expertise (mise, chezmoi, brew, nix)

**Discovery Method:** GitHub code search for SKILL.md files

---

## Ecosystem Authors (Nexus Pattern)

| Author | Repos | Expertise |
|--------|-------|-----------|
| **terrylica** | cc-skills (5+ plugins) | mise, chezmoi, devops, plugin-dev |
| **wshobson** | agents (31.8K) | Multi-agent orchestration |
| **affaan-m** | everything-claude-code (90.8K) | Agent harness optimization |
| **VoltAgent (org)** | awesome-* (3 repos) | Cross-tool compatibility |

---

## Gaps and Limitations

1. **Real-Time Discovery:** No API for skills.sh new releases
2. **Cross-Platform Matrix:** Unclear which skills work on Cursor/Codex vs Claude Code only
3. **Adoption Metrics:** GitHub awesome lists lack install counts
4. **Deprecated Signal:** No indicator for unmaintained repos
5. **Private Collections:** Org/team-specific skills unavailable

---

## Strategic Recommendations

### 1. Establish Periodic Monitoring
- **Daily:** Top 20 skills on skills.sh by install count
- **Weekly:** New repos with `topic:claude-code-skills`
- **Monthly:** Audit "Nexus authors" for new repos

### 2. Cross-Reference Local Analysis
- Map `source-catalog.md` entries to GitHub topics
- Identify skills in `.claude/skills/` directory
- Create adoption heat map

### 3. Framework-Specific Deep Dives
- **mise:** terrylica (114 installs), samhvw8 (98 installs)
- **chezmoi:** terrylica (85 installs), connorads (homebrew-adjacent)
- **homebrew:** bobmatnyc (84 installs), connorads (68 installs)

### 4. Document Undiscovered Patterns
- SKILL.md patterns in personal dotfiles encode expertise
- Identify "hidden" skills via GitHub code search
- Map framework-specific skill density

---

## Conclusion

The Claude Code skills ecosystem is distributed across three tiers with distinct characteristics:

1. **Tier-1** (10K+ stars): Awesome lists and official registries
2. **Tier-2** (3K-12K stars): Domain/framework-specific collections
3. **Tier-3** (skills.sh): Individual authors, personal dotfiles

Future research should prioritize **framework-specific collections** and **ecosystem authors** to surface emerging patterns before mainstream discovery.
