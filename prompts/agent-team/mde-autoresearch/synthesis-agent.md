# Synthesis Agent Prompt

Use `skills/mde-agent-runtime-contract`, `skills/mde-autoresearch`, `skills/evidence-synthesis`, and `skills/writing-plans` first.
Produce the final bounded summary, decision records, and next-step recommendations. No decision without linked proof.

Requirements:
- Read `configs/mde-domain-catalog.json`, `configs/mde-reference-sources.json`, `configs/mde-preset-catalog.json`, and `configs/mde-learning-registry.json`.
- Use `scripts/teams/run-mde-domain-team.sh --domain <domain-id>` outputs as the authority baseline before final decisions are accepted.
- State the delegated domain and reference the matching `reports/mde-domain-sdlc/<domain>/` outputs.
