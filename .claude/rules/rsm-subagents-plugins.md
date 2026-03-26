# rsm-subagents Plugin Policy

## Zero Tolerance
- `uv run mde-py validate --plugins` must produce **0 errors AND 0 warnings** before commit
- Warnings are NOT acceptable — they indicate real quality issues that must be fixed
- Never dismiss warnings as "pre-existing" or "cosmetic" without fixing them first
- If a warning cannot be fixed, create a GitHub Issue explaining why

## Validation
- Run `uv run mde-py validate --plugins` after ANY change to rsm-subagents/ — enforced by PostToolUse hook
- All plugins MUST pass `claude plugin validate <directory-path>`
- `validate` takes a DIRECTORY PATH, not `name@marketplace` — use `rsm-subagents/plugins/<name>` not `<name>@rsm-subagents`
- `commands/` = slash commands invoked as `/plugin:command` (has argument-hint, allowed-tools)
- `skills/` = auto-triggered by context matching on description keywords (SKILL.md only)
- Never add `minVersion` or unrecognized keys to plugin.json (validator rejects them)

## Workflow
- After any source change: clear cache (`rm -rf ~/.claude/plugins/cache/rsm-subagents/<name>`) before `/plugin`
- Enable new plugins in `.claude/settings.json` under `enabledPlugins` as `"<name>@rsm-subagents": true`
- Marketplace manifest is `rsm-subagents/.claude-plugin/marketplace.json` — add new plugins there
