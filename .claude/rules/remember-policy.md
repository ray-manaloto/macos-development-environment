# Remember Plugin Policy

## Data Directory
- All remember plugin data MUST live under `.generated/remember/`
- `.remember` MUST be a symlink to `.generated/remember/` — NEVER a directory
- If `.remember` exists as a directory, run `uv run mde-py migrate consolidate-generated` to fix
- `.generated/` MUST be in `.gitignore` — never commit transient data

## Pre-Compaction / Pre-Clear Requirement
- ALWAYS invoke `/remember` before any compaction, `/clear`, or session end
- This writes the handoff note so the next session has context
- NOTE: There is no automatic hook that triggers `/remember` yet — this is a manual discipline
- Verify handoff was written: the file `.remember/remember.md` should be non-empty after invocation

## remember.md Lifecycle (important)
- `remember.md` is a ONE-SHOT briefing: SessionStart reads it, then CLEARS it (`:>`)
- After session start, `remember.md` is always empty until `/remember` is invoked again
- If a session ends without `/remember`, the next session has no handoff in `remember.md`
- HOWEVER: `now.md` and `today-*.md` are ALWAYS loaded at session start as fallback context
- When instructing the next session, say "Read the handoff" (not "at .remember/remember.md")
  because the plugin loads all memory files automatically — the handoff may be in now.md

## Self-Learning from Memory
- When memory files exist (now.md, today-*.md, recent.md, archive.md), agents SHOULD read them for project learnings
- Extracted patterns should update: CLAUDE.md, .claude/rules/, agent definitions, skill descriptions
- User corrections from memory → feedback memories in auto memory system
- Recurring errors from memory → GitHub Issues with `auto:agent-discovered` label

## Local Patch: Marketplace Path Resolution (applied 2026-03-28)
A local patch is applied to `save-session.sh` and `run-consolidation.sh` in both
plugin cache copies (`0.1.0/` and `779ab61d8d41/`). The patch separates PLUGIN_ROOT
(pipeline code) from PROJECT_DIR (user data) so marketplace installs resolve correctly.

- Upstream issue: https://github.com/Digital-Process-Tools/claude-remember/issues/5
- Upstream fix commit: https://github.com/Digital-Process-Tools/claude-remember/commit/225c361
- Marketplace still pins pre-fix SHA `779ab61d` — `claude plugin update` won't help
- Patched files: `~/.claude/plugins/cache/claude-plugins-official/remember/*/scripts/{save-session,run-consolidation}.sh`
- Each patch has inline comments with links — search for "LOCAL PATCH" in the files
- If plugin cache is cleared/reinstalled, the patch must be re-applied
- **Removal condition:** when `claude plugin update` pulls commit `225c361` or later
- Check `.generated/remember/logs/autonomous/` for error logs — if the path bug recurs,
  logs will contain `No such file or directory` for `.claude/remember`

## Hook Configuration
The remember plugin requires these hooks in `.claude/settings.json`:
- `SessionStart`: loads memory files into context
- `PostToolUse`: triggers auto-save when tool call delta exceeds threshold
- `UserPromptSubmit` (optional): injects timestamp

Implemented memory preservation hooks (in settings.json):
- `SessionEnd` (matcher: `clear`): `save-memory-on-clear` saves context before `/clear`
- `PreCompact`: `remember-precompact` saves checkpoint before compaction
- `Stop`: `remember-stop` writes to `now.md` + `dream-extract` runs pattern extraction
- NOTE: These hooks write to `now.md`, NOT `remember.md` — `/remember` is still manual

IMPORTANT: `/clear` CANNOT be intercepted via UserPromptSubmit — slash commands are
processed by the CLI before hooks fire. Use SessionEnd with reason "clear" instead.

NOTE: Codex adversarial review (2026-03-27) found evidence that UserPromptSubmit
MAY see slash commands (Anthropic issues #24858, #35478). The official docs confirm
SessionStart(source="clear") and SessionEnd(reason="clear") but don't explicitly
confirm UserPromptSubmit for /clear. Test empirically before relying on it.

Validate hooks are registered and pointing to the correct plugin root.
