# Marketplace Skills Research: Ranked List

**Research Date:** 2026-03-21
**Search Scope:** skills.sh (npx skills search), GitHub code search (SKILL.md files)
**Finding Reference:** `docs/research/trail/findings/finding-marketplace-chezmoi-mise-search.yaml`

---

## Executive Summary

Marketplace search across skills.sh and GitHub identified **25+ relevant skills** for dotfiles, mise, and macOS dev-environment automation. The **top-tier recommendations** are:

1. **terrylica/cc-skills@mise-tasks** (114 installs) — premier mise automation
2. **terrylica/cc-skills@chezmoi-workflows** (85 installs) — most-adopted chezmoi skill
3. **bobmatnyc/claude-mpm-skills@homebrew-formula-maintenance** (84 installs) — homebrew expertise
4. **samhvw8/dotfiles@mise-expert** (98 installs) — alternative mise specialist

**Current Installed:** faintghost/skills@chezmoi-config (28 installs) — LOW adoption relative to alternatives.

---

## Tier 1: Peak Adoption (80+ installs)

These skills have proven track records with 80+ installations each.

### 1. terrylica/cc-skills@mise-tasks (114 installs)
- **URL:** https://skills.sh/terrylica/cc-skills/mise-tasks
- **Category:** Mise task automation
- **Repository:** https://github.com/terrylica/cc-skills
- **Key Facts:**
  - Highest adoption rate in mise category
  - Same author as #2 (chezmoi-workflows) — suggests ecosystem compatibility
  - Part of 20-plugin terrylica ecosystem
  - Source verified: GitHub API call confirmed plugin structure
- **Recommendation:** INSTALL FIRST — likely highest quality and best integration with other terrylica skills

### 2. samhvw8/dotfiles@mise-expert (98 installs)
- **URL:** https://skills.sh/samhvw8/dotfiles/mise-expert
- **Category:** Mise expertise skill
- **Key Facts:**
  - High adoption, specialist focus
  - Sourced from dotfiles repository (production battle-tested)
- **Recommendation:** INSTALL as alternative/complement to terrylica@mise-tasks for broader mise expertise

### 3. terrylica/cc-skills@chezmoi-workflows (85 installs)
- **URL:** https://skills.sh/terrylica/cc-skills/chezmoi-workflows
- **Category:** Chezmoi dotfile workflows
- **Repository:** https://github.com/terrylica/cc-skills
- **Key Facts:**
  - Highest adoption in chezmoi category
  - Same author as mise-tasks → ecosystem compatibility
  - Part of dotfiles-tools plugin architecture
  - GitHub discovery found SKILL.md with interactive drift check patterns
- **Recommendation:** INSTALL SECOND — replace faintghost/skills@chezmoi-config (28 installs) with this higher-adoption version

### 4. bobmatnyc/claude-mpm-skills@homebrew-formula-maintenance (84 installs)
- **URL:** https://skills.sh/bobmatnyc/claude-mpm-skills/homebrew-formula-maintenance
- **Category:** Homebrew package management
- **Key Facts:**
  - Highest adoption in homebrew category
  - Specializes in formula creation/maintenance
  - No direct ecosystem lock-in, can be used independently
- **Recommendation:** INSTALL to complete chezmoi+mise+brew triangle

---

## Tier 2: Strong Adoption (50-79 installs)

### 5. bobmatnyc/claude-mpm-skills (homebrew variants)
- **Homebrew Cask Authoring** (connorads/dotfiles) — 68 installs
- **Homebrew Formula Dev** (arustydev/ai) — 14 installs
- **Recommendation:** Secondary sources if formula-maintenance insufficient

### 6. terrylica/cc-skills@mise-configuration (63 installs)
- **URL:** https://skills.sh/terrylica/cc-skills/mise-configuration
- **Category:** Project-level mise configuration
- **Key Facts:**
  - Complements mise-tasks (same author)
  - Focused on mise.toml project setup
  - Likely covers declarative configuration patterns
- **Recommendation:** INSTALL alongside mise-tasks for complete mise coverage

### 7. connorads/dotfiles@homebrew-cask-authoring (68 installs)
- **URL:** https://skills.sh/connorads/dotfiles/homebrew-cask-authoring
- **Category:** Homebrew cask expertise
- **Recommendation:** Optional if advanced cask patterns needed

---

## Tier 3: Moderate Adoption (30-49 installs)

### 8. patricio0312rev/skills@dev-environment-bootstrapper (36 installs)
- **URL:** https://skills.sh/patricio0312rev/skills/dev-environment-bootstrapper
- **Category:** Full dev environment orchestration
- **Key Facts:**
  - Orchestrates complete environment setup
  - May coordinate chezmoi+mise+brew flows
- **Recommendation:** EVALUATE for unified setup orchestration patterns

### 9. faintghost/skills@chezmoi-config (28 installs) **[CURRENTLY INSTALLED]**
- **URL:** https://skills.sh/faintghost/skills/chezmoi-config
- **Category:** Chezmoi configuration
- **Key Facts:**
  - Currently installed in mde project
  - LOW adoption relative to terrylica@chezmoi-workflows (85)
  - 3x fewer installations than top-tier chezmoi skill
- **Recommendation:** REPLACE with terrylica@chezmoi-workflows for higher adoption and better maintenance likelihood

---

## Tier 4: Niche Adoption (10-29 installs)

### 10. fonnesbeck/shay-mwa@chezmoi-chef (26 installs)
- **URL:** https://skills.sh/fonnesbeck/shay-mwa/chezmoi-chef
- **Category:** Chezmoi workflow patterns

