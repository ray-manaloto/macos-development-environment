# Research: kingbootoshi/codex-orchestrator

**Date:** 2026-03-29
**Sources:** https://github.com/kingbootoshi/codex-orchestrator (README, src/cli.ts, src/jobs.ts, src/tmux.ts, plugins/codex-orchestrator/README.md)
**Status:** 256 stars, 38 forks -- actively maintained

---

## Overview

codex-orchestrator is a Bun/TypeScript CLI (`codex-agent`) that spawns OpenAI Codex CLI agents inside detached tmux sessions and provides a job management layer on top. It is designed specifically for Claude Code orchestration: Claude acts as the strategic layer (planning, synthesis), Codex agents handle execution (research, implementation, review).

---

## How It Delegates Tasks to Codex CLI Agents

The delegation model is:

1. `codex-agent start "<prompt>" [flags]` creates a job record (JSON in `~/.codex-agent/jobs/<jobId>.json`)
2. Spawns a detached tmux session: `tmux new-session -d -s codex-agent-<jobId> -c <cwd>`
3. Inside the session, runs codex under `script` for full output capture
4. Sends the prompt into the running codex TUI via `tmux send-keys`
5. Returns the job ID immediately; codex runs in background
6. Orchestrator polls/captures via `tmux capture-pane` or reads the `.log` file

Job states: `pending -> running -> completed | failed`

The pipeline pattern promoted by the plugin skill:
```
Ideation -> Research -> Synthesis -> PRD -> Implementation -> Review -> Testing
(Claude)    (Codex)    (Claude)    (Claude)   (Codex)        (Codex)   (Codex)
```

---

## How It Captures Structured Output

### Live Output (session running)

```
tmux capture-pane -t "<session>" -p
tmux capture-pane -t "<session>" -p -S -   # full scrollback, 50MB buffer
```

### Logged Output (session ended)

All session output is captured via the `script` command when the session starts:
- macOS: `script -q "<logFile>" codex <args>`
- Linux: `script -q -c "codex <args>" "<logFile>"`

Output is available in `~/.codex-agent/jobs/<jobId>.log` even after the tmux session exits.

### Structured Metadata (tokens, files, summary)

Codex CLI writes JSONL session files to `~/.codex/sessions/`. The orchestrator reads these via `src/session-parser.ts` to extract:
- `tokens.input`, `tokens.output`, `tokens.context_window`, `tokens.context_used_pct`
- `files_modified: string[]`
- `summary: string`

The `jobs --json` command merges parsed session data with job records into a single structured JSON -- the intended polling mechanism for Claude.

### The `.log` File Fallback

If the tmux session is gone, `getJobOutput()` falls back to reading `~/.codex-agent/jobs/<jobId>.log`. This is reliable since `script` captures everything from session start.

---

## How It Passes Complex Prompts to Codex

### Short Prompts (fewer than 5000 chars)

```
const promptContent = options.prompt.replace(/'/g, "'\\''" );
tmux send-keys -t "<session>" '<promptContent>'
sleep 0.3
tmux send-keys -t "<session>" Enter
```

Single-quote shell escaping: replace `'` with `'\''`. Standard POSIX approach.

### Long Prompts (5000 chars or more)

```
# Write prompt to file
writeFileSync("<jobId>.prompt", options.prompt);

# Use tmux clipboard approach
tmux load-buffer "<promptFile>"
tmux paste-buffer -t "<session>"
sleep 0.3
tmux send-keys -t "<session>" Enter
```

The prompt file is always written as `<jobId>.prompt` regardless of length (for reference/debugging).

### Codex CLI Configuration Arguments

```
codex -c model="<model>"
      -c model_reasoning_effort="<effort>"
      -c skip_update_check=true
      -c 'notify=["bun","run","<notifyHook>","<jobId>"]'
      -a never
      -s <sandbox>
```

Flags used:
- `-c key=value` -- inline config overrides (model, reasoning effort, skip update check, notify hook)
- `-a never` -- auto-approval mode (never ask for confirmation)
- `-s <mode>` -- sandbox: `read-only | workspace-write | danger-full-access`

### Update Prompt Skip Sequence

After session creation, a deliberate 3-step sequence skips the Codex update nag:
```
sleep 1                                      # wait for codex to init
tmux send-keys -t "<session>" "3"            # select "skip until next version"
sleep 0.5
tmux send-keys -t "<session>" Enter
sleep 1
# NOW send the actual task prompt
```

---

## Codex CLI Argument Parsing Issues

From source code analysis:

1. **Single-quote escaping in shell commands**: Uses `replace(/'/g, "'\\''" )` -- standard POSIX but breaks if the prompt contains shell metacharacters that survive the quoting boundary in edge cases.

2. **Long prompt threshold at 5000 chars**: Chosen to avoid `tmux send-keys` buffer overflow / TUI rendering issues with large strings. The exact threshold is empirical.

3. **No stdin-based approach**: Codex CLI is a TUI application. All input must go through tmux send-keys or paste-buffer. There is no `echo "prompt" | codex` path.

