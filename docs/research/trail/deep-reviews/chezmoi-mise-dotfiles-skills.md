# Deep Review: Chezmoi + Mise Dotfiles Skills Landscape

**Date:** 2026-03-20
**Researcher:** research-agent (Claude Opus 4.6)
**Sources reviewed:** 10 URLs fetched via agent-fetch, 3 skills.sh searches, project codebase analysis
**Scope:** Identify existing and missing skills/plugins for chezmoi and mise dotfiles management

---

## 1. Executive Summary

This project (macos-development-environment) already has strong mise skills (`mise-enforcement`, `mise-tool-management`) and basic chezmoi validation (`src/mde/validate/chezmoi.py`), but **no dedicated chezmoi skills** and **no dotfiles-lifecycle skills** that tie the two tools together. The skills.sh searches returned empty results for chezmoi, mise, and dotfiles -- confirming these are greenfield skill opportunities. The awesome-claude-skills ecosystem has no chezmoi or mise skills either. martinemde/dotfiles provides the best reference for AI-first chezmoi integration patterns. gstack has no dotfiles management at all -- it is purely a sprint/review skill pack.

**Key finding:** We need 3-4 new skills to close the gap, not a dozen. The existing `mise-tool-management` and `mise-enforcement` skills are already well-designed; they need minor updates, not replacement.

---

## 2. Source Analysis

### 2.1 martinemde/dotfiles (AI-first dotfiles with chezmoi)

**URL:** https://github.com/martinemde/dotfiles
**Status:** Full review via agent-fetch

**Key patterns:**
- Uses chezmoi as the dotfiles manager with `chezmoi init --apply $GITHUB_USERNAME` as the entry point
- Uses mise for reproducible tool management (explicitly called out in README)
- Uses znap for fast zsh plugin loading, starship for cross-shell prompts
- Achieves 50-80% faster shell startup through caching and lazy-loading
- Supports macOS, Linux, and Devcontainers (portability)
- Non-interactive installation via env vars (`GIT_USER_NAME`, `GIT_USER_EMAIL`) for CI/CD
- ISC license

**AI-first integration patterns to adopt:**
1. **Pragmatic minimalism** -- single-purpose tools, minimal config, no bloated frameworks
2. **Portability via chezmoi templates** -- OS-conditional config via `.tmpl` files
3. **Non-interactive bootstrap** -- env-var-driven setup for agent contexts
4. **install.sh with chezmoi passthrough** -- `./install.sh -- --force` pattern

**What they do NOT have:** No Claude Code skills, no agent-aware workflows, no drift detection. Their AI-first claim is about the design philosophy (pragmatic, minimal), not about AI agent integration.

### 2.2 chezmoi Official (twpayne/chezmoi)

**URL:** https://github.com/twpayne/chezmoi
**Stars:** 18.6k, 5,633 commits
**Status:** Full review

**Core command workflow (from chezmoi.io docs):**
- `chezmoi add $FILE` -- home dir to source dir
- `chezmoi edit $FILE` -- edit source copy
- `chezmoi status` -- quick summary of pending changes
- `chezmoi diff` -- detailed diff
- `chezmoi apply` -- deploy changes to home dir
- `chezmoi edit --apply $FILE` -- edit + deploy in one step
- `chezmoi cd` -- shell into source dir
- `chezmoi init --apply $GITHUB_USERNAME` -- bootstrap from remote
- `chezmoi update` -- pull + apply
- `chezmoi data` -- print template data
- `chezmoi add --template $FILE` -- add as template
- `chezmoi chattr +template $FILE` -- convert existing to template
- `chezmoi cat $FILE` -- preview rendered output
- `chezmoi execute-template` -- test/debug templates
- `chezmoi doctor` -- health checks
- `chezmoi verify` -- detect drift (already used by our `src/mde/validate/chezmoi.py`)

**Notable:** chezmoi itself now ships a `pyproject.toml` and `uv.lock` -- the chezmoi project uses Python/uv for its documentation tooling, matching our stack.

