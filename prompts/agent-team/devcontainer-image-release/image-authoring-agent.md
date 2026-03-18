# Devcontainer Image Authoring Prompt

Objective: define the authored Dockerfile contract, upstream base-image pin policy, OCI metadata requirements, and local reproduction commands.

Requirements:
- Cover `.devcontainer/Dockerfile` and `.devcontainer/devcontainer.json`.
- Require explicit version + digest pinning for the upstream devcontainer base image.
- Require OCI labels, especially repository source metadata.
- Include proof commands for local build and smoke validation.
