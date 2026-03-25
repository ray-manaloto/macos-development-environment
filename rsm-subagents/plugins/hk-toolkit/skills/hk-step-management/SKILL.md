---
name: hk-step-management
description: >
  Add, remove, or modify hook steps in hk.pkl. Use when adding new linters,
  removing deprecated steps, changing file globs, or reorganizing hook structure.
---

# hk Step Management

## Adding a Step

### Using a Builtin

```pkl
["ruff"] = (Builtins.ruff) {
    exclude = List("vendor/**", "generated/**")
}
```

Available builtins: `hk builtins` to list all. Common ones:
- `Builtins.ruff` / `Builtins.ruff_format`
- `Builtins.prettier`
- `Builtins.eslint`
- `Builtins.shellcheck`
- `Builtins.biome`

### Custom Command Step

```pkl
["my-linter"] {
    check = "my-tool check"          // Read-only check
    fix = "my-tool fix"              // Optional: auto-fix command
    glob = "*.py"                    // Optional: file filter
    exclude = List("tests/**")       // Optional: exclusions
    profiles = List("slow")          // Optional: profile gating
}
```

### Quality Gate Step (no file filtering)

```pkl
["mde-quality"] {
    check = "uv run mde-py quality"  // Runs on entire repo, not per-file
}
```

## Removing a Step

Delete the step entry from the `Mapping` block in hk.pkl, then run `hk validate`.

## Organizing Steps

### Separate fixers from validators

```pkl
local fixers = new Mapping<String, Step> {
    ["ruff"] = Builtins.ruff
    ["ruff_format"] = Builtins.ruff_format
}

local validators = new Mapping<String, Step> {
    ["quality"] { check = "uv run mde-py quality" }
}

hooks {
    ["pre-commit"] {
        fix = true
        stash = "git"
        steps = new Mapping { ...fixers ...validators }
    }
    ["fix"] {
        fix = true
        steps = fixers  // Only fixers, no validators
    }
}
```

### Profile-Gated Steps

```pkl
["slow-tests"] {
    check = "uv run pytest --slow"
    profiles = List("slow")  // Only with: hk run pre-commit --slow
}
```

## After Changes

1. `hk validate` — Check pkl syntax
2. `hk check` — Run all check steps
3. `hk run pre-commit --verbose` — Full hook test
