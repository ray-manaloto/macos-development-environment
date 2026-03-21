# Dotfiles + Agent Orchestration: Adoption Checklist

**Research Date:** 2026-03-21
**Status:** Ready for implementation
**Priority Tiers:** Immediate (Week 1) → Near-term (Weeks 2-4) → Medium-term (Weeks 5-8)

---

## Tier 1: Immediate Adoption (Week 1) — Golden Patterns from Other Projects

These are proven patterns from existing projects that we should adopt NOW. Zero implementation risk.

### ✅ Pattern 1: barnabasJ's agents/ Folder Structure

**What to do:**
Ensure agents/ folder is properly ignored by chezmoi and correctly symlinked.

**Checklist:**
- [ ] Verify `.chezmoiignore` includes:
  ```
  .agents/
  .claude/agents/
  .claude/skills/
  agents/                    # If we add agents/ folder like barnabasJ
  ```
- [ ] Verify symlinks in `dot_claude/`:
  ```
  ~/.claude/CLAUDE.md → ~/.local/share/chezmoi/agents/AGENTS.md
  ~/.claude/commands/ → ~/.local/share/chezmoi/agents/commands/
  ```
- [ ] Run `chezmoi verify` to ensure no conflicts
- [ ] Document pattern in `.claude/agents/README.md`

**Evidence:** barnabasJ/dotfiles successfully uses this pattern (17 command files symlinked)

**Effort:** 2 hours

**Owner:** chezmoi-specialist agent

---

### ✅ Pattern 2: Global AI Preferences via Symlink

**What to do:**
Create single source of truth for AI preferences (Claude Code, Codex, potential future tools)

**Checklist:**
- [ ] Create `~/.config/aide/CLAUDE_PREFERENCES.md` (or equivalent)
  - Copy current content from `~/.claude/CLAUDE.md`
  - Add sections: code-style, testing, security, git conventions
- [ ] Create symlink: `~/.claude/CLAUDE.md` → `~/.config/aide/CLAUDE_PREFERENCES.md`
- [ ] Verify via `chezmoi verify` (should show symlink, not conflict)
- [ ] Document symlink strategy in `.claude/README.md`

**Evidence:** jalexandercarr/dotfiles uses this successfully (no drift between agents)

**Effort:** 3 hours

**Owner:** chezmoi-specialist agent

---

### ✅ Pattern 3: Specialist Agent YAML Headers

**What to do:**
Standardize YAML frontmatter across all specialist agents

**Checklist:**
- [ ] Review current agent specs:
  ```bash
  cat .claude/agents/chezmoi-specialist.md | head -10
  cat .claude/agents/mise-specialist.md | head -10
  cat .claude/agents/brew-specialist.md | head -10
  ```
- [ ] Ensure all follow this format:
  ```yaml
  ---
  name: chezmoi-specialist
  description: Chezmoi expert for dotfile management
  tools: Read, Glob, Grep, Bash
  skills: [chezmoi-config, dotfiles-team]
  model: haiku
  memory: project
  disallowedTools: WebFetch, WebSearch
  ---
  ```
- [ ] Add `disallowedTools` to all agents (safety constraint)
- [ ] Add `skills:` array to all agents
- [ ] Run automated validation:
  ```bash
  uv run mde-py validate agents
  ```

**Evidence:** Aristoddle/beppe-dotfiles-docs uses strict YAML headers

**Effort:** 2 hours

**Owner:** claude-code-specialist agent

---

### ✅ Pattern 4: Adopt terrylica/cc-skills as Reference

**What to do:**
Review and reference terrylica's cc-skills ecosystem (85K+ installs combined)

**Checklist:**
- [ ] Review https://github.com/terrylica/cc-skills
  - chezmoi-workflows skill (85 installs, most popular)
  - mise-tasks skill (114 installs)
  - mise-configuration skill (63 installs)
- [ ] Document which patterns to adopt:
  - Chezmoi interactive drift detection (from chezmoi-workflows)
  - Mise task orchestration patterns
- [ ] Update `.claude/skills/README.md` with references
- [ ] Note: terrylica uses public GitHub as skill source (adopt this pattern)

**Evidence:** terrylica/cc-skills is the most-installed chezmoi/mise skill ecosystem

**Effort:** 4 hours (review only, no code changes)

**Owner:** researcher agent

---

## Tier 2: Near-Term Implementation (Weeks 2-4) — High-Impact Gaps

These require design + implementation but have clear ROI.

### 🔴 Gap 1: Drift Detection Agent (Weeks 1-2)

**What to do:**
Implement automated detection of chezmoi drift with periodic verification

**Design:**
```
drift-detection-agent:
  - Trigger: Daily at 2 AM (mise task)
  - Operation:
    1. Run: chezmoi verify
    2. If failed: Compare with chezmoi diff
    3. Log drift to ~/.local/state/chezmoi-drift.log
    4. Option A: Auto-repair (chezmoi apply)
    5. Option B: Alert user (create GitHub issue)
    6. Metrics: time to detect, time to repair, drift size
  - Output: Drift report (daily, weekly summary)
```

