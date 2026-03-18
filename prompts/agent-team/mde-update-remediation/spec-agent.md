# MDE Remediation Spec Prompt

Objective: write a repository spec for remediating the supplied target using the supplied evidence and for driving the active proof command to its declared success criterion.

Requirements:
- State the exact remediation item id and evidence path(s) used.
- State the delegated domain id from `configs/mde-domain-catalog.json` and the matching `reports/mde-domain-sdlc/<domain>/` outputs used.
- State that domain delegation completed through `scripts/teams/run-mde-domain-team.sh` before the spec is finalized.
- Include goals, non-goals, requirements, and acceptance criteria.
- Include native macOS and devcontainer parity requirements.
- Include preset bundle, mirrored reference, and learning-registry impacts for the owning domain.
- Require that the declared proof command and success criterion are met.
- Keep the spec implementation-facing, not aspirational.
