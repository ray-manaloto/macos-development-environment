# Multi-Agent Runner

This repo includes a runner hook to orchestrate external multi-agent systems
for review, QA, and docs validation. It is intentionally generic so you can
plug in your preferred runner.

## Configure
Set one of the following environment variables:
- `MULTI_AGENT_RUNNER`: a command that accepts a task string.
- `MULTI_AGENT_RUNNER_ARGS`: optional extra args.

Example:

```bash
export MULTI_AGENT_RUNNER="/path/to/your-runner"
export MULTI_AGENT_RUNNER_ARGS="--parallel"
```

## Usage

```bash
scripts/run-multi-agent.sh
```

This will dispatch three passes:
- Review
- QA
- Docs sync
