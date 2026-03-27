# Agent Teams Lifecycle Policy

## Spawning
- Always `TeamCreate` before spawning agents with `team_name`
- Run agents in background (`run_in_background: true`) so the lead can coordinate
- Set `mode: bypassPermissions` for implementers working in worktrees

### Agent Type Requirements (MANDATORY)
Team members MUST use agent types that have `SendMessage` and `TaskUpdate` tools.
Without these, agents become zombies that cannot:
- Send findings back to the team lead
- Process shutdown_request messages (requires SendMessage to reply)
- Mark tasks as completed

**Safe for teams:** `general-purpose`, `agent-teams:team-reviewer`, `agent-teams:team-debugger`,
`agent-teams:team-implementer`, `agent-teams:team-lead`

**NEVER use as team members:** `claude-code-guide`, `Explore`, `Plan`, or any read-only agent type.
These lack SendMessage/TaskUpdate and will become unrecoverable zombies.

If you need specialist knowledge (e.g., Claude Code docs), spawn a `general-purpose` agent
and include the specialist knowledge in the prompt instead.

## Shutdown Protocol (MANDATORY)
Plain text "shut down" messages do NOT terminate agents. You MUST use the structured protocol:

```json
SendMessage({
  "to": "agent-name",
  "message": {"type": "shutdown_request", "reason": "Tasks complete."},
  "summary": "Shutdown agent-name"
})
```

- Send shutdown_request IMMEDIATELY when agent's tasks are done — do not send plain text first
- If agent doesn't terminate within 30s of approval, it's stuck — proceed with TeamDelete
- Always TeamDelete after all agents are terminated to clean up team resources

## Task Coordination
- Use TaskCreate/TaskUpdate with dependencies (addBlockedBy) for cross-agent sequencing
- Team task lists are scoped to the team — they're separate from the session task list
- When unblocking an agent, send them a direct message (not just TaskUpdate)

## Common Pitfalls
- Sending "please shut down" as plain text → agent acknowledges but stays alive in idle loop
- Forgetting TeamDelete → stale team config blocks creating new teams with same name
- Not using run_in_background → lead blocks waiting for first agent, can't spawn others in parallel
- Using `claude-code-guide` or `Explore` as team members → zombie agents that can't shutdown or report
- Not verifying agent type has SendMessage before spawning → requires manual `rm -rf ~/.claude/teams/` cleanup
