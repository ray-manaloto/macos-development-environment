# Multi-Agent Runner

This repo includes a small hook to orchestrate external multi-agent systems
for review, QA, and docs validation. It is intentionally tool-agnostic, so
you can plug in any runner that fits your stack.

## What it is
- `scripts/run-multi-agent.sh` dispatches three tasks (review, QA, docs sync).
- `MULTI_AGENT_RUNNER` is a command that accepts a single task string.
- The runner is responsible for using single or multiple agents and for
  logging results somewhere useful (for example, `reports/multi-agent`).

## Why use it
- Parallelize review/QA/docs for faster feedback.
- Use specialized prompts per task (less context mixing).
- Keep this repo independent from any single agent framework.

## How it works
1. Configure environment variables (runner path + optional args).
2. Run `scripts/run-multi-agent.sh`.
3. The script calls your runner once per task.
4. If `MULTI_AGENT_PARALLEL=1`, tasks run concurrently.
5. The runner returns non-zero on failure so the script can fail fast.

## Configure
Set these in your shell (prefer `~/.oh-my-zsh/custom/macos-env.zsh` so they
load automatically):

```bash
export MULTI_AGENT_RUNNER="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/agent-runner.sh"
export MULTI_AGENT_RUNNER_ARGS="--parallel --output reports/multi-agent"
export MULTI_AGENT_PARALLEL=1
```

### Recommended runner shapes

| Pattern | Pros | Cons | Good fit |
| --- | --- | --- | --- |
| Orchestrator framework (LangGraph, CrewAI, AutoGen, OpenHands) | Built-in coordination, shared memory/tools, rich logging | Heavier setup, higher cost, more moving parts | Recurring workflows with complex orchestration |
| Thin wrapper + per-task CLI | Simple, transparent, easy to debug | No shared memory, parallelism is manual | Small teams and quick feedback loops |
| Worktree-per-agent wrapper | Safe parallel edits, clean diffs per agent | More setup, more disk usage | Tasks that may modify files |

### Example runner (thin wrapper)

```bash
#!/usr/bin/env bash
set -euo pipefail

task="$1"
out_dir="reports/multi-agent"
mkdir -p "$out_dir"

case "$task" in
  "Review"*)
    some_agent_cli "Review for correctness and risks." > "$out_dir/review.md"
    ;;
  "Run QA"*)
    ./scripts/quality-checks.sh > "$out_dir/qa.txt"
    ;;
  "Ensure docs"*)
    some_agent_cli "Check docs vs scripts and repo layout." > "$out_dir/docs.md"
    ;;
  *)
    echo "Unknown task: $task" >&2
    exit 2
    ;;
esac
```

## Gotchas
- Parallel runs can clash when agents write to the same files. Use git
  worktrees or restrict multi-agent runs to read-only tasks.
- Output can interleave when parallelized. Write per-task logs to disk.
- Some agent CLIs require a TTY; prefer non-interactive flags for automation.
- Rate limits and cost spikes are common with parallel calls; set concurrency
  limits inside your runner.
- `MULTI_AGENT_RUNNER_ARGS` is whitespace-split. For complex args, wrap them
  in your runner script instead of trying to quote in the env var.
