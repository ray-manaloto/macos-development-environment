---
name: gitagent Tool Investigation Finding
description: gitagent exists (v0.1.7, production-ready) but not installed in project; spec's validation strategy has workflow gaps
type: project
---

## Finding Summary

**Status**: Tool EXISTS but NOT INSTALLED. Spec has validation strategy gaps.

**Tool Details**:
- GitHub: `open-gitagent/gitagent` (confirmed active, last commit Mar 20 2026)
- npm: `@open-gitagent/gitagent` v0.1.7 (published Feb 24 2026)
- Type: Framework-agnostic, git-native AI agent format with import/export bridge
- Current state: `which gitagent` returns nothing; not in `.mise.toml`

## Why Investigation Started

Spec (2026-03-20-native-claude-code-migration-design.md) Section 12.3-12.6 and checklist items 13a, 13b, 41 recommend using gitagent for agent validation. Deep review reported "No tool called gitagent was found in any search." Investigation confirmed: tool exists but wasn't in project's declared tools.

## Critical Gap: Validation Strategy Mismatch

**Spec says (Section 12.3-12.4)**:
```bash
gitagent import --from claude .claude/agents/
gitagent validate
gitagent export --format claude-code
```

**Reality**:
- gitagent expects `CLAUDE.md` file in import source (not present)
- gitagent validates gitagent format (`agent.yaml` + `SOUL.md`), not Claude Code format (`.md` with YAML frontmatter)
- Project agents are all Claude Code format, not gitagent format
- **Result**: `gitagent validate` fails on `.claude/agents/*.md` files

**Why This Matters**: 
Spec relies on gitagent for validation (checklist 13b, 41), but gitagent is a **portability/export bridge**, not a validator for Claude Code agents. The spec instead creates custom `validate_agents.py` (Section 12.5) to fill this gap.

## Correct Use Cases for gitagent

**✓ DO use for**:
- Export Claude Code agents to CrewAI, AutoGen, LangChain, OpenAI formats
- Build cross-framework agent portability
- Compliance validation (FINRA/SEC) for multi-framework deployments

**✗ DON'T use for**:
- Validating `.claude/agents/*.md` files in place (custom validator needed)
- Format conversion without understanding multi-file structure requirement

## Required Actions

1. **Install** (1-line change): Add `@open-gitagent/gitagent` to `.mise.toml` (npm backend)
2. **Clarify spec** (Section 12.3-12.4): Mark gitagent for export/portability, not validation
3. **Keep custom validator** (Section 12.5): `validate_agents.py` is the primary validator for Claude Code format

## Evidence

All findings verified:
- `gh repo view open-gitagent/gitagent` ✓
- `npx @open-gitagent/gitagent --version` ✓ (v0.1.0)
- Test: `gitagent import --from claude .claude/agents/` ✗ (CLAUDE.md not found)
- Test: `gitagent validate .claude/agents/` ✗ (expects agent.yaml + SOUL.md)
- Confirmed: 25 agent files in `.claude/agents/` are Claude Code format, not gitagent format
