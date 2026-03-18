# Implementation Agent Prompt

Use `skills/mde-agent-runtime-contract`, `skills/mise-enforcement`, and `skills/writing-plans` first.
Turn accepted domain decisions into starter-bundle and preset recommendations for the target domain.

Requirements:
- Keep the implementation surface within the domain bundle, preset, and catalog contracts.
- Specify the minimum starter files, validation commands, and realization notes the domain should own.
- Prefer declarative manifests and lockfiles over imperative setup steps.
- Flag follow-up work that belongs outside the scoped config and prompt surfaces.
