---
name: self-audit
description: >
  This skill should be used when the user asks to "audit evaluator", "check for replacement",
  "can another plugin replace this", "self-audit marketplace evaluator", "is there a better
  evaluator plugin", or "should we replace marketplace-evaluator".
  Checks if any community plugin now provides the same functionality as this plugin,
  and whether this plugin should be improved or replaced.
allowed-tools: [Read, Glob, Grep, Bash, Agent]
---

# Self-Audit: Can This Plugin Be Replaced?

Check whether a community plugin now does what marketplace-evaluator does, and whether
this plugin should be improved or replaced.

## Audit Process

### Step 1: Define Own Capabilities

Read this plugin's skills and agents to enumerate what it provides:
1. Marketplace screening across multiple marketplaces
2. Goal-based evaluation with configurable criteria
3. Multi-model deep review (Claude + Codex)
4. Persistent repo-based output (JSON + markdown)
5. Meta-learning from past evaluations
6. Self-audit for replacement detection

### Step 2: Search for Competitors

1. Read the latest evaluations JSON for plugins tagged with `plugin-finding` or `plugin-management` goals
2. Search marketplace descriptions for keywords: "evaluate plugins", "plugin audit", "marketplace scan", "skill doctor", "plugin manager"
3. Check installed plugins for overlapping capabilities

### Step 3: Compare

For each candidate competitor:

| Criterion | marketplace-evaluator | Competitor |
|-----------|----------------------|------------|
| Multi-marketplace scan | Yes/No | Yes/No |
| Goal-based filtering | Yes/No | Yes/No |
| Multi-model review | Yes/No | Yes/No |
| Repo-persisted output | Yes/No | Yes/No |
| Meta-learning | Yes/No | Yes/No |
| Self-audit | Yes/No | Yes/No |

### Step 4: Recommend

- **KEEP**: No competitor covers all capabilities
- **IMPROVE**: Competitor does X better — extract pattern, add to this plugin
- **REPLACE**: Competitor fully supersedes this plugin — recommend migration plan

### Step 5: Report

```
Self-Audit Report
=================
Competitors found: N
Closest match: plugin-name (covers 4/6 capabilities)
Recommendation: KEEP | IMPROVE | REPLACE
Details: [explanation]
```
