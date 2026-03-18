# Devcontainer Dependency Bot Prompt

Objective: define automatic update policy for the devcontainer base image and GitHub Actions pins.

Requirements:
- Cover Dependabot configuration for `docker` and `github-actions`.
- Keep updates PR-gated with no scheduled rebuild lane in v1.
- Explain how digest and SHA updates are reviewed and merged safely.
- Include operator-visible expectations for update cadence and scope.
