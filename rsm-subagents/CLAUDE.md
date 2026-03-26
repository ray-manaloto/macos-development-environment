# rsm-subagents Plugin Marketplace

Local plugin marketplace for Claude Code. See `.claude/rules/rsm-subagents-plugins.md` for full policy.

## Creating Plugins

Use `/plugin-dev:create-plugin` to scaffold new plugins. Add the plugin to the marketplace manifest at `.claude-plugin/marketplace.json`.

## Plugin Structure

```
plugins/<name>/
  agents/       # Agent definitions (.md files)
  commands/     # Slash commands — /plugin:command (has argument-hint, allowed-tools)
  skills/       # Auto-triggered by context matching (SKILL.md only, no argument-hint)
  hooks/        # hooks.json with pre/post tool hooks
  README.md
  LICENSE
```

## Validation (zero tolerance)

```bash
uv run mde-py validate --plugins   # Must produce 0 errors AND 0 warnings
claude plugin validate rsm-subagents/plugins/<name>  # Per-plugin check
```

Validate after EVERY change. Warnings are real issues -- fix them or file a GitHub Issue.

## Testing Workflow

After any source change, clear the cache before testing:

```bash
rm -rf ~/.claude/plugins/cache/rsm-subagents/<name>
```

Then re-invoke the plugin command/skill to load fresh.

## Enabling Plugins

Add to `.claude/settings.json` under `enabledPlugins`:

```json
"<name>@rsm-subagents": true
```

## Key Rules

- `validate` takes a DIRECTORY PATH, not `name@marketplace`
- Never add `minVersion` or unrecognized keys to plugin.json
- `commands/` have `argument-hint` and `allowed-tools`; `skills/` use SKILL.md only
