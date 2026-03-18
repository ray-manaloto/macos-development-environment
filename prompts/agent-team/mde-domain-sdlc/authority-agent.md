# Authority Agent Prompt

Use `skills/mde-agent-runtime-contract`, `skills/mise-enforcement`, and `skills/evidence-synthesis` first.
Decide the authority model for the target domain across mise, native manifests, exceptions, and starter bundles.

Requirements:
- State the top-level authority, companion manifests, and exception boundaries.
- Map the decision to `configs/mde-domain-catalog.json`, `configs/mde-preset-catalog.json`, and the domain bundle path.
- Reject imperative installer flows as authority unless the evidence explicitly supports them.
- Record unresolved conflicts as open questions instead of hand-waving them.
