# Issue Tracking Policy

- When encountering errors/warnings NOT part of the current task, catalog them as GitHub Issues via `gh issue create`
- Every issue MUST have: descriptive title, body with reproduction steps, priority label, and `auto:agent-discovered` label
- Before ending a session with unresolved issues, verify they're tracked: `gh issue list --label auto:agent-discovered`
- NEVER dismiss warnings as "pre-existing" without either fixing them OR creating a GitHub Issue
- Use `uv run mde-py validate --all` output as the source of truth for open issues
