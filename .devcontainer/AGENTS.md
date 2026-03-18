## Devcontainer Execution Policy

- Use `mise`-managed tooling for devcontainer operations.
- Preferred invocations:
  - `mise x devcontainer -- devcontainer <subcommand>`
  - `devcontainer <subcommand>` only when it resolves from `mise` toolchain.
- Before reporting readiness, run:
  - `bash scripts/tests/devcontainer-bootstrap-contract.test.sh`
  - `mise run mde:devcontainer:image:build`
  - `mise run mde:devcontainer:image:smoke`
  - `mise run mde:devcontainer:lifecycle:smoke`