**Checklist:**
- [ ] Design drift detection agent in `.claude/agents/drift-detection-agent.md`
- [ ] Create Python implementation in `src/mde/agents/drift_detection.py`
- [ ] Add `chezmoi verify` command to mde-py CLI
- [ ] Create mise task:
  ```toml
  [tasks.drift-check]
  run = "uv run mde-py drift-detect --auto-repair false"
  cron = "0 2 * * *"  # Daily at 2 AM
  ```
- [ ] Implement drift logging to `~/.local/state/chezmoi-drift.log`
- [ ] Create test cases:
  - Normal state (no drift)
  - Manual edit drift (user edited file)
  - Version conflict (upstream changed)
- [ ] Document in `.claude/skills/drift-detection/SKILL.md`

**Evidence:**
- All reviewed projects lack this (gap confirmed)
- Chezmoi verify API is simple, low-risk
- Nightly execution avoids performance impact

**Effort:** 1-2 weeks

**Expected Impact:** +0.10 points (drift is #1 failure reason)

**Owner:** drift-detection-agent (new), chezmoi-specialist (support)

---

### 🔴 Gap 2: Lifecycle Coordinator Agent (Weeks 3-4)

**What to do:**
Orchestrate brew → mise → chezmoi in dependency order with validation

**Design:**
```
lifecycle-coordinator-agent:
  - Input: List of tools to install
  - Operation:
    1. Analyze dependency graph (brew deps, mise tool versions, chezmoi templates)
    2. Install in order: brew → mise base → mise tools → chezmoi
    3. Validate each step before proceeding
    4. Metrics: time per step, validation failures
    5. Rollback on critical failures
  - Output: Provisioning report with timing per step
```

**Checklist:**
- [ ] Design lifecycle coordinator in `.claude/agents/lifecycle-coordinator-agent.md`
- [ ] Create Python implementation in `src/mde/agents/lifecycle_coordinator.py`
- [ ] Implement dependency graph:
  - Parse Brewfile for package deps
  - Parse mise.toml for tool versions
  - Parse chezmoi templates for required values
- [ ] Create orchestration workflow:
  ```python
  coordinator = LifecycleCoordinator()
  coordinator.install_brew(packages)
  coordinator.install_mise(config)
  coordinator.apply_chezmoi()
  coordinator.validate()
  ```
- [ ] Add validation steps after each phase
- [ ] Create mise task:
  ```toml
  [tasks.bootstrap]
  run = "uv run mde-py provision --validate"
  ```
- [ ] Test on new machine (or VM)
- [ ] Document idempotency (should be safe to run 2x)

**Evidence:**
- All reviewed projects lack this (gap confirmed)
- Bootstrap currently imperative (pelted/.dotfiles)
- High pain point for new developers

**Effort:** 2-3 weeks

**Expected Impact:** +0.12 points (new machine setup pain relief)

**Owner:** lifecycle-coordinator-agent (new), mise-specialist (support)

---

## Tier 3: Medium-Term Implementation (Weeks 5-8) — Supporting Gaps

These have lower priority but add robustness.

### 🟡 Gap 3: Shell Performance Monitoring Skill (Week 5-6)

**What to do:**
Add startup time benchmarking with regression detection

**Design:**
```
shell-performance-skill:
  - Trigger: On `chezmoi apply` completion
  - Measurement:
    1. Measure ~/.zshrc load time (hyperfine or zsh -i -c exit)
    2. Measure ~/.bashrc load time
    3. Compare to baseline
    4. Alert if regression > 50ms
  - Output: Performance report in ~/.local/state/shell-perf.csv
```

**Checklist:**
- [ ] Create `.claude/skills/shell-performance-monitoring/SKILL.md`
- [ ] Select benchmarking tool:
  - Option A: hyperfine (https://github.com/sharkdp/hyperfine)
  - Option B: builtin zsh profiling (zsh -xi 2>&1)
  - Recommendation: hyperfine (external tool, accurate)
- [ ] Add to mise config:
  ```toml
  [tools]
  hyperfine = { version = "latest", github = "sharkdp/hyperfine" }
  ```
- [ ] Create shell-perf measurement script:
  ```bash
  hyperfine \
    "zsh -i -c exit" \
    "bash -i -c exit"
  ```
- [ ] Store baseline in `~/.config/shell-perf-baseline.json`
- [ ] Create post-chezmoi-apply hook to run measurement
- [ ] Implement regression alert in post-apply hook

**Evidence:**
- DarkPhilosophy/zsh-bench tool exists (but not integrated)
- pelted/.dotfiles mentions "fast startup" but no metrics
- Easy win for shell startup performance

**Effort:** 1 week

**Expected Impact:** +0.06 points (DX improvement)

**Owner:** shell-performance skill (new)

---

### 🟡 Gap 4: Secret Rotation Agent (Weeks 7-8)

**What to do:**
Monitor secret expiration dates and alert for rotation

**Design:**
```
secret-rotation-agent:
  - Trigger: Weekly on Sunday 9 AM
  - Operation:
    1. Query 1Password for expiring secrets (API)
    2. Query age-encrypted files for metadata
    3. Query Keychain for certificate expiry (macOS)
    4. Compile list of expiring secrets (< 14 days)
    5. Alert: Create GitHub issue or send notification
    6. Auto-rotate if framework supports
  - Output: Secret rotation report with expiry dates
```

**Checklist:**
- [ ] Design secret-rotation-agent in `.claude/agents/secret-rotation-agent.md`
- [ ] Implement in `src/mde/agents/secret_rotation.py`:
  - 1Password API integration (op CLI)
  - age metadata extraction
  - Keychain query (macOS security)
- [ ] Create alert mechanism:
  - GitHub issue creation (gh CLI)
  - Slack notification (optional)
  - Email (optional)
- [ ] Create mise task:
  ```toml
  [tasks.check-secrets]
  run = "uv run mde-py secret-check --alert github"
  cron = "0 9 * * 0"  # Weekly Sunday 9 AM
  ```
- [ ] Implement 14-day warning threshold
- [ ] Add test cases:
  - Secret expiring in 30 days (no alert)
  - Secret expiring in 10 days (alert)
  - Expired secret (critical alert)
- [ ] Document audit trail

**Evidence:**
- No reviewed projects implement this (gap confirmed)
- Security/compliance critical
- Integration with fnox already in our stack

**Effort:** 2 weeks

**Expected Impact:** +0.08 points (security/compliance)

**Owner:** secret-rotation-agent (new)

---

## Tier 4: Lower Priority (Weeks 9+) — Nice to Have

### 🟢 Gap 5: Bootstrap Validation (Week 9)

**Checklist:**
- [ ] Design bootstrap-validator-agent
- [ ] Create idempotency tests
- [ ] Health checks before/after
- [ ] Timing metrics per step
- [ ] Rollback capability

**Expected Impact:** +0.05 points

---

### 🟢 Gap 6: Skill Discovery & Sync

**Checklist:**
- [ ] Design skill-discovery-agent
- [ ] Integrate with awesome-claude-skills registry
- [ ] Create skills-lock.json versioning
- [ ] Implement auto-update for patch versions

**Expected Impact:** +0.05 points

---

## Overall Implementation Timeline

| Week | Phase | Tasks | Agent Owner |
|------|-------|-------|-------------|
| **1** | **Immediate Adoption** | barnabasJ pattern, jalexandercarr symlinks, YAML headers, terrylica review | chezmoi-specialist, claude-code-specialist |
| **2** | **Drift Detection** | Agent design, Python impl, mise task, logging | drift-detection-agent |
| **3-4** | **Lifecycle Coordinator** | Agent design, dependency graph, orchestration, tests | lifecycle-coordinator-agent |
| **5-6** | **Shell Performance** | Skill design, hyperfine integration, regression detection | shell-performance-skill |
| **7-8** | **Secret Rotation** | Agent design, 1Password/age/Keychain integration, alerting | secret-rotation-agent |
| **9+** | **Lower Priority** | Bootstrap validation, skill discovery | Future agents |

---

## Success Metrics

| Metric | Target | Owner |
|--------|--------|-------|
| Drift detection latency | < 5 seconds | drift-detection-agent |
| Lifecycle provisioning time | < 15 minutes | lifecycle-coordinator-agent |
| Shell startup regression detection | ± 50ms threshold | shell-performance-skill |
| Secret rotation alert accuracy | 100% (no missed expirations) | secret-rotation-agent |
| Overall improvement score | 0.91 (from 0.450 baseline) | researcher |

---

## References

### Key Projects

1. **barnabasJ/dotfiles** — https://github.com/barnabasJ/dotfiles (agents/ folder pattern)
2. **jalexandercarr/dotfiles** — https://github.com/jalexandercarr/dotfiles (symlink strategy)
3. **terrylica/cc-skills** — https://github.com/terrylica/cc-skills (most-installed chezmoi/mise)
4. **Aristoddle/beppe-dotfiles-docs** — https://github.com/Aristoddle/beppe-dotfiles-docs (Phase 6 research)
5. **DarkPhilosophy/zsh-bench** — https://github.com/DarkPhilosophy/zsh-bench (shell perf tool)

### Tools to Integrate

- **hyperfine** — Shell startup benchmarking
- **chezmoi verify** — Drift detection
- **1Password API** — Secret query
- **op CLI** — 1Password integration
- **age** — Secret encryption
- **fnox** — Secret access in agent context

---

## Approval & Sign-Off

- **Researcher:** Approved research findings (2026-03-21)
- **Implementation:** Ready for Phase 1 (drift detection)
- **Community:** Open source reference implementation potential
- **Timeline:** 9-10 weeks to +0.46 improvement (0.91 baseline)