### 11. gwenwindflower/.charmschool@chezmoi (17 installs)
- **URL:** https://skills.sh/gwenwindflower/.charmschool/chezmoi
- **Category:** Educational chezmoi patterns (Charm school approach)

### 12. miles990/claude-software-skills@development-environment (18 installs)
- **URL:** https://skills.sh/miles990/claude-software-skills/development-environment
- **Category:** General dev environment

### 13. panaversity/agentfactory@python-dev-environment (17 installs)
- **URL:** https://skills.sh/panaversity/agentfactory/python-dev-environment
- **Category:** Python-specific dev environment

### 14. arustydev/ai@pkgmgr-homebrew-formula-dev (14 installs)
- **URL:** https://skills.sh/arustydev/ai/pkgmgr-homebrew-formula-dev
- **Category:** Homebrew formula development

---

## Unified Ecosystem: terrylica/cc-skills (20 plugins)

**Key Discovery:** terrylica/cc-skills is a comprehensive plugin marketplace that bundles multiple related capabilities.

### Structure
| Plugin | Focus | Relevance |
|--------|-------|-----------|
| dotfiles-tools | Chezmoi natural language workflows | CRITICAL — handles chezmoi automation |
| devops-tools | Doppler, MLOps, credentials | HIGH — relevant for secrets management |
| plugin-dev | Skill architecture validation | REFERENCE — understanding plugin patterns |
| itp | ADR-driven 4-phase development | REFERENCE — development methodology |
| gh-tools | GitHub workflow automation | HIGH — integrates with PR/git workflow |

**Recommendation:** Install terrylica/cc-skills as primary ecosystem for:
- Unified chezmoi + mise authoring (both via same team)
- Plugin architecture patterns (may inform mde's own skill system)
- DevOps integration (Doppler, secrets, CI/CD)

---

## Alternative Ecosystems NOT Recommended

### Nix-based Configuration
- **0xbigboss/claude-code@nix-best-practices** (181 installs)
- **greenheadhq/nixos-config@managing-macos** (10 installs)

**Status:** Discovered for completeness, NOT recommended for mde.
**Reason:** Project is committed to chezmoi+mise+brew architecture per CLAUDE.md and mise-first policy.

---

## Marketplace Platform Assessment

### Accessible Directories
- ✅ **skills.sh** — Primary marketplace, full search support (npx skills search)
- ✅ **GitHub Code Search** — SKILL.md discovery via gh command
- ❌ **skillsmp.com** — No accessible directory or API
- ❌ **awesome-skills.com** — No accessible directory or API
- ❌ **lobehub.com/skills** — No accessible directory or API

### Recommendation
- Primary source: **skills.sh** (proven, discoverable, install-ready)
- Secondary source: **GitHub code search** (deep patterns, less-advertised skills)
- Avoid: Web marketplace platforms (no public APIs, HTML not parseable)

---

## Recommended Installation Order

### Phase 1: Core (Install First)
1. `terrylica/cc-skills@mise-tasks` (114 installs) — mise automation
2. `terrylica/cc-skills@chezmoi-workflows` (85 installs) — chezmoi replacement for faintghost
3. `bobmatnyc/claude-mpm-skills@homebrew-formula-maintenance` (84 installs) — homebrew

### Phase 2: Enhancement (Install If Needed)
4. `terrylica/cc-skills@mise-configuration` (63 installs) — project-level mise config
5. `samhvw8/dotfiles@mise-expert` (98 installs) — additional mise expertise
6. `patricio0312rev/skills@dev-environment-bootstrapper` (36 installs) — orchestration

### Phase 3: Optional (Reference Only)
7. `fonnesbeck/shay-mwa@chezmoi-chef` — patterns and examples
8. `connorads/dotfiles@homebrew-cask-authoring` — advanced homebrew

---

## Integration Notes

### Known Coordination Patterns (from GitHub discovery)
- **btuckerc/boilerplate**: Coordinates chezmoi + mise in single install-tools skill
- **rmullin7286/dotfiles**: Chezmoi-sync patterns (git add → commit → push)
- **terrylica/cc-skills**: Interactive drift check (chezmoi apply, chezmoi git rebase)

### Recommendation
Create unified **mde-dev-environment-setup** skill that chains:
1. Mise task execution (via mise-tasks skill)
2. Chezmoi apply + drift check (via chezmoi-workflows skill)
3. Homebrew cleanup (via homebrew-formula-maintenance skill)
4. Validation (verify all installed tools working)

---

## Discovery Method & Confidence

| Method | Sources Found | Confidence |
|--------|----------------|-----------|
| `npx skills search` | 25+ skills across 5 categories | HIGH — primary marketplace |
| GitHub code search | 12+ SKILL.md patterns | MEDIUM — subset only (rate limited) |
| Web marketplaces | 0 accessible results | LOW — platforms not queryable |

**Overall Confidence:** CONFIRMED for skills.sh tier 1-2; PROBABLE for tier 3-4 (smaller sample size).

---

## Next Steps

1. **Install and test** top-tier skills (Phase 1) in non-production environment
2. **Document integration** patterns in `.claude/skills/` for mde-dev-environment-setup skill
3. **Verify compatibility** between terrylica mise-tasks + chezmoi-workflows (same author)
4. **Plan replacement** of faintghost/skills@chezmoi-config with terrylica@chezmoi-workflows
5. **Monitor updates** to terrylica ecosystem (highest maintenance likelihood)
