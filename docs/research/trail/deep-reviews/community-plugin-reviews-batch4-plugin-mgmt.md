# Community Plugin Deep Reviews — Batch 4: Plugin Management/Skills

**Date**: 2026-03-26
**Agent**: claude-opus-4.6 (subagent batch evaluator)
**Plugins reviewed**: skill-doctor, skill-validator, skill-provenance

---

## 1. skill-doctor — EXTRACT

- **Components**: skills=3 (skill-doctor, treat, rollback), agents=0, cmds=0, hooks=0
- **Policy conflicts**: None
- **Overlap**: HIGH with rsm-subagents-dev skill and uv run mde-py validate --plugins

**Rationale**: Well-designed 3-skill plugin for auditing/upgrading skills with staging directories and rollback. The `best-practices.md` reference file (12 checklist items covering frontmatter, dynamic injection, overlap detection, model override, context isolation, security) is more comprehensive than existing rsm-subagents-dev skill.

Reasons not to install:
1. Overlaps mde-py validate --plugins (structure, frontmatter, forbidden keys, references, agents, hooks)
2. Overlaps rsm-subagents-dev skill
3. Depends on `claude-code-guide` subagent type (undeclared dependency)
4. Depends on `skill-creator` plugin's `quick_validate.py` (undeclared dependency)

**Extract**: `best-practices.md` 12-item checklist — add as reference file to rsm-subagents-dev skill. The staging + backup + rollback workflow pattern is good UX but not needed given worktree-based workflow.

---

## 2. skill-validator — REJECT

- **Components**: skills=0, agents=0, cmds=2, hooks=0
- **Policy conflicts**: Node.js validation logic (skill-validator.js, 13K+ tokens)
- **Overlap**: COMPLETE with uv run mde-py validate --plugins

**Rationale**: Node.js-based validation tool with /skill-validate and /skill-validate-fix commands. Complete functional overlap with src/mde/validate/plugins.py which already performs frontmatter validation, reference integrity, forbidden keys, agent/command/skill fields, and hooks.json validation. Wrong language (JavaScript when project mandates Python). Japanese documentation. The --fix auto-repair feature is interesting but not unique enough to justify overhead.

---

## 3. skill-provenance — REJECT

- **Components**: skills=1, agents=0, cmds=0, hooks=0
- **Policy conflicts**: 2 shell scripts (validate.sh 213 lines, package.sh 364 lines)
- **Overlap**: Partial with YAML provenance tracking in research pipeline

**Rationale**: Sophisticated metaskill (v4.8.0, 500+ line SKILL.md) for version-tracking skill bundles with MANIFEST.yaml, SHA-256 hashes, changelogs, cross-platform metadata, and .skill ZIP packaging targeting agentskills.io.

Rejection reasons:
1. Shell scripts (validate.sh, package.sh) violate no-shell-scripts policy
2. Wrong scope — designed for distributing skills across multiple platforms; mde uses skills locally via rsm-subagents
3. Overkill versioning — plugin.json version + git history already sufficient
4. 500+ line SKILL.md would consume substantial context budget
5. Partial overlap with existing YAML provenance tracking
