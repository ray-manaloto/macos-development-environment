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

## Marketplace: rsm-remember (updated 2026-03-30)
The remember plugin is installed from `rsm-remember` local marketplace (not `claude-plugins-official`)
to get the upstream path resolution fix. This pulls the latest commit from the upstream repo.

- Upstream fix: https://github.com/Digital-Process-Tools/claude-remember/commit/225c361
- Installed version: v0.2.0 at commit `618fc72` (includes the fix)
- Marketplace config: `rsm-remember/.claude-plugin/marketplace.json`
- To update: `claude plugin update remember@rsm-remember --scope project`
- The old `remember@claude-plugins-official` and its local patches are removed
- Config at `.claude/remember/config.json` sets `data_dir` to `.generated/remember`

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
