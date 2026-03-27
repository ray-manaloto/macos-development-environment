---
name: MISE_STRICT research findings
description: Clarification that "strict mode" in project refers to MDE_AUTOFIX_STRICT environment variable, not official mise feature
type: reference
---

# MISE_STRICT Research Findings

## Key Discovery
No official `MISE_STRICT` environment variable exists in the official mise repository or documentation.

## Project-Specific Finding
The project uses **`MDE_AUTOFIX_STRICT`** (not MISE_STRICT):
- Defined in: `scripts/macos-dev-maintenance.sh` (line 8)
- Defaults to: `0` (disabled)
- Requires: Both `MDE_AUTOFIX=1` AND `MDE_AUTOFIX_STRICT=1` to activate
- Purpose: Remove brew-managed runtimes (node, go, rust, python) in favor of mise-managed versions
- Status: **DESTRUCTIVE** — uses `brew uninstall`

## Official Mise Environment Variables Found
- **MISE_PIN=1** — Pin exact versions instead of fuzzy versions
- **MISE_YES=1** — Auto-answer "yes" to prompts (equivalent to config `yes = true`)
- **MISE_TRUSTED_CONFIG_PATHS** — Colon-separated paths for trusted configs
- **MISE_BACKENDS_<TOOL>** — Override backend for specific tools
- **MISE_ENV_CACHE=1** — Enable caching for secret resolution (fnox integration)

## Settings (Not Environment Variables)
- **status.missing_tools** — Controls warning behavior for missing tools (value: "if_other_versions_installed")

## Documentation Updated
1. Created: `docs/research/trail/findings/finding-mise-strict.yaml`
2. Updated: `docs/research/source-catalog.md` — Added "Mise Environment Variables & Settings" section with 6 source entries

## Recommendation
README.md reference (line 81) to "strict mode" should be clarified as "MDE_AUTOFIX_STRICT environment variable" to avoid confusion with potential future official mise strict mode features.
