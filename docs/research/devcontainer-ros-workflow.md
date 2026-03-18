# Devcontainer Research ROS Workflow

This workflow operationalizes evidence-first research for devcontainer + `mise` + validation automation.

## Pipeline

1. Discover
- Generate 50-150 candidates using source-priority stack.
- Log all query strings and shortlist reasons.

2. Mine
- Score candidate repos and reduce to top 15.
- Extract code/workflow patterns from top 15.

3. Verify
- Map extracted patterns to local acceptance contracts:
  - devcontainer runtime checks
  - `mise` authority checks
  - `mde-verify` hard-gate semantics
  - AGENTS/skill enforcement checks

4. Synthesize
- Emit `adopt|adapt|reject` decisions.
- Produce final research bundle and implementation spec.

5. Spec
- Publish decision-complete spec in `docs/plans/`.

## Source Priority Stack

1. GitHub (`github`, `github-official`)
2. Reddit/HN (`mcp-reddit`, `mcp-hackernews`)
3. Curated lists (awesome/tool indexes)
4. Blog/news (`brave`, `kagisearch`, `dappier`)
5. X via API (`mcp-api-gateway`) when credentials exist

## Query Rules

### GitHub repository queries
Must include:
- stars floor (example: `stars:>50`)
- recency (example: `pushed:>=2025-01-01`)
- `archived:false`
- topical qualifiers/tags when available

### GitHub code queries
Use qualifiers such as:
- `path:.devcontainer`
- `content:mise`
- `content:chezmoi`
- `.github/workflows`

### Social/blog queries
Must include:
- date bounds
- minimum engagement thresholds
- implementation-specific keywords

## Required Evidence Files

- `reports/research-ros/<date>-discovery-records.jsonl`
- `reports/research-ros/<date>-pattern-records.jsonl`
- `reports/research-ros/<date>-social-pattern-records.jsonl`
- `reports/research-ros/<date>-decision-records.jsonl`
- `reports/research-ros/<date>-acceptance-records.jsonl`
- `reports/research-ros/<date>-research-bundle.json`

## Quality Gates

- At least 3 distinct source classes.
- At least 10 repositories mined.
- At least 20 non-repo artifacts reviewed.
- No decision without evidence link.
- Final spec includes machine-checkable acceptance commands/signals.
