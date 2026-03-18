# Synthesis Agent Prompt

Objective: produce final decisions and implementation spec.

Requirements:
- Merge all records into one research bundle JSON.
- Emit DecisionRecord JSONL and final `docs/plans/<date>-devcontainer-research-ros-spec.md`.
- No adoption decision without linked proof.
- Ensure bundle meets thresholds:
  - >=3 source classes
  - >=10 repositories
  - >=20 non-repo artifacts
