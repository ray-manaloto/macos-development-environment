# CLAUDE.md

@AGENTS.md

## Claude Code

### Subagents

Defined in `.claude/agents/`. Use matching specialist types. Core: researcher (Sonnet), coder, tester (pytest/ruff/ty), reviewer (Sonnet, read-only). Specialists: python-coder, mise-specialist, chezmoi-specialist, brew-specialist, security-auditor, claude-code-specialist, remember-specialist. Agents write discoveries to `.generated/learnings/` for dream pipeline consumption.

### Hooks

Auto-discovered in `src/mde/hooks/` via `__hook_meta__`. Never edit `cli.py` to add hooks. Policy files in `.claude/rules/` are loaded automatically. See `hooks-auto-discovery.md` for the convention. Key advisory hooks (all exit 0): `check-knowledge` (PostToolUse — detects stale hook/test/subcommand counts in auto-memory and agent defs), `guard-debate` (PreToolUse — warns when raw codex/gemini CLI used instead of `mde debate`), `check-observability` (SessionStart — verifies OTEL collector health), `dream-extract` (Stop — extracts patterns into dream pipeline), `remember-stop` (Stop — writes session context to `now.md`).

### Plugins

Local marketplace at `rsm-subagents/` (7 plugins: mise-toolkit, chezmoi-toolkit, hk-toolkit, marketplace-evaluator, research-review-toolkit, devcontainer-toolkit, workflow-toolkit). Plugin validation (`uv run mde-py validate --plugins`) must produce 0 errors AND 0 warnings.

### Remember

`.remember` symlinks to `.generated/remember/`. ALWAYS invoke `/remember` before compaction, `/clear`, or session end — memory loss is permanent.

### Plugin/Tool Evaluation

Before building any new tool/plugin/agent: search community plugins (`claude-community` marketplace), existing skills, and PyPI/npm first — build new is LAST RESORT. Every candidate MUST be evaluated — never skip without explicit user approval.
