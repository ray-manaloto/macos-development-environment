# Devcontainer Validation Prompt

Objective: define the validation contract that proves the published devcontainer image is usable and the release gate is real.

Requirements:
- Cover tool presence checks, post-create execution, `mise trust`, managed-config drift check, and `mise run mde:verify`.
- Require strict JSON validation for `scripts/status-dashboard.sh --json`.
- Include local and CI command sequences.
- Report any residual risk or unvalidated surface area explicitly.
