---
name: hk-config
description: >
  This skill should be used when the user asks to edit or manage hk.pkl configuration files, such as adding stash settings,
  changing hook modes, configuring profiles, or modifying any hk configuration.
  Also use when user asks about hk settings or pkl syntax.
---

# hk Configuration Management

## pkl File Structure

hk uses Apple's Pkl language for configuration. The project config lives at `hk.pkl` in the repo root.

### Template

```pkl
amends "package://github.com/jdx/hk/releases/download/v<VERSION>/hk@<VERSION>#/Config.pkl"
import "package://github.com/jdx/hk/releases/download/v<VERSION>/hk@<VERSION>#/Builtins.pkl"

// Step definitions
local steps = new Mapping<String, Step> {
    ["step-name"] = Builtins.<builtin>
}

// Hook registration
hooks {
    ["pre-commit"] {
        fix = true
        stash = "git"
        steps = steps
    }
}
```

## Configuration Commands

- `hk config dump --json` — Show effective runtime settings
- `hk config explain <key>` — Show where a setting comes from
- `hk config get <key>` — Get a specific value
- `hk config sources` — Show precedence order
- `hk validate` — Validate pkl syntax

## Stash Configuration

Set via git config (not pkl):

```bash
# Disable stashing untracked files (fixes new-file stash restore bug)
git config --local hk.stashUntracked false

# Or via environment
export HK_STASH_UNTRACKED=false
```

## Profiles

Profiles allow conditional step execution:

```pkl
["slow-test"] {
    check = "uv run pytest --slow"
    profiles = List("slow")  // Only runs with --slow or --profile slow
}
```

## After Every Edit

1. Run `hk validate` to check syntax
2. Run `hk check` to verify steps pass
3. Run `hk run pre-commit --verbose` to test full hook
