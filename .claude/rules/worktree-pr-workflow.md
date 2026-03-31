# Worktree PR Workflow Policy

- NEVER merge a feature branch to main for verification purposes
- Run all verification (pytest, ruff, ty, validate) on the feature branch
- The `/finishing-a-development-branch` skill MUST be the only path to merge or PR
- If you need to verify outside a worktree: `git checkout feat/branch` in the main repo, do NOT `git merge`
- The WorktreeCreate hook automatically unsets VIRTUAL_ENV and runs uv sync, eliminating the venv mismatch

## Automatic Worktree Setup (WorktreeCreate hook)

When Claude Code creates worktrees (via `--worktree` or `isolation: "worktree"`),
the `worktree_create` hook automatically:
1. Creates the git worktree branching from HEAD
2. Runs `mise trust` on the worktree path
3. Runs `uv sync --frozen` with VIRTUAL_ENV unset
4. Recreates the `.remember` symlink
5. Copies `.worktreeinclude` files

This replaces Claude Code's default behavior. To disable: remove the
`WorktreeCreate` entry from `.claude/settings.json`.
