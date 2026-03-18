
# Domain Team Governance Baseline

Domain specific setup and tooling work now routes through `configs/mde-domain-catalog.json` and one SDLC team per domain.
The baseline contract is:

- mirrored reference bundles live under `.artifacts/reference-mirror/`
- preset bundles live under `configs/tool-bundles/`
- accepted findings write back to `configs/mde-learning-registry.json`
- `mde:refs:verify`, `mde:preset:verify`, `mde:domain:verify`, and `mde:learn:verify` are hard gates
