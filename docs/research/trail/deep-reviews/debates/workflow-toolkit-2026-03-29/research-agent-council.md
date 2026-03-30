# Agent Council: Research Notes

**Source**: https://github.com/team-attention/agent-council
**Fetched**: 2026-03-29
**Stars**: 123 | **Forks**: 23 | **Issues**: 18 (9 open, 9 closed)

---

## Summary

Agent Council is a Claude Code skill (and Codex CLI skill) that orchestrates parallel calls to multiple AI CLIs — Codex, Gemini, and others — and synthesizes their responses using the host agent as "Chairman." Inspired by Karpathy's LLM Council but using subscription-based CLIs instead of direct API calls (zero additional API cost).

---

## 1. Coordination Pattern: 3-Stage Council

```
Stage 1: Parallel dispatch → all configured members receive the question simultaneously
Stage 2: Response collection → each member's output written to files in a job directory
Stage 3: Chairman synthesis → host agent (Claude / Codex) reads all outputs and synthesizes
```

The host agent acts as Chairman by default (`role: auto`). Optionally, a separate CLI can be specified as Chairman via `council.config.yaml`.

---

## 2. How Prompts Are Passed to Each CLI

### Architecture overview

`council.sh` (bash) delegates to `council-job.sh` (bash) which delegates to `council-job.js` (Node.js). The job runner (`council-job.js`) spawns one `council-job-worker.js` process per member using Node's `child_process.spawn()`.

Workers are spawned with `detached: true` and immediately `unref()`d — they run independently and are polled via filesystem.

### Prompt storage and delivery

1. The prompt text is written to `<jobDir>/prompt.txt` before any workers start.
2. Each worker reads `prompt.txt` at startup.
3. The prompt is appended as the last positional argument when spawning the member CLI binary.

This means `codex exec` becomes `codex exec "<full prompt text>"` and `gemini` becomes `gemini "<full prompt text>"`.

### Quote and shell escaping

`splitCommand()` is a custom shell-like tokenizer that handles backslash, single-quote, and double-quote tokens. Critically, `spawn()` is used (not `exec()`), so the final args array is passed directly to the OS without shell interpolation. The prompt arrives in the child process's argv as a raw string.

**Risk**: Prompts starting with `--` could be misinterpreted as flags by some CLIs, since the prompt is appended as a positional arg without `--` separator.

---

## 3. Output Capture

Each worker pipes stdout to `output.txt` and stderr to `error.txt` in a per-member subdirectory. Status is tracked in `status.json` which is updated atomically (write to tmp file, then rename).

File structure per job:
```
.jobs/council-<id>/
  prompt.txt
  job.json                    # metadata: members, chairman, config
  members/
    codex/
      status.json             # { member, state, startedAt, pid, exitCode, ... }
      output.txt              # stdout from "codex exec <prompt>"
      error.txt               # stderr
    gemini/
      status.json
      output.txt
      error.txt
```

---

## 4. Status Polling

In a real terminal: `council.sh` starts the job then enters a wait loop, polling `council-job.sh status` repeatedly until `overallState == "done"`.

In host-agent context (Claude/Codex tool cells): `council.sh` detects it is not in a TTY and returns a single `wait` JSON payload immediately. The payload contains structured todo/plan UI updates for both Claude (`todo_write.todos`) and Codex (`update_plan.plan`). The host agent is then expected to call `wait` again, then `results`, then `clean`.

Host-agent detection logic: checks `$CODEX_CACHE_FILE` env var OR checks if stdout/stderr are non-TTY AND the script path contains `/.codex/skills/` or `/.claude/skills/`.

---

## 5. Failure Handling and Retries

### Per-member failure states

| `state` value | Cause |
|---|---|
| `done` | Exit code 0 |
| `error` | Non-zero exit code |
| `missing_cli` | ENOENT — binary not on PATH |
| `timed_out` | SIGTERM sent after configurable timeout |
| `canceled` | SIGTERM from user or stop command |

**No retries** — each member runs once. Failed members do not block the council completing.

### Timeout

Configured via `settings.timeout` in YAML (seconds, 0 = disabled). When timeout fires, SIGTERM is sent to the child process.

---

## 6. Chairman Synthesis

