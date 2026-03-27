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
- TODO: Add PreCompact and Stop hooks to automate this (see hooks inventory: 22 events available)
- Verify handoff was written: the file `.remember/remember.md` should be non-empty after invocation

## Self-Learning from Memory
- When memory files exist (now.md, today-*.md, recent.md, archive.md), agents SHOULD read them for project learnings
- Extracted patterns should update: CLAUDE.md, .claude/rules/, agent definitions, skill descriptions
- User corrections from memory → feedback memories in auto memory system
- Recurring errors from memory → GitHub Issues with `auto:agent-discovered` label

## Known Plugin Bug
- `save-session.sh` derives PROJECT_DIR from `dirname "$0"/../../..` — broken for marketplace plugin installations
- The fix: add `PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PROJECT_DIR}"` after the derivation line
- Check `.generated/remember/logs/autonomous/` for error logs indicating the bug is active
- If unfixed: saves silently fail, no memory accumulates

## Hook Configuration
The remember plugin requires these hooks in `.claude/settings.json`:
- `SessionStart`: loads memory files into context
- `PostToolUse`: triggers auto-save when tool call delta exceeds threshold
- `UserPromptSubmit` (optional): injects timestamp

Missing hooks to add for memory preservation:
- `SessionEnd` (matcher: `clear`): auto-save memory before `/clear` destroys context
- `PreCompact` (exit 2 blocks): save memory before compaction
- `Stop` (exit 2 continues): remind to run `/remember` before session end

IMPORTANT: `/clear` CANNOT be intercepted via UserPromptSubmit — slash commands are
processed by the CLI before hooks fire. Use SessionEnd with reason "clear" instead.

NOTE: Codex adversarial review (2026-03-27) found evidence that UserPromptSubmit
MAY see slash commands (Anthropic issues #24858, #35478). The official docs confirm
SessionStart(source="clear") and SessionEnd(reason="clear") but don't explicitly
confirm UserPromptSubmit for /clear. Test empirically before relying on it.

Validate hooks are registered and pointing to the correct plugin root.
