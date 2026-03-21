# Chezmoi Ignore Files (.chezmoiignore/.chezmoiignore.tmpl)

## Purpose

`.chezmoiignore{,.tmpl}` lets you keep files in the source state but exclude them from the target state. This is the primary way to avoid deploying certain files or directories to specific machines.

## Key Rules

- Patterns are matched against the **target path** (destination), not the source path.
- Matching uses `doublestar.Match` semantics.
- Lines prefixed with `!` are **exclusions** (negations). All excludes take priority over all includes.
- Comments start with `#` and run to end-of-line. A `#` after the beginning of the line is treated as a comment only if it is preceded by whitespace.
- `.chezmoiignore` is interpreted as a Go template **whether or not** it has a `.tmpl` extension.
- `.chezmoiignore` files placed in subdirectories only apply to that subdirectory.

## Template Usage

Because `.chezmoiignore` is always template-aware, you can ignore files based on machine data:

```text
{{- if ne .chezmoi.hostname "work-laptop" }}
.work
{{- end }}

{{- if eq .chezmoi.os "windows" }}
Documents/*
!Documents/*PowerShell/
{{- end }}
```

Tip: logic usually reads as "ignore unless" because chezmoi installs by default.

## Common Patterns

```text
README.md
*.txt
*/.cache/**
backups/   # ignore the directory entry
backups/** # ignore everything inside
```

## Debugging

Use `chezmoi ignored` to see what is currently ignored.

If in doubt about syntax or edge cases, consult the official chezmoi documentation for `.chezmoiignore{,.tmpl}` and `chezmoi ignored`.
