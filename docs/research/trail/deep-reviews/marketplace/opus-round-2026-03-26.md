# Opus Deep Review Round — 20 Finalists

**Date**: 2026-03-26
**Model**: claude-opus-4.6
**Method**: 4 parallel agents, 5 plugins each, full source code review

## Summary

| Plugin | Verdict | Confidence | Goals | Key Finding |
|--------|---------|------------|-------|-------------|
| evolve-loop | EXTRACT | 0.85 | agent-improvement, self-updating | 8 .sh files; extract anti-cheating patterns, eval quality classifier |
| superpowers-optimized | EXTRACT | 0.90 | agent-improvement, memory | 1 .sh hook; extract secret protection (56+13 patterns), self-consistency reasoner |
| engram | REJECT | 0.95 | memory-research | MCP server, proprietary license, existing stack covers all use cases |
| hipocampus | EXTRACT | 0.75 | memory-research | 1 .sh hook; extract 5-level compaction tree, ROOT.md index pattern |
| claude-workflow | REJECT | 0.85 | agent-improvement | MCP server, 2 .sh hooks, invasive global skill installation |
| cortex | REJECT | 0.90 | sdlc-orchestration | 6 .sh, bash hooks, auto-commit, wrong stack (NestJS/Spring Boot) |
| devteam | REJECT | 0.85 | sdlc-orchestration | Japanese docs, tmux-based (not Agent Teams), file-queue incompatible |
| groundwork | EXTRACT | 0.80 | sdlc-orchestration | 4 bash hooks; extract checkpoint-compact, validation-loop, error recovery |
| contextstellar | EXTRACT | 0.75 | context-token, prompt-opt | 3 bash hooks; extract local scorer algorithm (5-dimension prompt scoring) |
| auto-memory | EXTRACT | 0.82 | self-updating, memory | Python hooks (compliant!); extract dirty-file tracking, git context enrichment |
| claude-skills-updater | INSTALL | 0.82 | self-updating, plugin-finding | Zero violations, fills plugin update gap, minimal context cost |
| harnesskit | REJECT | 0.92 | plugin-finding | 6 bash hooks, overwrites CLAUDE.md, writes settings.json |
| plugin-manager | REJECT | 0.85 | plugin-finding | Node.js HTTP server for editing settings.json — CLI-first project |
| cync | REJECT | 0.90 | dotfiles-tooling | 4 .sh, duplicates chezmoi functionality, parallel sync mechanism |
| backpack-ontology | EXTRACT | 0.72 | memory-research | MCP server; extract progressive discovery pattern, graph schema conventions |
| prompt-improver | REJECT | 0.85 | prompt-optimization | Per-prompt overhead (~150 tokens every interaction), overlap with challenger |
| pwp | EXTRACT | 0.80 | code-modernization | 11 skills but 6+ overlap; extract migrate and perf protocols |
| open-crab | REJECT | 0.95 | self-updating | Requires local LLM (Ollama), Chinese commands, MCP server |
| bake-claude-md-files | EXTRACT | 0.75 | replace-handcoded | Good methodology, better as one-time task than permanent plugin |
| mine | INSTALL | 0.82 | telemetry | Pure Python hooks, session analytics, error pattern recall, fills real gap |

## INSTALL Candidates (for codex follow-up)

### claude-skills-updater
- **Source**: https://github.com/dcuenot/claude-skills-updater
- **Components**: 1 skill, no hooks, no scripts
- **Why**: Scans marketplaces, compares versions via gh CLI, interactive update with user confirmation. Fills gap — no mechanism to keep plugins current.

### mine
- **Source**: https://github.com/anipotts/claude-code-tips (plugins/mine/ subdirectory only)
- **Components**: 1 skill, 5 Python hooks (SessionEnd, SubagentStop, PreCompact, SessionStart, PostToolUseFailure)
- **Why**: Session cost analytics, token tracking, cross-session search, error pattern recall. Pure Python hooks. PostToolUseFailure surfaces past similar failures.

## Codex GPT-5.4 Follow-Up Review

### claude-skills-updater — Codex: DISAGREE

> "The upstream README and SKILL.md show it depends on authenticated gh and direct git/mkdir
> shell commands against ~/.claude/..., which is not a clean fit for mde's mise-first, Python-only,
> minimal-footprint contract. It is also a very new, thin plugin with an initial v1.0.0 release
> published March 13, 2026 and effectively a single public commit, so I would not treat INSTALL
> at 0.82 confidence as justified without forking/adapting it first."

**Resolution**: Downgrade to EXTRACT. Codex correctly identifies maturity concerns and shell
command reliance. The plugin update scanning methodology is worth extracting but not installing as-is.

### mine — Codex: DISAGREE

> "The hook layer is pure Python, but the shipped mine skill is large and Bash-centric, with
> shell-based query/install flows including brew install guidance, which is a poor fit for mde's
> no-shell-scripts, mise-first, and context-budget policies. More importantly, two marquee features
> look structurally unreliable: PreCompact and PostToolUseFailure both read session state that is
> only populated on SessionEnd, so live burn-rate warnings and error recall may not work mid-session."

**Resolution**: Downgrade to EXTRACT. Codex found a genuine reliability issue (hooks reading
data that isn't populated until session end). The SQLite schema, Python hook patterns, and
session analytics concept are worth extracting, but the plugin needs fixes before installing.

## Multi-Model Consensus

| Plugin | Opus | Codex | Final |
|--------|------|-------|-------|
| claude-skills-updater | INSTALL | DISAGREE | **EXTRACT** (maturity, shell reliance) |
| mine | INSTALL | DISAGREE | **EXTRACT** (reliability bug, bash-centric skill) |

**Result: 0 INSTALL verdicts survived multi-model review. All 20 finalists are EXTRACT or REJECT.**

## Top Extraction Priorities

1. **superpowers-optimized** secret protection patterns (56 file + 13 hardcoded patterns)
2. **evolve-loop** eval quality classifier + anti-cheating (challenge tokens, hash chains)
3. **superpowers-optimized** self-consistency reasoner (5-path majority vote)
4. **auto-memory** Python hook patterns (cleanest hook implementation seen)
5. **groundwork** checkpoint-and-compact state persistence
6. **contextstellar** local prompt scorer algorithm (5-dimension scoring)
7. **hipocampus** compaction tree design (Raw→Daily→Weekly→Monthly→Root)
8. **mine** SQLite session analytics schema + Python hooks (fix reliability first)
9. **claude-skills-updater** plugin update scanning methodology (rewrite in Python)
