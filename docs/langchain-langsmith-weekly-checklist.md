# LangChain + LangSmith Weekly Checklist

Use this checklist for weekly reviews and maintenance of the LangChain/LangSmith
CLI toolchain.

## Weekly
- [ ] Run `scripts/install-langchain-cli-tools.sh` to pick up upstream updates.
- [ ] Run `scripts/verify-langchain-tools.sh` and confirm PASS.
- [ ] Export a small trace sample for regression tracking:
  - [ ] `langsmith-fetch traces ./out/weekly/traces --limit 10 --format raw`
- [ ] Export a small thread sample for UX drift tracking:
  - [ ] `langsmith-fetch threads ./out/weekly/threads --limit 10 --format raw`
- [ ] Check for new conflicts on `PATH` (e.g., `langchain`, `deepagents`).
- [ ] Review the latest multi-agent runs if configured (`scripts/run-multi-agent.sh`).

## Auth And Access
- [ ] Confirm `LANGSMITH_API_KEY` is still valid (pass in verification output).
- [ ] If using service keys, ensure `LANGSMITH_WORKSPACE_ID` is set.

## Cleanup
- [ ] Archive or rotate old exports under `./out/`.
- [ ] Remove any accidental secrets from exported JSON or logs.

## Notes
- Record issues in `docs/decision-log.md`.
- Update `docs/quality-playbook.md` if new checks are added.
