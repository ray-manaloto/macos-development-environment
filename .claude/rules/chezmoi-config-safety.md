# Chezmoi Config Safety

## sourceDir must survive chezmoi apply

The `.chezmoi.toml.tmpl` template generates `~/.config/chezmoi/chezmoi.toml` on every
`chezmoi apply`. Any field in `chezmoi.toml` that isn't in the template gets WIPED.

### Rules

- NEVER remove `sourceDir` from `.chezmoi.toml.tmpl` — it causes chezmoi to revert
  to the default `~/.local/share/chezmoi`, breaking all operations
- The template uses `{{ .chezmoi.sourceDir | dir }}` to output the repo root
  (parent of the effective source dir) so `.chezmoiroot` remains load-bearing
- `[data.git]` uses `promptStringOnce` — values are cached in chezmoi.toml after
  first prompt, preserved on subsequent applies
- After ANY edit to `.chezmoi.toml.tmpl`: verify with `chezmoi execute-template`
  that sourceDir and [data.git] are present in the output
- The validator (`chezmoi.sourcedir-default`) catches reversion to default sourceDir

### What went wrong (2026-03-29)

sourceDir was removed from the template to fix a "dead code" warning. Every subsequent
`chezmoi apply` wiped sourceDir from chezmoi.toml, breaking chezmoi. The fix was:
1. Add sourceDir back using `{{ .chezmoi.sourceDir | dir }}` (points to repo root)
2. Add `[data.git]` via `promptStringOnce` (cached after first prompt)
3. Add validator to catch reversion to default sourceDir
