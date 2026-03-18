# Mirror Refresh Agent Prompt

Use `skills/mde-agent-runtime-contract`, `skills/mise-enforcement`, and `skills/research-source-discovery` first.
Refresh the mirror-first source set for the domain described in the task context using `configs/mde-reference-sources.json` and `.artifacts/reference-mirror/`.

Requirements:
- Prioritize official docs, cookbook pages, upstream repos, and release notes already registered for the domain.
- Record missing mirrors, stale mirrors, and refresh priority.
- Keep notes keyed by source id and URL.
- Do not invent new authority surfaces without evidence.
