# Lifecycle Execution Guarantees

## Timing and Blocking

- No explicit timeout mechanism in the spec
- Long-running commands can block container readiness
- The `waitFor` property controls what blocks container startup
- Background processes (`&`, `nohup`) can be used but must be managed carefully

## Prebuild Optimization

Prebuilds execute lifecycle commands during image build, caching the results:
- `onCreateCommand` and `updateContentCommand` are prebuild-safe
- `postCreateCommand` runs after prebuild completes
- Use `waitFor: "updateContentCommand"` to define the prebuild cutoff

## Container Restart Behavior

On container restart (stop then start):
- Creation commands (onCreate, updateContent, postCreate) do NOT re-run
- Only `postStartCommand` re-runs
- `postAttachCommand` re-runs when editor re-attaches

This makes `postStartCommand` ideal for:
- Starting dev servers that don't persist across stops
- Restarting sidecar compose services
- Re-establishing background processes

## Parallel Execution Guarantees

When using object syntax for parallel commands:
- All named commands start simultaneously
- No ordering guarantee between commands
- Each command gets its own process
- Exit codes are tracked independently
- A failing named command does not kill siblings
- The overall event succeeds only if ALL named commands succeed
