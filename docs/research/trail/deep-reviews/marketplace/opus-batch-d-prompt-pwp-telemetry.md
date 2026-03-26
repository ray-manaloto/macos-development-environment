# Opus Deep Review: opus-batch-d-prompt-pwp-telemetry

**Date**: 2026-03-26
**Model**: claude-opus-4.6
**Agent ID**: a8a305b4

---

I now have a thorough understanding of all 5 plugins. Here is my deep review:

---

## Plugin Deep Review Results

### 1. prompt-improver
**VERDICT: REJECT**
**CONFIDENCE: 0.85**
**GOALS: prompt-optimization**
**COMPONENTS: skills=1, agents=0, cmds=0, hooks=UserPromptSubmit (Python, wraps every user prompt)**
**POLICY_VIOLATIONS: none (Python hook, no .sh, no API keys)**
**OVERLAP: partial with challenger plugin (both intercept/improve user prompts)**
**RATIONALE:** The hook wraps EVERY user prompt in a "PROMPT EVALUATION" wrapper that injects ~150 tokens of meta-instructions into every single interaction, telling Claude to decide if the prompt is "vague enough" to invoke the skill. This is invasive -- it adds latency and context overhead to every prompt, including ones that are perfectly clear. The skill itself (research-based clarifying questions via AskUserQuestion) is useful in principle but the trigger mechanism is a blunt instrument. The bypass mechanism (* prefix) is non-standard and would confuse users. The skill references TodoWrite and WebFetch which are deprecated/disallowed in this project. Overlaps with the challenger plugin's role of questioning assumptions. Net value is negative due to per-prompt overhead.
**EXTRACTABLE:** The question-patterns.md and research-strategies.md reference files contain solid prompt engineering guidance that could be adapted as reference material for the existing challenger or guide plugins.

### 2. pwp (Project Workflow Protocol)
**VERDICT: EXTRACT**
**CONFIDENCE: 0.80**
**GOALS: code-modernization, replace-handcoded**
**COMPONENTS: skills=11, agents=0, cmds=0, hooks=none**
**POLICY_VIOLATIONS: none (pure markdown skills, no scripts, no hooks, no API keys)**
**OVERLAP: HIGH -- pwp-code-review overlaps with codebase-quality + engineering; pwp-security-audit overlaps with safety-net; pwp-test overlaps with test-generator; pwp-debug overlaps with bugbash; pwp-docs overlaps with guide**
**RATIONALE:** Pure skills-only plugin with zero hooks, zero scripts -- cleanest architecture of the five. However, installing all 11 skills would add massive context budget overhead (11 skill descriptions loaded every session) while 6+ overlap significantly with already-enabled plugins. The skills themselves are well-structured protocol documents with checklists, severity levels, and anti-patterns, but they are generic (not Python/mde-specific). The pwp-migrate and pwp-perf skills are the most unique -- they cover structured migration and performance optimization workflows not well-covered by existing plugins. The pwp-api-design and pwp-bootstrap skills are irrelevant to a CLI tool project.
**EXTRACTABLE:** pwp-migrate (structured migration protocol) and pwp-perf (performance optimization protocol) are the two skills worth extracting. Their checklist-based approach could be adapted into the existing engineering plugin or used as reference material for the mise-toolkit or python-quality-toolkit.

### 3. Open-Crab
**VERDICT: REJECT**
**CONFIDENCE: 0.95**
**GOALS: self-updating**
**COMPONENTS: skills=0, agents=0, cmds=4, hooks=none, MCP server (Node.js + local LLM)**
**POLICY_VIOLATIONS: HARD -- requires local LLM server (Ollama with qwen3:8b); MCP server ships an entire Node.js service; commands are in Chinese; relies on jq-style JSON parsing in JS; npx runtime dependency**
**OVERLAP: disk-clean overlaps with vitals; security overlaps with safety-net**
**RATIONALE:** This plugin requires a local LLM (Ollama) running at localhost:11434, which violates the subscription-only policy (no API keys, but requires running a separate LLM server). The MCP server adds 5 tools for file-summarize, content-qa, file-search, scan-analyze, and llm-status -- all of which duplicate capabilities Claude Code already has natively. The commands are written in Chinese, which is a localization mismatch. The "evolve" command (self-maintaining plugin) is an interesting concept but the implementation delegates to the local LLM for review, which is both unnecessary (Claude can review its own commands) and architecturally wrong for this project. No skills, no hooks -- just commands that run system scans.
**EXTRACTABLE:** Nothing. The self-evolution concept is interesting but the implementation is not portable.

