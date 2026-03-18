# Guidance Consolidator Agent Prompt

Use `skills/mde-agent-runtime-contract`, `skills/mde-autoresearch`, and `skills/mise-enforcement` first.
Convert accepted findings into concise AGENTS, skills, and guidance updates that reduce future prompt-time correction.

Requirements:
- Read `configs/mde-domain-catalog.json` and `configs/mde-learning-registry.json` before changing guidance.
- Do not consolidate guidance that bypasses the owning domain team.
- Link accepted guidance updates back to the delegated domain outputs and learning-registry records.
