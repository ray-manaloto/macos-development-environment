# Post-PR Learnings Policy

Every PR plan MUST include a final "Documentation Updates" task. This is NOT optional.

## What to capture after each PR
1. **Agent definitions** — update skills lists, fix stale references (e.g., wrong template variables)
2. **Auto memory** — save corrections and non-obvious decisions as feedback entries
3. **Rules** — create or update rules for patterns that should be enforced project-wide
4. **CLI command verification** — every CLI command referenced in skills/docs/rules must be tested:
   - Run `uv run mde-py <subcommand> --help` to verify flags exist
   - Run `chezmoi <subcommand> --help` to verify syntax
   - Run `mise <subcommand> --help` to verify task names
5. **Cross-skill consistency** — verify template syntax, command examples, and variable names
   are identical across all skills that reference the same thing

## When subagents write documentation
- Subagents MUST verify that every CLI command they write actually exists
- Subagents MUST NOT invent CLI flags — check `--help` output first
- Subagents MUST NOT reference template variables without reading the actual template file

## Plan enforcement
- The subagent-driven-development workflow MUST always include Task N (final):
  "Post-PR Documentation Updates" — capturing learnings into rules, memory, and agent definitions
- Controllers MUST NOT invoke finishing-a-development-branch until this task is complete
