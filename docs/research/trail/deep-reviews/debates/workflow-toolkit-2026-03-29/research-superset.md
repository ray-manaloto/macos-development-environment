# Superset — Research Notes (2026-03-29)

Sources fetched:
- https://github.com/superset-sh/superset (README)
- https://github.com/superset-sh/superset/issues (open issues)
- https://github.com/superset-sh/superset/pulls (open PRs)
- https://github.com/superset-sh/superset/pull/2998 (codex loading-state fix)
- https://github.com/superset-sh/superset/pull/2994 (agent registry refactor)

---

## What Superset Is

Superset is a **macOS desktop application** (Electron + React + Bun) that acts as a multi-agent
orchestration shell. It is NOT a CLI orchestration library. Its primary value proposition is
running many CLI-based coding agents simultaneously across isolated git worktrees, from a single
GUI with a built-in terminal, diff viewer, and IDE handoff.

> "Orchestrate swarms of Claude Code, Codex, and more in parallel. Works with any CLI agent.
> Built for local worktree-based development."

This is **not** what the debate pipeline needs. The debate pipeline needs programmatic CLI
invocation and output capture. Superset wraps CLIs in PTY terminal sessions for interactive use.

---

## How Superset Coordinates Multiple CLI Tools

### Architecture: PTY Wrapper Per Agent

Each agent (claude, codex, gemini, etc.) runs inside a dedicated PTY (pseudoterminal) session
within Superset's terminal emulator. Coordination is per-worktree, not per-prompt: each "workspace"
maps to a git worktree + one running CLI agent session.

Superset does NOT:
- Batch-dispatch a prompt to multiple agents simultaneously and compare outputs
- Parse or diff model responses programmatically
- Have a "debate" or "multi-model review" mode

### Agent Registry (packages/shared/src/builtin-terminal-agents.ts)

As of PR #2994, agent metadata lives in a shared manifest:
```
builtin-terminal-agents.ts
  → labels, descriptions, commands, prompt-commands
  → capability-driven setup targets (not hardcoded per-agent sequences)
  → feeds: MCP description strings, default preset seeding, command building
```

Each agent has:
- `command`: the shell command to launch the agent (e.g., `claude`, `codex`, `gemini`)
- `promptCommand`: a keyboard shortcut or command to submit a prompt inside the PTY
- Icon, docs URL, label
- Optional config file managed by Superset (e.g., `.amp/settings.json` for Amp CLI)

### Prompt Delivery Mechanism

Prompts are delivered by **typing text into the PTY** — there is no `--prompt` flag injection or
stdin piping at the coordination layer. The workflow is:
1. User (or automation) types a prompt into the terminal pane
2. Agent CLI reads it interactively from the PTY

The exception is "workspace presets" which can auto-send a fixed initial prompt when a workspace
starts, via the `promptCommand` mechanism (simulated keystrokes into PTY).

### Output Capture: Hook-Based, Not stdout Pipe

Superset does NOT capture stdout/stderr from agents by redirecting file descriptors. Instead it:
1. Injects hooks into each agent's config file at agent setup time
2. Hooks fire lifecycle events (`SessionStart`, `UserPromptSubmit`, `Stop`) back to Superset
3. Superset uses these events to update "loading/working" state in the sidebar

