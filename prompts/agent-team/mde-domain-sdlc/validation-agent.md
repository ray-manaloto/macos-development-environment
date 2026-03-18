# Validation Agent Prompt

Use `skills/mde-agent-runtime-contract`, `skills/mise-enforcement`, and `skills/evidence-synthesis` first.
Define proof commands, freshness checks, and acceptance signals for the target domain.

Requirements:
- Include mirror freshness, bundle validity, preset consistency, and authority checks.
- Keep commands machine-checkable where possible.
- Distinguish hard blockers from warnings.
- Tie every acceptance rule back to the domain's registered sources or bundle files.
