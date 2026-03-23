---
name: Context7 platform for live docs
description: MCP server + CLI tool that pulls current library docs into LLM context, resolves hallucinated APIs from training data cutoff
type: reference
---

## URL References

- **Main repo:** https://github.com/upstash/context7 (50k+ stars, MIT)
- **CLI SKILL.md:** https://github.com/upstash/context7/blob/master/skills/context7-cli/SKILL.md
- **Official site:** https://context7.com
- **Dashboard (API keys):** https://context7.com/dashboard
- **CLI docs:** https://context7.com/docs/clients/cli
- **MCP manual install:** https://context7.com/docs/resources/all-clients

## Quick Facts

- **Problem solved:** LLMs hallucinate APIs and use outdated docs from training data cutoff
- **Solution:** Fetches live, version-specific docs from source → injects into prompt
- **Modes:** CLI+Skills or pure MCP integration
- **Install:** `npx ctx7 setup` (interactive, OAuth auth)
- **Language:** TypeScript
- **License:** MIT
- **Auth:** OAuth, API key, or `CONTEXT7_API_KEY` env var
- **Rate limits:** Higher limits with free API key from context7.com/dashboard

## CLI Commands (SKILL.md Reference)

### Library Resolution
```bash
ctx7 library <name> <query>        # Finds library ID (e.g., /facebook/react)
```

### Documentation Fetching
```bash
ctx7 docs <libraryId> <query>      # Gets version-specific docs for library
```

### Skill Management
```bash
ctx7 skills install /owner/repo    # Install from GitHub repo
ctx7 skills search <keywords>      # Search registry
ctx7 skills suggest                # Auto-suggest based on project deps
ctx7 skills list                   # List installed skills
ctx7 skills remove <name>          # Uninstall
ctx7 skills generate               # AI-generated custom skill (requires login)
```

### Setup & Auth
```bash
ctx7 setup                         # Interactive MCP/skill setup
ctx7 login                         # OAuth
ctx7 login --no-browser            # Print URL instead of opening browser
ctx7 logout                        # Clear tokens
ctx7 whoami                        # Check login status
```

## MCP Tools (when using MCP mode)

- **resolve-library-id:** Takes library name + query, returns Context7 ID
- **query-docs:** Takes library ID + query, returns documentation

## Key Concepts

- **Library ID format:** `/owner/repo` or `/namespace/library` (slash prefix required)
- **Version targeting:** Mention version in prompt (e.g., "Next.js 14") → auto-matches
- **Rule-based triggering:** Can set rule in CLAUDE.md/Cursor Rules/etc. to auto-invoke for library questions

## For MDE Integration

- Add `ctx7` to mise config (prefer registry backend)
- Optional: `uv run mde-py` could expose ctx7 as a subcommand
- Consider both CLI (for scripting) and MCP (for Claude Code native integration)
- Use --api-key flag for CI/CD flows to skip OAuth browser prompt
