# Octokit SDLC Agent Team

This team orchestrates a full SDLC workflow for the Octokit discovery library using specialized subagents.

## Subagents

1. `spec-planner`
- Writes the implementation spec and atomic execution plan.
- Activates: `writing-plans`, `brainstorming`, `software-architecture`.

2. `spec-reviewer`
- Reviews plan for correctness/risk and returns approval status.
- Activates: `requesting-code-review`, `review-verification-protocol`, `code-review-checklist`.

3. `bdd-test-designer`
- Converts approved plan into BDD tests (red-first).
- Activates: `test-driven-development`, `vitest-testing`, `testing-patterns`.

4. `coding-agent`
- Implements plan with TDD constraints and verification evidence.
- Activates: `test-driven-development`, `verification-before-completion`, `clean-code`.

5. `qa-functional`
- Validates functionality and UX of library + CLI.
- Activates: `webapp-testing`, `systematic-debugging`, `verification-before-completion`.

6. `qa-nonfunctional`
- Validates reliability, metadata completeness, and security posture.
- Activates: `verification-before-completion`, `security-review`, `review-verification-protocol`.

7. `docs-agent`
- Produces docs for humans and AI/LLM agent consumers.
- Activates: `doc-coauthoring`, `documentation-templates`, `prompt-engineering`.

## Config + Prompt Templates

- Team config: `configs/agent-teams/octokit-sdlc-team.yaml`
- Subagent prompt templates: `prompts/agent-team/octokit-sdlc/*.md`

## Output Locations

- Common output directory: `reports/octokit-sdlc/`
- Shared generated artifacts: `.artifacts/octokit-sdlc/`

Both are gitignored.

## Runner Requirements

Set `MULTI_AGENT_RUNNER` to a command/script that accepts a single task string.
See `docs/multi-agent-runner.md`.

Example:

```bash
export MULTI_AGENT_RUNNER="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/agent-runner.sh"
```

## Execute Team

```bash
scripts/teams/run-octokit-sdlc-team.sh
```

The runner now performs a mandatory validation step:

```bash
scripts/teams/validate-octokit-sdlc-output.sh
```

The overall run fails if required files are missing, empty, or contain placeholder output.

Optional flags (via env vars):

- `OCTOKIT_TEAM_PARALLEL_QA=1|0` (default `1`)
- `OCTOKIT_TEAM_OUT_DIR=reports/octokit-sdlc`
- `OCTOKIT_TEAM_ARTIFACT_DIR=.artifacts/octokit-sdlc`
- `OCTOKIT_TEAM_DATE=YYYY-MM-DD`

## SDLC Order

1. Spec/plan
2. Spec review
3. BDD tests
4. Code execution
5. QA (functional + non-functional)
6. Documentation
7. Validation gate
