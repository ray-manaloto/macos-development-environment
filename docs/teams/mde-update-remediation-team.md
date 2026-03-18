# MDE Update Remediation Team

This team remediates one declared target at a time using the modernization matrix, the ownership registry, and a supplied evidence pack. It supports `mde:update` log-driven remediation, but it is no longer limited to a single maintenance log or a single proof command.

Before it writes a spec or plan, it must classify the target through `configs/mde-domain-catalog.json` and run the owning domain SDLC team.

## Roles
- `log-triage-agent`: classify the active remediation target and evidence into issue buckets.
- `maintenance-remediation-agent`: review owning scripts, tasks, registries, and docs for fixes tied to the target.
- `parity-sync-agent`: audit native macOS vs devcontainer behavior where the target crosses both surfaces.
- `validation-agent`: define proof commands and acceptance checks.
- `spec-agent`: write the remediation spec.
- `plan-agent`: write the sequenced next-step plan.

## Run
```bash
scripts/teams/run-mde-update-remediation-team.sh
```

Run a specific remediation item:

```bash
scripts/teams/run-mde-update-remediation-team.sh scripts/install-agent-stack.sh /absolute/path/to/evidence.log
```

Override the proof command and success criterion:

```bash
MDE_UPDATE_REMEDIATION_PROOF_COMMAND='bash scripts/install-agent-stack.sh' \
MDE_UPDATE_REMEDIATION_SUCCESS_CRITERION='installer exits successfully and validation tests pass' \
scripts/teams/run-mde-update-remediation-team.sh scripts/install-agent-stack.sh /absolute/path/to/evidence.log
```

The delegated domain output will be written under `reports/mde-domain-sdlc/<domain>/` and must be treated as an input to the remediation spec and plan.

## Validate
```bash
scripts/teams/validate-mde-update-remediation-output.sh "$(date +%F)" reports/mde-update-remediation scripts/install-agent-stack.sh /absolute/path/to/evidence.log
```

## Outputs
- `reports/mde-update-remediation/<date>-01-log-triage.md`
- `reports/mde-update-remediation/<date>-02-maintenance-remediation.md`
- `reports/mde-update-remediation/<date>-03-parity-sync.md`
- `reports/mde-update-remediation/<date>-04-validation.md`
- `docs/plans/<date>-mde-update-remediation-spec.md`
- `docs/plans/<date>-mde-update-remediation-plan.md`
