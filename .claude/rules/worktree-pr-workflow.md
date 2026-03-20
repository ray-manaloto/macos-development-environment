# Worktree PR Workflow Policy

- NEVER merge a feature branch to main for verification purposes
- Run all verification (pytest, ruff, ty, validate) on the feature branch
- The `/finishing-a-development-branch` skill MUST be the only path to merge or PR
- If you need to verify outside a worktree: `git checkout feat/branch` in the main repo, do NOT `git merge`
- The worktree's `VIRTUAL_ENV` warning is benign — uv uses the correct project venv regardless
