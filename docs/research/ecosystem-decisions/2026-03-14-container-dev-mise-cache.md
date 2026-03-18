# Container and Dev Tooling Decision

- Decision: container and dev tooling remain `mise`-first where possible, with shell acting only as orchestration around declared image or builder config.
- Cache policy: preserve OCI builder caches and devcontainer layer caches; do not default to cold image rebuilds.
- Validation: prefer native container tooling checks plus the repo's `mde:devcontainer:*` tasks.
- Sources:
  - <https://containers.dev/implementors/json_reference/>
  - <https://docs.docker.com/build/cache/>