### 4. bake-claude-md-files
**VERDICT: EXTRACT**
**CONFIDENCE: 0.75**
**GOALS: replace-handcoded, self-updating**
**COMPONENTS: skills=1, agents=0, cmds=0, hooks=none**
**POLICY_VIOLATIONS: none (pure markdown skill, user-invocable only, disable-model-invocation=true)**
**OVERLAP: partial with codebase-quality (both care about tooling enforcement); partial with engineering (both audit project configuration)**
**RATIONALE:** A single-skill plugin with a compelling idea: scan CLAUDE.md rules, identify which can be automated by existing linters/CI/hooks, implement the checks, then remove the prose from CLAUDE.md to free context budget. This directly serves the context-budget policy. The skill is well-designed -- user-invocable only (no auto-trigger), requires approval before changes, prioritizes existing tooling over custom scripts. However, it is generic (mentions ESLint, PHPStan, Pint) and would need adaptation for the Python/ruff/ty/hk.pkl toolchain. Installing as a full plugin wastes a plugin slot for a one-time or occasional use case. Better to extract the methodology and run it as a manual workflow.
**EXTRACTABLE:** The core methodology (inventory CLAUDE.md rules, classify as automatable vs judgment-required, implement checks in existing tooling, remove automated rules from CLAUDE.md) should be extracted as a one-time task or a command in the existing engineering plugin. The skill's implementation-priority section (discover existing tooling first, use native capabilities, custom scripts as last resort, wire into existing runners) aligns perfectly with project policies.

### 5. mine
**VERDICT: INSTALL**
**CONFIDENCE: 0.82**
**GOALS: telemetry**
**COMPONENTS: skills=1, agents=0 (the 5 agents + 8 cmds are in the outer repo, NOT in the mine plugin), hooks=5 Python hooks (SessionEnd, SubagentStop, PreCompact, SessionStart, PostToolUseFailure)**
**POLICY_VIOLATIONS: SOFT -- the outer claude-code-tips repo has 15 .sh files including hooks (safety-guard.sh, notify.sh, etc.), but the mine PLUGIN itself (plugins/mine/) uses ONLY Python hooks. The mine hooks use python3 not uv run, but this is acceptable since it runs outside the project venv. The SKILL.md contains inline bash heredocs for sqlite3 queries, which is the right tool for the job (not shell scripts as automation).**
**OVERLAP: partial with vitals (both track session metrics), partial with remember (both persist session state)**
**RATIONALE:** The mine plugin is the standout candidate. It solves a real gap -- no existing plugin provides session cost analytics, token usage tracking, cross-session search, or error pattern recall. The architecture is solid: a single unified Python hook dispatcher (hook.py, 469 lines, stdlib-only) handles all 5 hook events, a mine.py parser converts JSONL transcripts to normalized SQLite, and a comprehensive SKILL.md enables natural-language querying. The PostToolUseFailure handler that surfaces past similar failures is particularly valuable for the mde project's zero-tolerance policy. The PreCompact burn-rate warning helps with context-budget awareness. Important: install ONLY the mine sub-plugin (plugins/mine/), NOT the outer claude-code-tips repo which contains .sh hooks. The mine plugin itself is pure Python with no bash hooks. One concern: the SKILL.md is very large (~13K tokens) which impacts context budget, but it uses progressive disclosure well and the value of session analytics justifies the cost.
**EXTRACTABLE:** N/A -- full install recommended, but only the plugins/mine/ subdirectory.

---

## Summary Table

| Plugin | Verdict | Confidence | Key Factor |
|--------|---------|------------|------------|
| prompt-improver | REJECT | 0.85 | Per-prompt overhead, overlap with challenger |
| pwp | EXTRACT | 0.80 | 2 useful skills (migrate, perf) from 11; massive overlap otherwise |
| Open-Crab | REJECT | 0.95 | Requires local LLM, Chinese commands, MCP server overhead |
| bake-claude-md-files | EXTRACT | 0.75 | Good methodology, better as one-time task than permanent plugin |
| mine | INSTALL | 0.82 | Unique session analytics, pure Python, fills real gap |
