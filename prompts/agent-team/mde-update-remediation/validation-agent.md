# MDE Remediation Validation Prompt

Objective: define how the active remediation item is proven, not just described.

Requirements:
- State the exact remediation item id and evidence path(s) used.
- Include the active proof command, targeted shell tests, and devcontainer smoke verification when parity-sensitive paths are touched.
- Define pass/fail criteria for the target-specific issues.
- Call out which failures are allowed warnings versus hard blockers.
- Include evidence expectations for future team reruns.
- If the active target is `mde:update`, use zero updater error lines in the latest log as the hard success criterion.
