# Community Plugin Deep Reviews — Batch 1: Token/Context/Safety

**Date**: 2026-03-26
**Agent**: claude-opus-4.6 (subagent batch evaluator)
**Plugins reviewed**: cc-boost, token-saver, claude-md-optimizer, bake-claude-md-files, claude-memory-compactor, claude-code-safety-net, claude-impact-analysis, scan-modules-plugin

---

## 1. cc-boost — REJECT

- **Components**: skills=0, agents=0, cmds=0, hooks=2 (Setup + PreToolUse)
- **Policy conflicts**: Node.js hooks (not Python); hardcoded install path
- **Overlap**: High with token-saver (same domain)
- **Rationale**: Chinese-language plugin with narrower feature set than token-saver. Node.js hooks conflict with no-shell-scripts policy. Token-saver covers same domain with 21 processors vs cc-boost's handful.

## 2. token-saver — INSTALL

- **Components**: skills=1, agents=0, cmds=1, hooks=2 (PreToolUse + SessionStart)
- **Policy conflicts**: None — hooks are Python
- **Overlap**: Minor — no output compression exists today
- **Rationale**: 94% test coverage, Apache 2.0, v2.1.1. 21 specialized processors for git/pytest/docker/npm/ruff. 60-99% token savings. Python hooks. Minimal context footprint.

## 3. claude-md-optimizer — REJECT

- **Components**: skills=1, agents=0, cmds=0, hooks=0
- **Policy conflicts**: None
- **Overlap**: High — mde already has progressive disclosure via .claude/rules/
- **Rationale**: Automates what mde already did manually. CLAUDE.md already under 100-line target. One-time task, not ongoing need.

## 4. bake-claude-md-files — EXTRACT

- **Components**: skills=1, agents=0, cmds=0, hooks=0
- **Policy conflicts**: None
- **Overlap**: Partial with hk.pkl, ruff, quality gate
- **Rationale**: Converting CLAUDE.md rules to automated checks is excellent methodology. mde already did most of this. EXTRACT: audit remaining .claude/rules/ for conversion to ruff rules or hk.pkl checks.

## 5. claude-memory-compactor — REJECT

- **Components**: skills=1, agents=0, cmds=0, hooks=0 (installed via shell script)
- **Policy conflicts**: Critical — bash install.sh writes inline bash to settings.json; bash -c wrapper with triple-escaped Python
- **Overlap**: High with context-budget policy + remember plugin
- **Rationale**: Unmaintainable bash/Python hybrid. 30-line threshold too aggressive for 200-line MEMORY.md policy. Concept trivial to reimplement as Python module if needed.

## 6. claude-code-safety-net — INSTALL

- **Components**: skills=0, agents=0, cmds=3, hooks=1 (PreToolUse)
- **Policy conflicts**: Node.js guard utility (acceptable precedent)
- **Overlap**: None — no destructive command blocking exists
- **Rationale**: Mature v0.8.2 plugin blocking git reset --hard, rm -rf, git push --force. Handles nested bash -c unwrapping (5 levels), interpreter one-liners, xargs rm, find -delete. Enforces worktree-pr-workflow mechanically.

## 7. claude-impact-analysis — REJECT

- **Components**: skills=0, agents=0, cmds=0, hooks=1 (PreToolUse on Edit|Write)
- **Policy conflicts**: Node.js hook; requires .impactrc.json (violates declarative-config)
- **Overlap**: Partially addressed by quality gate
- **Rationale**: 10s timeout per edit adds noise for 58-module project. Basic grep-based import analysis. Quality gate already catches breaking changes. pydeps or importlab better fits.

## 8. scan-modules-plugin — REJECT

- **Components**: skills=1, agents=0, cmds=1, hooks=1 (SessionStart)
- **Policy conflicts**: Critical — bash SessionStart hook, generates bash post-commit hook conflicting with hk.pkl, auto-modifies CLAUDE.md
- **Overlap**: Partial with CLAUDE.md architecture section
- **Rationale**: 404-line SKILL.md is extremely context-heavy. Overkill for 58-module project. On-demand Grep is fast enough.
