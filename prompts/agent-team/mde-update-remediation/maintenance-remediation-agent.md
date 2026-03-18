# MDE Maintenance Remediation Prompt

Objective: analyze the owning maintenance, installer, task, and registry surfaces for fixes that are directly supported by the supplied remediation target and evidence.

Requirements:
- State the exact remediation item id and evidence path(s) used.
- Use `configs/mde-modernization-matrix.json` and `configs/mde-tool-ownership.json` as the primary contract inputs.
- Focus on `scripts/macos-dev-maintenance.sh`, `scripts/install-agent-stack.sh`, and `scripts/install-langchain-cli-tools.sh` first.
- Treat direct installers separately from declarative reconcilers; call out whether the owning surface should become a validator, reconciler, migration helper, or explicit exception handler.
- Prefer deterministic fixes over retry-only patches.
- Call out where a change should be macOS-only versus shared with devcontainer.
- Explicitly identify residual risks that still need rerun proof.
