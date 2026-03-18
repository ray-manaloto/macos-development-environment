# Devcontainer Image Release Team

This team prepares the GHCR-backed devcontainer image release workflow using the shared `scripts/agent-runner.sh` contract.

## Roles
- `image-authoring-agent`: Dockerfile pinning, OCI labels, and image-source-of-truth rules.
- `gha-publish-agent`: GitHub Actions build, validate, publish, and attestation flow.
- `dependency-bot-agent`: Dependabot policy for Docker and GitHub Actions updates.
- `validation-agent`: local and CI verification gates, including strict JSON parsing.
- `docs-agent`: final operator handoff and rollback/debug guidance.

## Run
```bash
scripts/teams/run-devcontainer-image-release-team.sh
```

## Validate
```bash
scripts/teams/validate-devcontainer-image-release-output.sh
```

## Outputs
- `reports/devcontainer-image-release/<date>-01-image-authoring.md`
- `reports/devcontainer-image-release/<date>-02-gha-publish.md`
- `reports/devcontainer-image-release/<date>-03-dependency-bot.md`
- `reports/devcontainer-image-release/<date>-04-validation.md`
- `reports/devcontainer-image-release/<date>-05-docs-handoff.md`
