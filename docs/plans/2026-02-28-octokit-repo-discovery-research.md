# Octokit Repo Discovery Research (R1)

## Scope
Research query strategy for finding modern dotfiles/bootstrap repositories using Octokit and GitHub Search API with recency filters.

## Findings

1. GitHub repository search supports required qualifiers for this use case:
- `topic:<tag>`
- `pushed:>=YYYY-MM-DD`
- `stars:>=N`
- `archived:false`

2. Topic search with broad tags (`homebrew`, `terminal`, `shell`) can return many non-dotfiles repositories.

3. Relevance improves significantly when non-`dotfiles` tags are scoped with `topic:dotfiles`.

4. API rate-limit exposure is real when querying many tags in one run.
- Mitigation: continue on per-tag failure and return partial results with warnings.

5. Deterministic ranking should not depend on API return order.
- Selected order: `pushedAt desc`, then `stars desc`, then `fullName asc`.

## Resulting Query Contract

- For `dotfiles` tag:
  - `topic:dotfiles pushed:>=<since> stars:>=<n> archived:false`

- For any non-dotfiles tag (example `mise`):
  - `topic:dotfiles topic:mise pushed:>=<since> stars:>=<n> archived:false`

## Defaults

- `days=60`
- Extended tag list includes: `dotfiles zsh zshrc starship tmux-conf sheldon chezmoi mise powerlevel10k claude-code macos homebrew nix-darwin home-manager terminal shell tmux neovim wezterm ghostty aerospace karabiner-elements`
- `minStars=0`
- `perTagLimit=30`
