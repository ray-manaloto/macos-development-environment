# gstack Research: /codex Skill and Multi-Model Workflow

**Date:** 2026-03-29
**Sources:** https://github.com/garrytan/gstack (README, issues, local install at ~/.claude/skills/gstack)
**Researcher:** Research Agent (Sonnet)

---

## Summary

gstack is Garry Tan's (YC CEO) open-source Claude Code skill library. It provides 20+ skills for
running a full sprint (plan → build → review → test → ship). The `/codex` skill is a "second opinion"
wrapper around OpenAI Codex CLI that runs an independent review from a different model.

---

## How /codex Uses Codex as a Second Opinion

The `/codex` skill is framed as the **"200 IQ autistic developer"** — a different AI system that
reviews the same diff independently, after Claude's own `/review` has run (or instead of it).

Three modes:
1. **Review mode** (`/codex review`) — pass/fail gate using `codex review --base <branch>`
2. **Challenge mode** (`/codex challenge`) — adversarial prompt using `codex exec` in read-only sandbox
3. **Consult mode** (`/codex <anything>`) — open-ended consultation with session continuity

The key design principle: Codex output is always shown **verbatim** inside a `CODEX SAYS (...)` block.
Claude adds synthesis only *after* the full output — never instead of it.

---

## CLI Flags and Prompt Patterns

### Review Mode (codex review)
```bash
codex review --base <base> -c 'model_reasoning_effort="xhigh"' --enable web_search_cached 2>"$TMPERR"
# With custom instructions:
codex review "focus on security" --base <base> -c 'model_reasoning_effort="xhigh"' --enable web_search_cached 2>"$TMPERR"
```

- `--base <branch>` — diff target
- `-c 'model_reasoning_effort="xhigh"'` — maximum reasoning effort (config flag)
- `--enable web_search_cached` — allows Codex to look up docs during review (OpenAI cached index)
- stderr: captured to a temp file for token/cost extraction

### Challenge and Consult Modes (codex exec)
```bash
codex exec "<prompt>" -s read-only -c 'model_reasoning_effort="xhigh"' --enable web_search_cached --json 2>/dev/null
# Session resume:
codex exec resume <session-id> "<prompt>" -s read-only ... --json
```

- `-s read-only` — sandbox mode (Codex cannot write files)
- `--json` — JSONL streaming output (events, not plain text)
- `resume <session-id>` — continues a previous conversation thread

### Model Selection
No model is hardcoded in the skill. Codex uses its current default automatically. Users can override with `-m <model-id>` which the skill passes through.

---

## How Codex Output Is Captured (Structured JSONL Parsing)

The challenge and consult modes use `--json` which produces JSONL event stream. The skill
parses this inline with a Python one-liner piped directly in bash:

```bash
codex exec "<prompt>" ... --json 2>/dev/null | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try:
        obj = json.loads(line)
        t = obj.get('type','')
        if t == 'item.completed' and 'item' in obj:
            item = obj['item']
            itype = item.get('type','')
            text = item.get('text','')
            if itype == 'reasoning' and text:
                print(f'[codex thinking] {text}')
                print()
            elif itype == 'agent_message' and text:
                print(text)
            elif itype == 'command_execution':
                cmd = item.get('command','')
                if cmd: print(f'[codex ran] {cmd}')
        elif t == 'turn.completed':
            usage = obj.get('usage',{})
            tokens = usage.get('input_tokens',0) + usage.get('output_tokens',0)
            if tokens: print(f'\ntokens used: {tokens}')
    except: pass
"
```

**Event types extracted:**
- `item.completed` with `type=reasoning` → `[codex thinking] ...` (reasoning traces)
- `item.completed` with `type=agent_message` → final response text
- `item.completed` with `type=command_execution` → `[codex ran] <cmd>` (tool calls Codex made)
- `turn.completed` → usage stats for cost display
- `thread.started` → `SESSION_ID:<id>` for session continuity (consult mode only)

**Session ID persistence:**
The parser extracts `SESSION_ID:<id>` from `thread.started` event. The skill saves this to
`.context/codex-session-id` so follow-up `/codex` invocations can resume the conversation.

**Review mode output** (non-JSONL): captured directly from stdout. Gate verdict is determined
by checking for `[P1]` markers in the output (P1 = critical finding → FAIL; P2 or none → PASS).

---

## Cross-Model Comparison Pattern

