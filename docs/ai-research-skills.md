# AI Research Skills Marketplace (Claude Code)

This repository installs the AI research skills marketplace from
`zechenzhangAGI/AI-research-SKILLs` into Claude Code. It provides a curated
library of research engineering skills for agent workflows.

## Install / Update
- Install or update the marketplace + all category plugins:
  - `scripts/install-ai-research-skills.sh`
- Reinstall everything even if already present:
  - `MDE_AI_RESEARCH_FORCE=1 scripts/install-ai-research-skills.sh`
- Override the marketplace source/name if needed:
  - `MDE_AI_RESEARCH_MARKETPLACE_REPO=org/repo`
  - `MDE_AI_RESEARCH_MARKETPLACE_NAME=ai-research-skills`

## Validate
- `scripts/verify-ai-research-skills.sh`

## Plugin Categories (19)
- model-architecture
- tokenization
- fine-tuning
- mechanistic-interpretability
- data-processing
- post-training
- safety-alignment
- distributed-training
- infrastructure
- optimization
- evaluation
- inference-serving
- mlops
- agents
- rag
- prompt-engineering
- observability
- multimodal
- emerging-techniques

## Notes
- Marketplace state is stored under `~/.claude/plugins/` (see
  `known_marketplaces.json` and `installed_plugins.json`).
- This uses the Claude Code plugin command surface (`/plugin`).
