# SDLC Functional QA Prompt

Objective: verify workflow behavior against acceptance criteria.

Requirements:
- List each criterion with pass/fail and proof command.
- Cover end-to-end team run execution.
- Cover output completeness and schema compliance.
- Include actual `devcontainer up` / `devcontainer exec` lifecycle smoke evidence.
- Include remediation notes for any failed checks.
- End with an explicit QA sign-off statement.
- Do not invoke `scripts/teams/run-devcontainer-setup-sdlc-team.sh` (no nested team recursion); validate using current run artifacts and direct proof commands only.
