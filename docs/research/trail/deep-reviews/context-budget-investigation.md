# Context Budget Crisis Investigation

## Executive Summary

**PRIORITY: CRITICAL**

The plugin configuration is loading **244 agents and 88 skills** (~14,840 tokens) into Claude Code's routing system when the migration spec explicitly requires **empty `enabledPlugins`**. This violates the "Absolute minimum viable complexity" principle and degrades routing accuracy for the 10 new native agents.

**Status: Spec not yet implemented (Phase 4, Step 16 incomplete)**

## Investigation Results

### 1. Plugin Inventory

#### Project Level (.claude/settings.json)
- **4 enabled plugins** with 25 agents total
  - `python-development@claude-code-workflows` (to disable)
  - `shell-scripting@claude-code-workflows` (to disable)
  - `developer-essentials@claude-code-workflows` (to disable)
  - `conductor@claude-code-workflows` (to disable)
- **Status:** NOT YET SET TO EMPTY (migration spec violation)

#### User Level (~/.claude/settings.json)
- **79 enabled plugins** with ~1,100+ cached agent/skill descriptions
  - 3 marketplaces: claude-code-workflows (64 plugins), claude-plugins-official (14), docker (2)
  - Includes irrelevant domains: blockchain-web3, payment-processing, SEO, HR-legal, UI-design
  - Config inheritance: project settings override user, but cached plugins still available for loading

### 2. Token Cost Analysis

**Routing Signal Cost (estimated):**
```
244 agents × 50 tokens/agent description = 12,200 tokens
88 skills × 30 tokens/skill description = 2,640 tokens
─────────────────────────────────────────────────────
Total agent/skill descriptions = ~14,840 tokens
% of Haiku context (200K): 0.007% (negligible)
% of Haiku practical window (50K after system): 0.03% (minimal)
% of Haiku problem-solving budget (30K): 0.05% (OBSERVABLE)
```

**Reality check:** The 244 agents consume ~5-7% of usable Haiku context. For a Haiku-class task (e.g., "fix typo in README"), this is significant.

### 3. Spec Violation Evidence

**Migration Checklist (Phase 4, Step 16):**
```
[ ] 16. **EDIT** `.claude/settings.json`: set `enabledPlugins` to `{}`
```
**Current status:** NOT CHECKED. The 4 plugins listed in Section 7.1 for deletion are still enabled.

**Section 7.1 Rationale:**
| Plugin | Should Disable | Reason |
|--------|---|---|
| python-development | YES | Generic Python advice wastes context; our rules are more specific |
| shell-scripting | YES | We have a no-shell-scripts policy |
| developer-essentials | YES | Generic; our CLAUDE.md + rules provide better guidance |
| conductor | YES | claude-flow ecosystem dependency |

**Why conductor is problematic:**
- It's from the claude-flow era (which was explicitly removed per Section 10.1)
- Native Claude Code subagents + Agent Teams replace it (Section 9, Pattern #2)
- Its presence signals incomplete migration cleanup

### 4. Routing Performance Impact

**Before (current state):**
- New agents (10) searching ranking space of 244 agents
- Pre-task hooks call `npx @claude-flow/cli@latest hooks pre-task --description "<task>"`
- Router must evaluate 244 agent descriptions to find best match for task

**After (spec compliance):**
- New agents (10) searching ranking space of 10 agents
- Same hook call completes faster with less context waste
- Routing decisions more accurate (less noise in evaluation)

**Estimated speedup:** 2-3x faster for pre-task routing in Haiku mode (unvalidated, needs benchmark)

### 5. Conflict with Project Rules

The 4 enabled plugins directly violate project policies:

| Rule | Conflict | Resolution |
|------|----------|-----------|
| `library-first.md` | generic plugins reduce dependency on battle-tested libraries | disable generic plugins |
| `no-shell-scripts.md` | shell-scripting plugin conflicts with policy | disable shell-scripting |
| `declarative-config.md` | python-development plugin generic advice wastes space | disable python-development |
| `declarative-config.md` | developer-essentials is generic | disable developer-essentials |

### 6. Root Cause

The migration spec was written in detail, but **Phase 4 (Hook & Plugin cleanup) was never executed**. The project has:
- ✅ Created 10 new agent files (Phase 3)
- ✅ Created new rules (Phase 2)
- ❌ Disabled legacy plugins (Phase 4, Step 16 NOT DONE)
- ❌ Added new hooks (Phase 4, Steps 14-15 NOT DONE)

This is a **migration pause state**, not a deployment.

## Gaps Identified

1. **Unknown:** Whether /reload-plugins command counts project-only agents or includes user-level plugins too
2. **Unknown:** Exact context cost once user-level plugins are filtered (current ~/.claude/settings.json has 79 enabled)
3. **Unknown:** Whether pre-task hook routing latency has degraded (no baseline benchmark before/after)
4. **Unknown:** Impact on agent selection accuracy (are wrong agents sometimes chosen due to noise?)
5. **Unknown:** Whether the 25 project agents include duplicates (same agent defined in multiple files?)

## Recommendation

**Execute Migration Phase 4 immediately:**

```bash
# Step 1: Disable legacy plugins
# Edit .claude/settings.json: change enabledPlugins to {}

# Step 2: Verify no regressions
# Run /reload-plugins and confirm:
#   - Agent count drops from 244 to ~10
#   - Project agents still present: researcher, coder, tester, reviewer, ...
#   - User agents NOT loaded (because enabledPlugins={} at project level)

# Step 3: Test pre-task routing
# Run any task and verify pre-task hook still recommends correct agent

# Step 4: Commit
# git commit -m "fix: disable legacy plugins per migration spec Phase 4, Step 16"
```

**Timeline:** Complete within 1 working session (< 30 minutes)

## Related Findings

- See `finding-context-budget-crisis.yaml` for structured data
- Check migration spec Section 7.1 for plugin disable rationale
- See migration spec Section 10.1 for why claude-flow was removed

## Appendix: Current Plugin Count Breakdown

```
Project agents:        25 (from 10 agent files)
User-level plugins:    79 (enabled in ~/.claude/settings.json)
User-level agents/skills cached: 1,116 (across 3 marketplaces)

Total agents visible to /reload-plugins: 244
Total skills visible to /reload-plugins: 88

Plugin breakdown:
  - claude-code-workflows: 64 (mostly disabled, 4 enabled at project level)
  - claude-plugins-official: 14 (all enabled at user level)
  - docker: 2 (beta-mcp-skills, mcp-toolkit — both enabled)
```

