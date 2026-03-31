# Centralized .generated/ Path Management

## Environment Variables

All MDE_* env vars are defined in the global mise config (`~/.config/mise/config.toml`),
managed via chezmoi template (`home/dot_config/mise/config.toml.tmpl`).

| Env Var | Composes From | Default | Purpose |
|---------|---------------|---------|---------|
| `MDE_PROJECT_DIR` | chezmoi template | `{{ .chezmoi.sourceDir \| dir }}` | Repository root |
| `MDE_GENERATED_DIR` | `$MDE_PROJECT_DIR` | `$MDE_PROJECT_DIR/.generated` | Runtime artifacts root |
| `MDE_DIR_REMEMBER` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/remember` | Remember plugin data |
| `MDE_DIR_LEARNINGS` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/learnings` | Agent discoveries |
| `MDE_DIR_TRANSCRIPTS` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/transcripts` | Agent transcripts |
| `MDE_DIR_SCHEMAS` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/schemas` | Schema cache |
| `MDE_DIR_REPORTS` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/reports` | Quality reports |
| `MDE_DIR_CONTEXT` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/context` | Context snapshots |
| `MDE_DIR_DREAM` | `$MDE_GENERATED_DIR` | `$MDE_GENERATED_DIR/dream` | Dream pipeline state |

## Python API

```python
from mde.lib.paths import get_paths
paths = get_paths()
paths.dir_remember     # Path to remember data
paths.generated_dir    # Path to .generated root
paths.project_dir      # Path to repo root
```

## Composition Rules

- Only `MDE_PROJECT_DIR` uses the chezmoi template `{{ .chezmoi.sourceDir | dir }}`
- All other vars compose from `$MDE_PROJECT_DIR` or `$MDE_GENERATED_DIR`
- mise `env_shell_expand = true` enables `$VAR` expansion at shell activation
- Adding a new subdirectory: (1) field in `MdePaths`, (2) entry in `_CHILD_DEFAULTS`, (3) env var in chezmoi template

## Validation

`uv run mde-py validate --paths` runs 9 checks. See `src/mde/validate/paths.py`.