Stage 3 is **not automated inside council.sh**. The skill's SKILL.md instructs the host agent (Claude/Codex) to read the collected results and synthesize directly in its own context. The `council.sh results` command formats the raw output files for the host agent to read.

An optional `chairman.command` in config is embedded in `job.json` but is not currently used to run synthesis automatically inside the script — it is metadata for the host agent.

---

## 7. Configuration

```yaml
# council.config.yaml
council:
  chairman:
    role: "auto"          # auto|claude|codex|gemini|...
    # command: "codex exec"  # optional: run synthesis inside council.sh

  members:
    - name: codex
      command: "codex exec"
      emoji: "robot"
      color: "BLUE"
    - name: gemini
      command: "gemini"
      emoji: "gem"
      color: "GREEN"

  settings:
    exclude_chairman_from_members: true   # prevent host from querying itself
    timeout: 120                          # seconds per member (0 = no timeout)
```

Config resolution order:
1. `--config` flag
2. `COUNCIL_CONFIG` env var
3. Skill-dir `council.config.yaml`
4. Repo-root `council.config.yaml`
5. Hardcoded fallback (claude + codex + gemini)

---

## 8. Issues Found in Tracker

**Substantive open issues**:

- **#13** (open): Proposal for Karpathy-style Stage 2 ranking pipeline — anonymize → peer rank → aggregate → synthesize. Currently Stage 1 outputs go directly to Chairman without blind ranking. This is a known quality gap.
- **#16** (open): Opencode as first-class host (3-host architecture).

**Closed issues revealing past problems**:

- **#1** (closed, resolved): Migration from Bash + awk YAML parsing to Node.js. Root cause: awk-based YAML parsing was fragile for complex config structures and broke on edge cases. Also had Windows compatibility issues.
- **#2** (closed, resolved): `parallel`, `timeout`, `show_thinking` settings were listed in config YAML but were not implemented. `timeout` is now implemented; `parallel` and `show_thinking` remain unimplemented.
- **#6** (closed, feature proposal): Per-member `system_prompt` field in config for persona/role injection — proposed but not yet implemented.
- **#3** (closed, feature proposal): stdin and file context input support (`--context <path>`) — proposed, not implemented.

---

## 9. Known Limitations

1. **Prompt as positional arg — no `--` separator**: The prompt is appended as the final positional argument to the CLI command without a `--` separator. Prompts starting with `--` may be misinterpreted as flags.

2. **Output is raw text**: `output.txt` is unprocessed stdout. No structured parsing of the CLI's output format.

3. **No retry logic**: A timed-out or missing-CLI member simply fails and the council continues without that member's input.

4. **Node.js runtime required**: Cannot self-install Node.js. This is documented prominently.

5. **Stage 3 synthesis is manual**: The Chairman step runs in the host agent's conversation, not as an automated script step.

6. **`splitCommand()` coverage**: Handles `\`, `'`, `"`, whitespace but does not handle all POSIX edge cases (subshells, process substitution, heredocs).

7. **No structured output contract**: There is no schema for what members should return. The Chairman receives raw CLI stdout, which may include ANSI codes, progress indicators, or other noise depending on the CLI.

---

## 10. Pull Request History

- No open PRs at time of fetch
- Key merged PRs: job-based architecture (PR #12), todo UI integration (PR #12), configurable chairman (PR #10), Codex install target (PR #10), OpenCode first-class support (PR #15)

---

## 11. Comparison with mde debate Pattern

| Dimension | agent-council | mde debate |
|---|---|---|
| CLI invocation | positional arg append | unknown — research needed |
| Output capture | file-based, async polling | unknown |
| Retries | none | unknown |
| Synthesis step | host-agent in-context | unknown |
| YAML fragility | was a problem (issue #1), fixed by Node migration | unknown |
| Prompt escaping | spawn() args array (no shell) | unknown |

---

## Source Catalog

| URL | Classification |
|---|---|
| https://github.com/team-attention/agent-council | HIGH |
| https://github.com/karpathy/llm-council | MEDIUM — inspiration/prior art |
| https://github.com/team-attention/agent-council/blob/main/skills/agent-council/scripts/council-job.js | HIGH |
| https://github.com/team-attention/agent-council/blob/main/skills/agent-council/scripts/council-job-worker.js | HIGH |
| https://github.com/team-attention/agent-council/blob/main/skills/agent-council/scripts/council.sh | HIGH |
