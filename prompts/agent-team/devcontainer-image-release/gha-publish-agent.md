# Devcontainer GHCR Publish Prompt

Objective: define the GitHub Actions workflow that builds, validates, and publishes the devcontainer image to GHCR.

Requirements:
- Cover PR smoke build, artifact handoff, validation, and publish-on-main behavior.
- Require SHA-pinned actions and explicit permissions.
- Cover multi-arch publication and provenance attestation.
- Include failure gates and rollback/debug notes.
