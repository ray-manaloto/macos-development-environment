# SDK and MCP Tooling Decision

- Decision: SDK and MCP CLIs stay `mise`-owned and inherit the backend-native policy of their ecosystem instead of bespoke installer scripts.
- Cache policy: Node-based tools reuse bun/npm backend caches; Python-based tools reuse pipx or uv-related caches depending on the declared backend.
- Validation: prefer backend-native validation commands and the modernization matrix over script-local assumptions.
- Sources:
  - <https://mise.jdx.dev/>
  - <https://mise.jdx.dev/dev-tools/backends.html>