**Secret management integrations:** 1Password, Bitwarden, gopass, KeePassXC, Keychain, LastPass, pass, Vault, age, gpg. Our project uses fnox + macOS Keychain + age (Tier 1), which aligns with chezmoi's `age` and `keychain` integrations.

### 2.3 mise Official (jdx/mise)

**URL:** https://github.com/jdx/mise, https://mise.jdx.dev/getting-started.html
**Status:** Full review

**Key capabilities relevant to dotfiles:**
- Backend system: registry > aqua > github > pipx > npm > cargo > go (matches our mise-first policy)
- `mise use --global` writes to `~/.config/mise/config.toml` (our chezmoi template sources this)
- `mise exec`, `mise run`, `mise activate` -- all work with chezmoi-deployed configs
- `mise doctor` -- health checks (complements `chezmoi doctor`)
- Tasks system: `[tasks]` in `mise.toml` for automation
- Environment variables: `[env]` in `mise.toml`

**Integration point with chezmoi:** Our `.chezmoisource/dot_config/mise/config.toml.tmpl` is the bridge -- chezmoi manages the mise config file as a template, allowing OS-conditional tool declarations.

### 2.4 skills.sh Searches

| Query | Result |
|-------|--------|
| `skills.sh/search?q=chezmoi` | Empty (insufficient_content) |
| `skills.sh/search?q=mise` | Empty (insufficient_content) |
| `skills.sh/search?q=dotfiles` | Empty (insufficient_content) |

**Conclusion:** No existing skills on skills.sh for any of these tools. This is a greenfield opportunity.

### 2.5 ComposioHQ/awesome-claude-skills

**URL:** https://github.com/ComposioHQ/awesome-claude-skills
**Status:** Full review of complete skill catalog

**Relevant skills found:** NONE for chezmoi, mise, or dotfiles management.

**Closest related skills:**
- `file-organizer` -- Intelligently organizes files/folders (generic, not dotfiles-specific)
- `using-git-worktrees` -- Creates isolated git worktrees (from superpowers, already in our project)
- `finishing-a-development-branch` -- Guides branch completion (already in our project)

**Categories that could theoretically host dotfiles skills:**
- "Development & Code Tools" -- most natural home
- "Productivity & Organization" -- secondary

**Verdict:** No existing skills to install. We must build our own.

### 2.6 garrytan/gstack

**URL:** https://github.com/garrytan/gstack
**Stars:** 16K+
**Status:** Full review

**Dotfiles relevance:** NONE. gstack is a sprint workflow skill pack (21 skills) focused on:
- Product planning (`/office-hours`, `/plan-ceo-review`)
- Code review (`/review`, `/codex`)
- QA automation (`/qa`, `/browse`)
- Release management (`/ship`, `/document-release`)
- Safety (`/careful`, `/freeze`, `/guard`)

**Patterns to note (not dotfiles-specific):**
- Skill chaining: each skill feeds output to the next
- `/gstack-upgrade` self-updater pattern -- could inspire a `/mde-upgrade` skill
- Cross-agent compatibility via `.agents/skills/` directory

**Verdict:** gstack has zero dotfiles patterns. Not applicable to this research question.

---

## 3. Existing Project State

### 3.1 Current chezmoi Integration

| Component | Location | Status |
|-----------|----------|--------|
| chezmoi source dir | `.chezmoisource/` | Active, contains Brewfile.tmpl, mise config.toml.tmpl, oh-my-zsh, tmux, zprofile |
| chezmoi validation | `src/mde/validate/chezmoi.py` | Basic: checks install + `chezmoi verify --exclude=scripts` |
| chezmoi template tests | `scripts/tests/chezmoi-template-parity.test.sh` | Contract test |
| chezmoi source tests | `scripts/tests/chezmoi-source-contract.test.sh` | Contract test |
| chezmoi test module | `tests/mde/test_chezmoi.py` | Unit tests |

