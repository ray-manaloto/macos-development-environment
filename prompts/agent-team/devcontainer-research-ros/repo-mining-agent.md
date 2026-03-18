# Repo-Mining Agent Prompt

Objective: mine shortlisted repositories and extract implementation patterns.

Requirements:
- Use query grammar from `docs/research/query-pack-devcontainer-ros.md`.
- Extract path-level/workflow-level proof.
- Emit PatternRecord JSONL per `docs/research/schemas/pattern-record.schema.json`.
- Mine at least 10 repos and produce scored shortlist (top 15).
