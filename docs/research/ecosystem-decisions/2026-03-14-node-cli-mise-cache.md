# Node CLI Backend and Cache Decision

- Decision: global Node CLIs remain `mise`-owned through the npm backend, with bun configured as the npm package manager backend.
- Cache policy: reuse bun's package cache rooted under `BUN_INSTALL`; warm via `mise install` rather than `bun add -g` loops.
- Validation: prefer Node-native and bun-native validation commands.
- Sources:
  - <https://mise.jdx.dev/lang/node.html>
  - <https://mise.jdx.dev/configuration/settings.html#npm-package-manager>
  - <https://bun.sh/docs/install/cache>