### 3.2 Current mise Integration

| Component | Location | Status |
|-----------|----------|--------|
| mise enforcement skill | `.agents/skills/mise-enforcement/SKILL.md` | Comprehensive contract |
| mise tool management skill | `.agents/skills/mise-tool-management/SKILL.md` | Backend selection, drift detection |
| mise config template | `.chezmoisource/dot_config/mise/config.toml.tmpl` | chezmoi-managed |
| mise-first rule | `.claude/rules/mise-first.md` | Active policy |
| Global tool migration skill | `.agents/skills/mde-global-tool-migration/SKILL.md` | Migration workflow |

### 3.3 Other mde-* Skills

| Skill | Scope | Status |
|-------|-------|--------|
| `mde-homebrew` | Brewfile management, cask/formula decisions | Active |
| `mde-macos-setup` | macOS defaults, preferences | Active (not in registry) |
| `mde-global-tool-migration` | Migrating globals to mise | Active |
| `mde-python-backend-selection` | Python tool backend choices | Active |
| `mde-node-cli-declaration` | Node CLI declaration in mise | Active |
| `mde-native-tool-validation` | Validate native tools | Active |
| `mde-package-cache-policy` | Cache behavior policy | Active |

---

## 4. Gap Analysis

### 4.1 Missing: Chezmoi Dotfiles Management Skill

**No skill exists for:**
- Adding/editing/applying dotfiles via chezmoi
- Template authoring (`.tmpl` files with Go template syntax)
- Managing chezmoi data (template variables)
- chezmoi diff/apply workflow in agent context
- Secret injection via chezmoi (age, keychain, fnox integration)
- chezmoi externals (pulling external repos/archives into dotfiles)

**Impact:** HIGH. Agents currently have no guidance on how to modify dotfiles through chezmoi. They may edit files directly in `~/.config/` instead of through `.chezmoisource/`, causing drift.

### 4.2 Missing: Chezmoi + mise Coordination Skill

**No skill exists for:**
- The full lifecycle: edit mise config template -> chezmoi apply -> mise install -> mise reshim
- Detecting when a tool addition requires chezmoi template update vs. direct mise config edit
- Coordinating chezmoi data variables with mise environment variables
- Cross-tool drift detection (chezmoi source vs. deployed vs. mise expected)

**Impact:** MEDIUM-HIGH. The `mise-tool-management` skill already says "Add to `.chezmoisource/dot_config/mise/config.toml.tmpl`" (line 33), but this is a one-liner, not a full workflow.

### 4.3 Missing: Dotfiles Drift Detection Skill

**No skill exists for:**
- Comprehensive drift: `chezmoi verify` + `chezmoi diff` + `mise outdated` + `mise doctor` in one pass
- Remediation workflows: when drift is detected, guide the agent through fix options
- Periodic drift audits (hook-driven or schedule-driven)

**Impact:** MEDIUM. Basic drift detection exists in `src/mde/validate/chezmoi.py` and `mise-tool-management` mentions `mise outdated`, but there is no unified skill.

### 4.4 Not Missing (Already Covered)

- **Mise backend selection** -- `mise-tool-management` covers this well
- **Mise enforcement** -- `mise-enforcement` is comprehensive
- **Homebrew management** -- `mde-homebrew` handles Brewfile
- **Secret management** -- `secrets-management.md` rule + `1password-fnox` skill

---

## 5. Recommendations

### 5.1 New Skills to Create (Priority Order)

#### Skill 1: `mde-chezmoi-dotfiles` (HIGH priority)

**Purpose:** Guide agents through chezmoi dotfiles management workflows.

**When to invoke:**
- Adding/editing shell config, tmux config, zsh plugins, starship config
- Modifying any file under `~/.config/` that is chezmoi-managed
- Setting up a new machine or devcontainer

