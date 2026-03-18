# Test-Driven Development skill (obra/superpowers)

Installed via:

```bash
bun x add-skill https://github.com/obra/superpowers --skill test-driven-development --yes
```

Location (project-scoped): `.agents/skills/test-driven-development`

Enabled for agents (symlinks created by installer): Antigravity, Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, Kiro CLI, OpenCode, Windsurf.

Usage expectation: follow skill guidance to enforce TDD-driven workflows on tasks. Apply this skill for all future tasks in this project.

Validation:
- Skill present: `ls .agents/skills/test-driven-development`
- Optionally re-validate with SkillPort if needed: `skillport validate .agents/skills`
