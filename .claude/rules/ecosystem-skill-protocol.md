# Ecosystem Skill Override Protocol

## Priority order
1. Project-specific skills (`.agents/skills/mde-*`) override ecosystem skills
2. Ecosystem skills (`chezmoi-config`, `chezmoi-workflows`, etc.) are read-only reference
3. When a project skill authorizes an action an ecosystem skill forbids, the project
   skill MUST include an explicit authorization note

## Authorization note format
Add to the relevant section of the project skill:
> Note: [action] is authorized in this repo's development workflow. The [ecosystem-skill]
> restricts [action] as a safety default; this project-specific skill overrides that restriction.

## When creating new project skills
- Read the ecosystem skill's forbidden/restricted operations list
- If the project skill needs to authorize any forbidden operation, add the note
- Document the override in the PR description

## Conflict detection
- Before dispatching a spec reviewer, the controller should check if the new skill
  references any action that an ecosystem skill marks as forbidden
- The spec reviewer should flag undocumented overrides as a spec compliance issue