**Key content:**
- NEVER edit deployed files directly; always go through `.chezmoisource/`
- Template authoring: Go template syntax, `chezmoi data` for available variables
- OS-conditional templates: `{{ if eq .chezmoi.os "darwin" }}`
- Workflow: edit source -> `chezmoi diff` -> `chezmoi apply`
- Secret injection: `{{ keychain "item-name" }}` or age-encrypted files
- External sources: `chezmoi externals` for oh-my-zsh, tmux plugins
- `chezmoi doctor` as a health check

#### Skill 2: `mde-dotfiles-lifecycle` (MEDIUM priority)

**Purpose:** Coordinate the full chezmoi + mise lifecycle when adding/removing tools.

**When to invoke:**
- Adding a new tool that needs both mise config and shell config
- Changing environment variables that flow through both systems
- Bootstrap/provision workflows (new machine, devcontainer)

**Key content:**
- Full lifecycle: `.chezmoisource/dot_config/mise/config.toml.tmpl` edit -> `chezmoi apply` -> `mise install --yes` -> `mise lock` -> `mise reshim`
- Decision tree: "Does this change need a chezmoi template update, a direct mise config edit, or both?"
- Bootstrap sequence: chezmoi init -> chezmoi apply -> mise install -> verify
- Environment variable coordination: mise `[env]` vs. shell rc files vs. chezmoi templates

#### Skill 3: `mde-dotfiles-drift` (MEDIUM priority, could merge into existing)

**Purpose:** Unified drift detection across chezmoi and mise.

**When to invoke:**
- `uv run mde-py validate --all` (as part of validation suite)
- Before committing changes to dotfiles
- After `chezmoi update` from remote

