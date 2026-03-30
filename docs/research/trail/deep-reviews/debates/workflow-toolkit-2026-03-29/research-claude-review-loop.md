# claude-review-loop: Deep Research Notes

**Source:** https://github.com/hamelsmu/claude-review-loop
**Fetched:** 2026-03-29
**Agent:** researcher
**Version documented:** plugin.json v1.8.0

---

## Summary

`claude-review-loop` is a Claude Code plugin (not a standalone script) that implements a
two-phase task→review lifecycle using a **Stop hook** to intercept Claude's exit. The plugin
invokes `codex` as the independent reviewer. Understanding its internals resolves several
open questions about how to structure a debate loop in the `mde` pipeline.

---

## Orchestration Architecture

### Two-phase state machine

State is persisted in `.claude/review-loop.local.md` as YAML frontmatter:

```yaml
---
active: true
phase: task           # transitions to "addressing" after stop hook fires
review_id: 20260329-153042-a3f9b2
started_at: 2026-03-29T15:30:42Z
---
<original task prompt>
```

Phase transitions:
1. **`task`** — Claude works on the task. When Claude calls Stop, the hook fires.
2. **`addressing`** — Hook has prepared the Codex runner; Claude runs Codex, then addresses findings. Next Stop call verifies the review file exists, then approves exit.

The hook uses a fail-open design throughout: any error clears state and returns `{"decision":"approve"}`.

### Stop hook mechanics (hooks/stop-hook.sh)

The hook:
1. Reads stdin (required to avoid broken pipe — the hook ignores the JSON body)
2. Parses the state file with `sed` (`parse_field()` extracts YAML frontmatter values)
3. In `task` phase:
   - Builds the full Codex multi-agent prompt via `build_review_prompt()`
   - Writes prompt to `.claude/review-loop-codex-prompt.txt`
   - Writes a bash runner script to `.claude/review-loop-run-codex.sh`
   - Transitions phase to `addressing` via `awk`-based rewrite (not `sed`, for robustness)
   - Returns `{"decision":"block", "reason":"...", "systemMessage":"..."}` telling Claude to run the script
4. In `addressing` phase:
   - If `reviews/review-<id>.md` exists: returns `{"decision":"approve"}`, cleans up
   - If review file is missing but runner script exists: re-blocks Claude, prompts retry (max 2 retries)
   - If both missing: fail-open, clean up

Hook timeout is **30 seconds** (configured in `hooks/hooks.json`). The hook itself is fast — it only writes files. Codex runs separately via Claude's Bash tool.

### Why the hook does NOT run Codex directly

An explicit design decision documented in the source comments:

> "Instead of running Codex inside this hook (which blocks Claude and hides all output),
> we write the prompt and a runner script, then tell Claude to execute it via Bash so
> Codex output streams to the user."

This is the key insight: **the stop hook is a file-writer + state machine, not a subprocess runner**.

---

## Codex Invocation Pattern

### How the runner script is generated

The hook generates `.claude/review-loop-run-codex.sh` via a heredoc with selective escaping:

```bash
cat > "$RUNNER_SCRIPT" << RUNNER_EOF
#!/usr/bin/env bash
# ...
codex ${CODEX_FLAGS} exec "$(cat ".claude/review-loop-codex-prompt.txt")" || CODEX_EXIT=$?
RUNNER_EOF
```

Key observations:
- `${CODEX_FLAGS}` is **expanded at write time** (baked into the generated script)
- All other `$` variables inside the heredoc are **escaped** (`\$`) so they stay literal
- The prompt is read from a file at runtime via `$(cat "...")` — NOT passed directly on the CLI
- This avoids all shell escaping issues with multi-line prompts containing special characters

### CLI flags used

Default: `codex --dangerously-bypass-approvals-and-sandbox exec "<prompt>"`

Configurable via `REVIEW_LOOP_CODEX_FLAGS` env var. The README documents:
- Default: `--dangerously-bypass-approvals-and-sandbox`
- Safer alternative: `--sandbox workspace-write`

The `exec` subcommand is used (not `-p` / `--prompt`). This is the non-interactive Codex mode.

### Codex multi-agent requirement

Requires `~/.codex/config.toml`:
```toml
[features]
multi_agent = true
```

The `/review-loop` command auto-enables this on first use. The stop hook validates this is set
before proceeding and returns a user-facing error message if not.

---

## Prompt Delivery: File vs Stdout

The prompt is written to a file (`.claude/review-loop-codex-prompt.txt`) and read by the
runner script at runtime. This is intentional:

- The prompt is a multi-line, multi-section document (see below)
- Shell heredoc quoting makes it impossible to safely embed this prompt as a CLI argument
- Writing to a file sidesteps all quoting/escaping edge cases

The prompt itself tells Codex to orchestrate 2–4 parallel sub-agents and write consolidated
output to `reviews/review-<id>.md`. Codex is responsible for creating that file.

---

## Structured Output: Codex Writes to File

Output capture mechanism: **Codex writes the review file directly**. Claude does not parse
codex stdout. The review is at a deterministic path: `reviews/review-${REVIEW_ID}.md`.