After `/codex review` runs, if `/review` (Claude's own review) was already run in the same
conversation, the skill generates a cross-model analysis block:

```
CROSS-MODEL ANALYSIS:
  Both found: [overlapping findings]
  Only Codex found: [unique to Codex]
  Only Claude found: [unique to Claude's /review]
  Agreement rate: X% (N/M total unique findings overlap)
```

This is in-context comparison only — no structured output file is written. Agreement rate and
unique findings are synthesized by Claude Code after both reviews are visible in context.

---

## Review Result Persistence

After a `/codex review`, the result is logged via:
```bash
~/.claude/skills/gstack/bin/gstack-review-log '{"skill":"codex-review","timestamp":"...","status":"...","gate":"pass|fail","findings":N,"findings_fixed":N}'
```

This writes to a local JSONL log used by `/retro` for sprint analytics. The log format is a
single JSON object (not streaming). `gstack-analytics` CLI reads it for personal dashboards.

---

## Error Handling and Known Failure Modes

### Binary Not Found
Step 0 of the skill checks `which codex` before anything else. If not found, stops with install instructions.

### Auth Error
Codex auth failures appear on stderr. The skill surfaces them verbatim:
> "Codex authentication failed. Run `codex login` in your terminal to authenticate via ChatGPT."

### Timeout
5-minute timeout (`timeout: 300000` on Bash calls). On timeout, tells user the diff may be too large.

### Empty Response
If the temp response file is empty or missing, surfaces the error — does not silently continue.

### Session Resume Failure
If `codex exec resume <id>` fails, deletes the session file and restarts fresh.

### CODEX_NOT_AVAILABLE Inconsistency (Issue #463, open 2026-03-24)
Some skills silently skip the second-opinion phase when Codex is not installed. Other skills
(plan-eng-review, ship) fall back to a Claude subagent via the Agent tool. This is inconsistent.
`/office-hours` Phase 3.5 silently skips with no message — a known regression against the
fallback pattern established elsewhere.

---

## Multi-CLI Limitation (Issue #619, open 2026-03-29)

12+ skills hardcode `codex exec` with Codex-specific flags. Users with Gemini CLI but not Codex
cannot use the second-opinion features. Key flags with no direct Gemini equivalent:
- `codex exec resume <session-id>` — no Gemini session continuity
- `-c 'model_reasoning_effort=...'` — dropped silently in shims
- `--json` JSONL output mode — Gemini doesn't produce structured trace events

Issue proposes a configurable `outside_voice.backend` in `~/.gstack/config.yaml` with
adapter translations. Currently unresolved as of 2026-03-29.

---

## Prompt Escaping and Shell Safety

The challenge/consult prompts are passed as shell string arguments to `codex exec "<prompt>"`.
Quotes inside the prompt are escaped by Claude Code when constructing the bash call.
The adversarial default prompt is hardcoded (no user-controlled injection risk):

```
"Review the changes on this branch against the base branch. Run `git diff origin/<base>` to see the diff. Your job is to find ways this code will fail in production..."
```

User-supplied focus areas (e.g., `/codex challenge security`) are interpolated into a
template string — no explicit shell escaping in the skill source. This is a latent risk if
user input contains unescaped quotes or backticks.

---

## /codex Skill: Metadata

From `SKILL.md.tmpl`:
- `preamble-tier: 3` — mid-weight context preamble
- `allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion`
- No Agent tool (subagents not spawned from /codex itself)
- All modes: 5-minute timeout on Bash calls
- All modes: `model_reasoning_effort="xhigh"`, `--enable web_search_cached`
- Consult mode only: session continuity via `.context/codex-session-id`

---

## Relationship to Our mde debate Implementation

| gstack /codex | mde debate |
|---|---|
| `codex exec ... --json` piped to inline Python | `mde debate invoke` calls CLI, parses output in Python |
| JSONL event stream parsing inline | Structured output to JSON files |
| Stderr → temp file for tokens | Captured in subprocess result |
| Session ID from `thread.started` event | No session continuity currently |
| Cross-model comparison in-context | Written to structured debate record |
| Gate verdict from `[P1]` markers | Configurable verdict extraction |
| `gstack-review-log` JSONL append | `.generated/learnings/` for dream pipeline |

Key difference: gstack /codex is read-only and presents output to the human for action.
mde debate is designed to feed findings back into an autonomous pipeline (dream → propose → apply).

---

## Source Catalog Entries

- https://github.com/garrytan/gstack — main repo (README)
- https://github.com/garrytan/gstack/issues/619 — multi-CLI backend proposal (Gemini support)
- https://github.com/garrytan/gstack/issues/463 — Codex unavailability fallback inconsistency
- ~/.claude/skills/gstack/codex/SKILL.md.tmpl — local installed skill source (authoritative)
- ~/.claude/skills/gstack/review/SKILL.md.tmpl — /review skill for cross-model context