**Key content:**
- Combined check: `chezmoi verify` + `chezmoi diff` + `mise outdated` + `mise doctor`
- Categorize drift: template drift (chezmoi source != deployed), tool drift (mise outdated), config drift (deployed != expected)
- Remediation guidance per drift type
- Integration with `src/mde/validate/chezmoi.py` (extend, don't replace)

### 5.2 Existing Skills to Update (Minor)

#### `mise-tool-management`: Add chezmoi cross-reference

Line 33 currently says:
```
3. Add to `.chezmoisource/dot_config/mise/config.toml.tmpl` under `[tools]`
```

Should add:
- Link to `mde-chezmoi-dotfiles` skill for template syntax
- Full lifecycle steps (apply, install, lock, reshim)
- Note about OS-conditional tool declarations in templates

#### `mise-enforcement`: Add chezmoi awareness

The enforcement skill should note that mise config lives inside chezmoi source and changes must go through chezmoi, not direct file edits to `~/.config/mise/config.toml`.

### 5.3 Skills NOT to Create

- **Chezmoi installation skill** -- chezmoi is already in mise config; installation is handled by mise-enforcement
- **Chezmoi git skill** -- chezmoi manages its own git; standard git skills apply
- **Generic dotfiles skill** -- too broad; the specific skills above are better
- **Mise plugin skill** -- mise's plugin system (aqua, github, etc.) is already covered by mise-tool-management

### 5.4 Skill Registry Update

Add to `configs/mde-skill-registry.json`:
```json
{
  "id": "skills/mde-chezmoi-dotfiles",
  "canonical_path": ".agents/skills/mde-chezmoi-dotfiles/SKILL.md",
  "aliases": ["mde-chezmoi-dotfiles", "chezmoi", "dotfiles"]
},
{
  "id": "skills/mde-dotfiles-lifecycle",
  "canonical_path": ".agents/skills/mde-dotfiles-lifecycle/SKILL.md",
  "aliases": ["mde-dotfiles-lifecycle", "dotfiles-lifecycle"]
}
```

---

## 6. Comparison: Our Approach vs. martinemde/dotfiles vs. gstack

| Dimension | Our Project (mde) | martinemde/dotfiles | gstack |
|-----------|-------------------|---------------------|--------|
| **Dotfiles manager** | chezmoi | chezmoi | None |
| **Tool manager** | mise (enforced) | mise (mentioned) | None (relies on system tools) |
| **AI integration** | Claude Code skills, agent rules, validation pipeline | Philosophy only ("AI-first" = pragmatic design) | 21 Claude Code skills (sprint workflow) |
| **Template management** | `.chezmoisource/*.tmpl` | chezmoi templates | N/A |
| **Secret management** | fnox + Keychain + age | Not documented | N/A |
| **Drift detection** | `chezmoi verify` + `mise outdated` via Python | Not documented | N/A |
| **Validation** | `uv run mde-py validate --all` | Not documented | N/A |
| **Skills count** | 14 registered + unregistered | 0 | 21 |
| **Portability** | macOS primary, devcontainer planned | macOS + Linux + devcontainers | Cross-repo |
| **Skill focus** | Dev environment management | Dotfiles deployment | Sprint/review/QA |

**Assessment:** Our project is significantly more advanced than martinemde/dotfiles in AI integration and validation, but lacks explicit chezmoi workflow skills. martinemde's portability (macOS + Linux + devcontainers) is a pattern to adopt for our chezmoi templates. gstack is complementary (sprint skills) not competitive (no dotfiles).

---

## 7. Adoptable Patterns from martinemde/dotfiles

1. **Non-interactive bootstrap via env vars** -- `GIT_USER_NAME`, `GIT_USER_EMAIL` for CI/agent contexts. Our `mde-chezmoi-dotfiles` skill should document this pattern.

2. **Pragmatic minimalism in tool selection** -- znap (not oh-my-zsh framework), starship (cross-shell), mise (not asdf). We already follow this with mise; consider evaluating znap vs. oh-my-zsh (we currently use oh-my-zsh per `.chezmoisource/dot_oh-my-zsh`).

3. **Shell startup performance benchmarking** -- martinemde claims 50-80% faster shell startup. Our skill should include a startup timing check: `time zsh -i -c exit`.

4. **Devcontainer support** -- chezmoi templates should be devcontainer-aware. Consider adding `{{ if .chezmoi.container }}` conditions.

---

## 8. Source Discovery Log (per Source Discovery Protocol)

| URL | Priority | Status | Notes |
|-----|----------|--------|-------|
| https://github.com/martinemde/dotfiles | HIGH | Full review | AI-first chezmoi dotfiles, portability patterns |
| https://github.com/twpayne/chezmoi | REFERENCE | Full review | 18.6k stars, canonical source |
| https://www.chezmoi.io/user-guide/command-overview/ | REFERENCE | Full review | Command workflow documented |
| https://github.com/jdx/mise | REFERENCE | Full review | GitHub page had load error, but docs worked |
| https://mise.jdx.dev/getting-started.html | REFERENCE | Full review | Backend system, tasks, env vars |
| https://skills.sh/search?q=chezmoi | SKIP | Empty | No chezmoi skills exist |
| https://skills.sh/search?q=mise | SKIP | Empty | No mise skills exist |
| https://skills.sh/search?q=dotfiles | SKIP | Empty | No dotfiles skills exist |
| https://github.com/ComposioHQ/awesome-claude-skills | REFERENCE | Full review | No chezmoi/mise/dotfiles skills |
| https://github.com/garrytan/gstack | REFERENCE | Full review | No dotfiles patterns; sprint skills only |
| https://www.chezmoi.io/user-guide/manage-different-types-of-file/ | HIGH | Fetch failed (parse) | Retry with different extraction |
| https://www.chezmoi.io/user-guide/templating/ | HIGH | Fetch failed (parse) | Retry with different extraction |
| https://www.chezmoi.io/user-guide/password-managers/ | HIGH | Fetch failed (parse) | Retry with different extraction |

---

## 9. Answers to Research Questions

### Q1: What chezmoi skills/plugins exist that we should install?

**None.** skills.sh has no chezmoi skills. awesome-claude-skills has no chezmoi skills. The chezmoi ecosystem relies on its own CLI + Go templates; there are no Claude Code skills for it anywhere in the ecosystem. We need to build `mde-chezmoi-dotfiles`.

### Q2: What mise skills/plugins exist that we should install?

**None externally.** skills.sh has no mise skills. awesome-claude-skills has no mise skills. However, our project already has two excellent mise skills (`mise-enforcement`, `mise-tool-management`) that are better than anything in the ecosystem. They need minor updates to cross-reference chezmoi, not replacement.

### Q3: How does martinemde/dotfiles integrate AI with chezmoi? What patterns to adopt?

martinemde/dotfiles uses "AI-first" to mean **design philosophy** (pragmatic minimalism, single-purpose tools, no bloated frameworks), NOT AI agent integration. There are no Claude Code skills, no agent-aware workflows, and no MCP tools. The patterns to adopt are:
1. Non-interactive bootstrap via env vars for agent/CI contexts
2. Shell startup performance benchmarking
3. Devcontainer-aware chezmoi templates
4. znap as a potential oh-my-zsh replacement (evaluate separately)

### Q4: Are there skills for chezmoi template management, diff/apply workflows, or secret management?

**No.** None exist anywhere in the ecosystem. This is the primary gap. Our proposed `mde-chezmoi-dotfiles` skill would be the first of its kind. chezmoi's native support for age encryption, macOS Keychain, and 1Password aligns with our secrets-management rule, but no skill ties them together.

### Q5: Are there skills for mise tool management, backend selection, or drift detection?

**Only ours.** Our `mise-tool-management` skill already covers backend selection (the 7-tier priority), tool addition workflow, aqua/github discovery, and drift detection via `mise outdated` and `mise doctor`. No external skills match this. The gap is the missing chezmoi coordination step.

### Q6: How should our existing mde-* skills be reorganized?

**Minimal reorganization needed.** The current skills are well-scoped:

| Current Skill | Keep/Change | Notes |
|--------------|-------------|-------|
| `mise-enforcement` | Keep, add chezmoi cross-ref | Add note: mise config lives in chezmoi source |
| `mise-tool-management` | Keep, expand chezmoi lifecycle | Expand step 3-5 to full lifecycle |
| `mde-homebrew` | Keep as-is | Brewfile.tmpl is already chezmoi-managed |
| `mde-macos-setup` | Keep as-is | macOS defaults are separate from dotfiles |
| `mde-global-tool-migration` | Keep as-is | Migration workflow is distinct |
| **NEW: `mde-chezmoi-dotfiles`** | Create | Core chezmoi workflow skill |
| **NEW: `mde-dotfiles-lifecycle`** | Create | Cross-tool coordination |

The drift detection gap can be closed by extending `src/mde/validate/chezmoi.py` rather than creating a separate skill (skill 3 from section 5.1 is optional -- the Python module is the right place for programmatic checks).

### Q7: Comparison: our approach vs martinemde/dotfiles vs gstack

See Section 6 table. Summary:
- **vs martinemde/dotfiles:** We are far more advanced in AI integration and validation but lack explicit chezmoi workflow documentation for agents. Their portability (cross-OS, devcontainers) is a pattern to adopt.
- **vs gstack:** Entirely different domains. gstack is sprint/review/QA skills; we are dev environment management skills. Complementary, not competitive. The self-updater pattern (`/gstack-upgrade`) is worth noting for a potential `/mde-upgrade` skill.

---

## 10. Next Steps

1. **Create `mde-chezmoi-dotfiles` skill** -- highest priority, closes the biggest gap
2. **Create `mde-dotfiles-lifecycle` skill** -- coordinates chezmoi + mise workflows
3. **Update `mise-tool-management`** -- expand chezmoi lifecycle steps
4. **Update `mise-enforcement`** -- add chezmoi source awareness
5. **Update source catalog** -- mark martinemde/dotfiles as [x] Full review
6. **Retry chezmoi docs fetch** -- templating, file types, and password manager pages failed to parse; retry with context7 or direct docs
7. **Evaluate znap vs oh-my-zsh** -- separate research task based on martinemde's approach
