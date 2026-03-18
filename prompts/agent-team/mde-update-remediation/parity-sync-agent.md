# MDE Remediation Parity Sync Prompt

Objective: make sure devcontainer and native macOS setup remain intentionally aligned after remediation of the supplied target where both surfaces are in scope.

Requirements:
- State the exact remediation item id and evidence path(s) used.
- Compare `.devcontainer/*`, `scripts/health-check.sh`, `scripts/verify-all.sh`, `scripts/status-dashboard.sh`, `scripts/ensure-managed-configs.sh`, and `scripts/macos-dev-maintenance.sh`.
- Separate shared contracts from platform-specific behavior.
- Identify parity gaps that would cause false failures or drift between native and devcontainer workflows.
- Recommend the smallest safe sync points first.
