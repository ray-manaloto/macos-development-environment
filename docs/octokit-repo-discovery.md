# Octokit Repo Discovery

Octokit-based repository discovery for modern dotfiles/bootstrap projects.

## What It Does

- Searches GitHub repositories by topic tags.
- Scopes non-`dotfiles` topic searches to `topic:dotfiles` to keep results bootstrap-focused.
- Filters by `pushed` date with a default of last 60 days.
- Deduplicates repositories found across multiple tags.
- Merges matched tags per repository.
- Sorts deterministically by:
  1. `pushedAt` descending
  2. `stars` descending
  3. `fullName` ascending

## Default Tags

- `dotfiles`
- `zsh`
- `zshrc`
- `starship`
- `tmux-conf`
- `sheldon`
- `chezmoi`
- `mise`
- `powerlevel10k`
- `claude-code`
- `macos`
- `homebrew`
- `nix-darwin`
- `home-manager`
- `terminal`
- `shell`
- `tmux`
- `neovim`
- `wezterm`
- `ghostty`
- `aerospace`
- `karabiner-elements`

## Prerequisites

- Node.js 20+ or Bun-managed Node runtime.
- GitHub token with repository search access:
  - `GITHUB_TOKEN` environment variable, or
  - `--token` CLI flag.

If you use GitHub CLI auth, this works:

```bash
export GITHUB_TOKEN="$(gh auth token)"
```

## Usage

Default run (table output, 60-day window):

```bash
bun run octokit:discover
```

JSON output:

```bash
bun run octokit:discover -- --format json
```

Custom day window:

```bash
bun run octokit:discover -- --days 90
```

Custom tags:

```bash
bun run octokit:discover -- --tags dotfiles,chezmoi,mise,starship
```

Filter by minimum stars:

```bash
bun run octokit:discover -- --min-stars 20
```

Limit results requested per tag:

```bash
bun run octokit:discover -- --per-tag-limit 50
```

## Testing

Run the BDD-style suite:

```bash
bun run test:octokit-discovery
```

The tests validate:

- default tag coverage
- date cutoff behavior
- topic query construction
- dedupe/merge semantics
- ranking determinism
- discovery orchestration shape

## Notes

- If GitHub API rate limits are hit for some tags, the command continues and prints warnings per failed tag, returning partial results for successful tags.