For Codex specifically (PR #2998):
- Superset manages `~/.codex/hooks.json` via a "merge" operation
- It injects `UserPromptSubmit` and `Stop` hooks into that file
- Previously used session-log file watching as a secondary signal — fragile, now deprecated

For Claude Code:
- Same hook injection pattern into Claude's settings
- Hook events propagate agent lifecycle state changes to the Superset UI

**Key implication**: Superset's output capture is lifecycle-state only (is-the-agent-working?),
NOT content capture (what-did-the-agent-say?). There is no mechanism to read the LLM's response
text back into Superset.

---

## Configuration and Setup Patterns

### Per-Project Config (.superset/config.json)
```json
{
  "setup": ["./.superset/setup.sh"],
  "teardown": ["./.superset/teardown.sh"]
}
```
Setup/teardown scripts run on workspace create/delete. They have access to:
- `SUPERSET_WORKSPACE_NAME`
- `SUPERSET_ROOT_PATH`

### Agent Setup: Capability-Driven (PR #2994)
Previously Superset had hardcoded per-agent wrapper call sequences. Now uses capability targets:
- `desktop-agent-capabilities.ts` — declares what setup actions each agent requires
- `desktop-agent-setup.ts` — executes those capabilities
- Centralized "managed binaries" list
- Each new agent only needs a manifest entry, not spread across multiple files

### External API URL Pattern (PR #2991)
Superset is building a stable `localhost` URL pattern so local LLM providers (Ollama, LM Studio,
etc.) can be configured without Superset hardcoding per-provider URLs.

---

## Known Issues and Bugs Relevant to CLI Integration

### Issue #2983 / PR #2984: `spawn git ENOENT`
- When adding a project on Windows/non-standard setups, `git` is not on PATH
- Superset uses `spawn('git', ...)` directly; if git is not on PATH it throws ENOENT
- Fix: resolve git binary path before spawning
- **Implication for debate pipeline**: same class of bug — never assume tool is on PATH

### Issue #2968 / PR #2969: Terminal socket backpressure
- High-output PTY panes flood the terminal-host with "Client socket buffer full" warnings
- Fix: skip writes to backpressured sockets
- **Implication**: when running many agents in parallel, output buffering becomes a bottleneck

### Issue #2970 / PR #2971: Keyboard protocol interception
- `Shift+Enter` was being intercepted by Superset's terminal layer, not forwarded to the PTY
- Breaks Kitty keyboard protocol used by some terminal multiplexers
- **Implication**: PTY-level prompt delivery is fragile with special key sequences

### PR #2998: Codex loading-state regression
- Codex's internal session-log format changed; Superset's watcher broke silently
- Fix: use Codex's public hook surface (`UserPromptSubmit`, `Stop`) instead
- **Critical implication for debate pipeline**: Codex's internal APIs are unstable across versions.
  Always use the public CLI flags and hook contracts, never parse internal log files.

### PR #2979: Codex workspace search regressions
- Workspace search broke after a Codex update
- Shows Codex is an actively changing target; wrappers need version tolerance

---

## Shell Escaping and Prompt Injection

Superset does NOT inject prompts via shell command-line arguments (no `claude -p "..."` style
invocation). Prompts go through PTY keystroke simulation. This means:
- No shell escaping problem at the CLI invocation level
- BUT prompt content fed into the PTY must not contain characters that have special meaning
  in the terminal (e.g., Ctrl sequences, escape codes)

The debate pipeline's approach of `codex -p "..."` or `claude -p "..."` flags is fundamentally
different from Superset's architecture. Shell escaping is our problem, not Superset's.

---

## What Superset Is NOT (Relevance Assessment)

| Feature needed for debate pipeline | Does Superset provide it? |
|---|---|
| Programmatic multi-model dispatch | No — GUI-only, PTY-based |
| Stdout/stderr capture of model responses | No — hook-based lifecycle only |
| CLI flag-based prompt injection | No — PTY keystroke simulation |
| Parallel response comparison | No |
| Retry on model failure | No explicit retry; PTY session can be restarted |
| Model failure detection | Partial — via hook `Stop` event; no error classification |

**Verdict**: Superset is a developer productivity tool for running parallel interactive agent
sessions in git worktrees. It is not an orchestration library for non-interactive multi-model
pipeline use. The debate pipeline (`mde debate`) should NOT attempt to reuse or depend on Superset.

---

## Observations Useful for mde debate Architecture

1. **Codex hooks.json management**: Superset merges `~/.codex/hooks.json` to inject lifecycle
   hooks. The debate pipeline should NOT write to that file — it would conflict with Superset
   if both are used on the same machine. Use `codex` flags instead.

2. **Agent manifest pattern**: Superset's `builtin-terminal-agents.ts` manifest is a good
   reference for how to define per-agent metadata (command, flags, capabilities) in one place.

3. **Codex instability warning**: PR #2998 confirms Codex's internal session-log format changes
   without notice. The debate pipeline must use only public CLI flags.

4. **git ENOENT pattern**: Always resolve binary paths or fail with a clear error when a required
   tool is missing (don't let spawn throw ENOENT).

5. **Buffer backpressure at scale**: Running 10+ agents in parallel generates high output volume.
   The debate pipeline's subprocess stdout/stderr capture must handle this (use asyncio pipes with
   proper backpressure handling, not blocking reads).

---

## Tech Stack

- Electron (desktop shell) + React (UI) + Bun (runtime) + Turbo (monorepo)
- tRPC (IPC between main/renderer)
- Drizzle ORM + Neon (database)
- Biome (linter/formatter)
- License: Elastic License 2.0 (ELv2) — source available, NOT open source