4. **Notify config value escaping**: The notify hook is embedded in `-c 'notify=[...]'` with nested escaping -- fragile if the hook path contains special characters.

5. **Issues list was not accessible** (GitHub requires authentication for issue listings) -- specific bug reports about escaping failures could not be retrieved.

---

## Workarounds for Output Capture Failures

### ANSI / TUI Noise

Codex runs in interactive TUI mode, producing heavy ANSI escape sequences. The `--strip-ansi` / `--clean` flag invokes `src/output-cleaner.ts` to strip these from `capture` and `output` command output. This is essential for machine-readable output.

### Capture-Pane Limitations

`tmux capture-pane -p` only captures the visible pane (typically ~100 lines of terminal height). Full scrollback requires `-S -` (start of history). The code sets a 50MB maxBuffer for full history capture.

### Session-Gone Fallback

When the tmux session has exited, output falls back to the `.log` file written by `script`. This is the primary mechanism for completed jobs.

### Turn-Complete Signal

`notify-hook.ts` is invoked by Codex when a turn completes, writing a signal file (`<jobId>.turn-complete`). The `await-turn` command polls this file. This avoids busy-polling `tmux capture-pane` looking for "idle" text patterns.

---

## tmux-Based Orchestration Patterns

### Session Naming

Sessions are named `codex-agent-<8-hex-jobId>` (e.g., `codex-agent-8abfab85`). The prefix is configurable.

### Detached Session Lifecycle

```
tmux new-session -d -s <name> -c <cwd> '<shellCmd>'
  script -q <logFile> codex <args>     (macOS)
    codex TUI running the agent
```

The session stays alive after codex exits via `;read` at the end of the shell command, allowing post-completion capture.

### Bidirectional Communication

- Orchestrator to agent: `tmux send-keys -t <session> '<message>'` + Enter
- Agent to orchestrator: `tmux capture-pane` for output; signal files for turn completion
- Interactive: `tmux attach -t <session>` (human can take over any session)

### Parallel Agents

Each job gets its own tmux session. N parallel agents = N tmux sessions. Claude can spawn many and poll with `jobs --json` to get all statuses in one call.

### Session Persistence

tmux sessions survive the orchestrator process exiting. Jobs can be rechecked with `codex-agent jobs` after an orchestrator restart because all state lives in `~/.codex-agent/jobs/*.json`.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| tmux over subprocess | Codex is a TUI app -- it reads from a terminal, not stdin |
| `script` for logging | Captures all terminal output including TUI artifacts |
| File-based long prompts | Shell arg length limits; avoids buffer overflow in send-keys |
| 0.3s sleep before Enter | Codex TUI needs time to register typed text before submission |
| `jobs --json` for polling | Single command returns all metadata; avoids multiple round-trips |
| JSONL session files | Codex natively writes these; structured data without screen scraping |
| `-a never` flag | Removes interactive confirmation dialogs that would block agents |
| Separate prompt file | Preserved for debugging; also the injection source for long prompts |

---

## Implications for mde Debate Implementation

1. **File-based prompt passing is the correct approach** for complex/long prompts. Write to a temp file, use `tmux load-buffer` + `paste-buffer` rather than escaping in shell args.

2. **The `script` command is essential** for capturing TUI output from codex. Plain stdout redirection does not work.

3. **Platform-specific script syntax**: macOS uses `script -q <file> <cmd>`, Linux uses `script -q -c "<cmd>" <file>`.

4. **Update prompt skip** must happen before sending the task prompt -- Codex shows an update nag on first launch that blocks input.

5. **ANSI stripping is necessary** for machine-readable output. Must be a post-processing step since `--strip-ansi` is applied at read time, not capture time.

6. **The 0.3s sleep pattern** before Enter is a known TUI timing requirement for reliable input, not an arbitrary hack.

7. **`-a never`** is the correct flag to make codex non-interactive (suppresses confirmation prompts for file edits).

8. **Turn detection via notify hook + signal file** is cleaner than polling capture-pane for "idle" text patterns. The notify config key in codex supports a bun/node runner command.

---

## Source Catalog

| URL | Status | Classification |
|---|---|---|
| https://github.com/kingbootoshi/codex-orchestrator | Fetched | HIGH -- primary source |
| https://github.com/kingbootoshi/codex-orchestrator/blob/main/src/tmux.ts | Fetched (via blob) | HIGH -- core implementation |
| https://github.com/kingbootoshi/codex-orchestrator/blob/main/src/jobs.ts | Fetched (via blob) | HIGH -- job lifecycle |
| https://github.com/kingbootoshi/codex-orchestrator/blob/main/src/cli.ts | Fetched (via blob) | HIGH -- CLI interface |
| https://github.com/kingbootoshi/codex-orchestrator/blob/main/plugins/codex-orchestrator/README.md | Fetched | MEDIUM -- plugin docs |
| https://github.com/kingbootoshi/codex-orchestrator/issues | SKIP (requires auth) | MEDIUM -- could not retrieve |
| https://github.com/kingbootoshi/codex-orchestrator/pulls | SKIP (requires auth) | LOW -- no open PRs visible |
