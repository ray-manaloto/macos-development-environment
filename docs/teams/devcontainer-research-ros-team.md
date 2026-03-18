# Devcontainer Research ROS Team

This team runs a deterministic research workflow for devcontainer setup automation.

## Pipeline

1. `scout-agent` (Discover)
- Builds candidate pool from prioritized sources.
- Skills: `research-source-discovery`, `mise-enforcement`.

2. `repo-mining-agent` (Mine)
- Extracts repository patterns with proof and scoring.
- Skills: `github-repo-mining`, `mise-enforcement`.

3. `social-signal-agent` (Mine social/blog)
- Extracts practical lessons from social and blog artifacts.
- Skills: `social-signal-mining`, `mise-enforcement`.

4. `validation-agent` (Verify)
- Maps patterns to local acceptance gates (`mde-verify`, runtime, policy checks).
- Skills: `evidence-synthesis`, `mise-enforcement`.

5. `synthesis-agent` (Synthesize + Spec)
- Produces adopt/adapt/reject decisions and final implementation spec.
- Skills: `evidence-synthesis`, `writing-plans`, `mise-enforcement`.

## Config + Prompts

- Team config: `configs/agent-teams/devcontainer-research-ros-team.yaml`
- Prompt templates: `prompts/agent-team/devcontainer-research-ros/*.md`

## Output Locations

- Reports: `reports/research-ros/`
- Artifacts: `.artifacts/research-ros/`

## Execute

```bash
scripts/teams/run-devcontainer-research-ros-team.sh
```

The output validator enforces method/quality gates:

```bash
scripts/teams/validate-devcontainer-research-ros-output.sh
```
