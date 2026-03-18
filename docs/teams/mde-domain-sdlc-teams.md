
# MDE Domain SDLC Teams

Each domain in `configs/mde-domain-catalog.json` owns one SDLC team config under `configs/agent-teams/`.

## Required stages
- `mirror-refresh-agent`
- `docs-tutorial-agent`
- `repo-mining-agent`
- `social-signal-agent`
- `authority-agent`
- `implementation-agent`
- `validation-agent`
- `learning-consolidator-agent`

## Run
```bash
scripts/teams/run-mde-domain-team.sh --domain python-pixi-uv
```
