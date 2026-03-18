## Agent Runtime Policy

- This repository defines the MacBook host setup contract for agent-run tooling work.
- Use `skills/mde-agent-runtime-contract` first for setup, installation, migration, automation, or research tasks in this repo.
- Use `skills/mde-package-cache-policy` for cache-aware setup, migration, automation, and verification work.
- Use `skills/mde-python-backend-selection` for Python CLI backend decisions.
- Use `skills/mde-node-cli-declaration` for Node global CLI declaration changes.
- Use `skills/mde-native-tool-validation` for lint, static analysis, and validation changes.
- Treat `configs/mde-domain-catalog.json` as the routing table for language and tool domains.
- Treat `configs/mde-reference-sources.json` as the mirror-first source manifest and refresh `.artifacts/reference-mirror/` before falling back to ad hoc web search.
- Treat `configs/mde-preset-catalog.json` and `configs/tool-bundles/` as the repo-scoped preset and starter-bundle surfaces.
- Treat `configs/mde-learning-registry.json` as the committed learning writeback surface for accepted findings.
- Use `mise` as the authority for global runtimes, global CLIs, and SDK CLIs.
- Keep repository libraries in native manifests instead of global installers.
- Prefer `mise run <task>` or `mise x <tool> -- <args>` over directly invoking unmanaged binaries.
- Treat Homebrew as exception-only through `configs/mde-install-exceptions.json`. Use `$mde-homebrew` for brew diagnostics, ownership conflicts, and update failures.
- reuse package manager caches by default and do not clear caches unless a bounded maintenance flow explicitly allows it.
- Classify setup and tooling work into a domain and delegate to the owning SDLC team before adopting or remediating guidance.
- Read `configs/mde-tool-ownership.json`, `configs/mde-modernization-matrix.json`, `configs/mde-install-exceptions.json`, `configs/mde-skill-registry.json`, `configs/mde-domain-catalog.json`, `configs/mde-reference-sources.json`, `configs/mde-preset-catalog.json`, and `configs/mde-learning-registry.json` before changing ownership or skill references.
- For methodical research/planning tasks, use the ROS skill chain in order:
  `skills/research-source-discovery`, `skills/github-repo-mining`, `skills/social-signal-mining`, `skills/evidence-synthesis`.