The review ID format is validated with a regex before use:
```bash
echo "$REVIEW_ID" | grep -qE '^[0-9]{8}-[0-9]{6}-[0-9a-f]{6}$'
```
This prevents path traversal. The format is `YYYYMMDD-HHMMSS-RAND6HEX`.

The Codex prompt instructs:
> "IMPORTANT: Spawn one agent per review path below. Wait for all agents to finish.
> Then deduplicate overlapping findings and write the consolidated review to: ${REVIEW_FILE}"

Each agent is instructed to **return findings as structured text (not write to files)**;
only the consolidation step writes the final file.

---

## Multi-agent Review Prompt Structure

The `build_review_prompt()` function in stop-hook.sh generates the full prompt inline.
It spawns up to 4 parallel agents:

| Agent | Condition | Focus |
|-------|-----------|-------|
| Diff Review | Always | `git diff` + `git diff HEAD~5`; code quality, tests, OWASP security |
| Holistic Review | Always | Project structure, AGENTS.md, documentation, architecture |
| Next.js Review | `next.config.*` or `"next"` in package.json | App Router, Server Components, caching |
| UX Review | `app/`, `pages/`, `public/`, or `index.html` exists | agent-browser E2E, accessibility |

Project type detection uses shell conditionals before building the prompt, so agents 3 and 4
are conditionally included in the prompt text itself — the same prompt is passed to Codex
regardless, and Codex decides which agents to spawn based on the instructions.

---

## Known Workarounds and Failure Modes

### Codex not writing the expected file (retry logic)

If Claude reaches phase `addressing` but `reviews/review-<id>.md` doesn't exist:
- The hook blocks exit again with instructions to re-run the script
- A counter in `.claude/review-loop-retries` limits this to **2 retry attempts**
- After 2 failures, the hook fails-open (approves exit, cleans up)

This handles the case where Codex exits non-zero or fails to produce output.

### ERR trap safety net

The entire hook is wrapped in an ERR trap:
```bash
trap 'log "ERROR: ..."; rm -f <temp files>; printf "{\"decision\":\"approve\"}\n"; exit 0' ERR
```
Any unexpected error exits cleanly rather than hanging Claude.

### Phase transition robustness

Phase transition uses `awk` not `sed` to avoid regex anchoring issues with YAML whitespace variants.
The transition is verified by re-reading the state file after writing.

### No open issues or PRs

As of 2026-03-29, the repository has **0 open issues** and **0 open PRs** (625 stars, 37 forks).
The issues page required authentication to show closed issues — no bug reports were accessible.

---

## File Structure (actual repo layout)

The README shows a flat layout but the actual structure uses a `plugins/` directory:

```
plugins/review-loop/
├── .claude-plugin/plugin.json
├── AGENTS.md
├── CLAUDE.md               (symlink to AGENTS.md)
├── commands/
│   ├── review-loop.md
│   └── cancel-review.md
├── hooks/
│   ├── hooks.json          (Stop hook, 30s timeout)
│   └── stop-hook.sh
└── scripts/
    └── setup-review-loop.sh
```

The hook path uses `${CLAUDE_PLUGIN_ROOT}` for portability:
```json
"command": "${CLAUDE_PLUGIN_ROOT}/hooks/stop-hook.sh"
```

---

## Implications for mde debate pipeline

1. **File-based prompt delivery is the correct pattern** for multi-line prompts to Codex.
   Never pass a long structured prompt as a CLI argument — write to a temp file and `cat` it.

2. **The stop hook should not run the secondary model** — it should only write files and
   return a block decision. Let Claude run the secondary model via its Bash tool, which
   streams output to the user and respects timeouts.

3. **File-based output verification** works: write to a deterministic path, check existence
   after the secondary model exits, retry once on failure, then fail-open.

4. **The `codex exec` subcommand** is the correct non-interactive Codex flag. Not `-p`.

5. **Multi-agent inside Codex** is the key mechanism for parallel review. The prompt
   instructs Codex to orchestrate sub-agents; Claude Code does not spawn them directly.

6. **State machine in a flat file** (YAML frontmatter in `.claude/`) is a viable and
   lightweight pattern. Simpler than a JSON database for two-state machines.

7. **Retry ceiling matters**: without a retry limit, a broken Codex run would loop forever.
   Two retries is the observed ceiling here.

---

## URLs Cataloged

- https://github.com/hamelsmu/claude-review-loop (main repo)
- https://github.com/hamelsmu/claude-review-loop/issues (requires auth for closed issues)
- https://github.com/hamelsmu/claude-review-loop/pulls (no open PRs)
- https://raw.githubusercontent.com/hamelsmu/claude-review-loop/main/plugins/review-loop/hooks/stop-hook.sh
- https://raw.githubusercontent.com/hamelsmu/claude-review-loop/main/plugins/review-loop/scripts/setup-review-loop.sh
- https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum (credited inspiration)
- https://x.com/ryancarson/article/2016520542723924279 (credited inspiration: compound engineering loop)
- https://developers.openai.com/codex/multi-agent/ (Codex multi-agent docs)
- https://agent-browser.dev/ (UX review dependency)
