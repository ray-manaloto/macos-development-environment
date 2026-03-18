
# MDE Autoresearch Team

This team runs the bounded repo wide research loop, but it must route authority decisions through the owning domain team before it finalizes synthesis or guidance changes.

## Run
```bash
MDE_DOMAIN=mise-core scripts/teams/run-mde-autoresearch-team.sh
```

Override the active domain:

```bash
MDE_DOMAIN=python-pixi-uv scripts/teams/run-mde-autoresearch-team.sh
```

## Domain delegation
- Read `configs/mde-domain-catalog.json` before classifying new work.
- Run `scripts/teams/run-mde-domain-team.sh --domain <domain-id>` before final decision records or guidance updates are accepted.
- Use `configs/mde-reference-sources.json`, `configs/mde-preset-catalog.json`, and `configs/mde-learning-registry.json` as the domain handoff surfaces.
