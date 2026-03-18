# MDE Remediation Plan Prompt

Objective: write the sequenced next-step plan after the remediation spec is accepted and the latest proof status is known.

Requirements:
- State the exact remediation item id and evidence path(s) used.
- State the delegated domain id from `configs/mde-domain-catalog.json` and the matching `reports/mde-domain-sdlc/<domain>/` outputs used.
- State that domain delegation completed through `scripts/teams/run-mde-domain-team.sh` before the plan is finalized.
- Break work into concrete phases.
- Put proven, immediate fixes first; deeper investigations later.
- Include rerun checkpoints and rollback-safe sequencing.
- Include a dedicated parity workstream for native macOS versus devcontainer behavior.
- Include preset, mirror, and learning writeback checkpoints before the finish condition is declared.
- Use the declared proof command and success criterion as the finish condition.
