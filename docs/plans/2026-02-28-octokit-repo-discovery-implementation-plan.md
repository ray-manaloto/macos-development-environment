# Octokit Repository Discovery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an Octokit-based CLI that discovers modern dotfiles/bootstrap repositories by topics and filters by last N days (default 60), with extended default tags and deterministic output.

**Architecture:** Implement a small Node ESM module that encapsulates query construction, Octokit search orchestration, result normalization, deduplication, and ranking. Expose a CLI entrypoint for local use and CI automation, plus BDD-style unit tests with mocked search responses.

**Tech Stack:** Node.js ESM, `@octokit/rest`, built-in `node:test` + `node:assert/strict`.

---

## Multi-Agent SDLC Breakdown

### Research Subagent (R1)
- Confirm GitHub Search query constraints and qualifier behavior (`topic:`, `pushed:>=`, `archived:false`).
- Define practical ranking and dedupe strategy for multi-tag searches.
- Output: query and ranking contract used by implementation/tests.

### Spec/Plan Subagent (S1)
- Convert requirements into explicit CLI contract and module API.
- Define defaults: `days=60`, expanded tag list, `minStars=0`, `perTagLimit=30`.
- Output: this document + acceptance criteria.

### Test Subagent (T1)
- Implement BDD-style tests for:
  - date cutoff construction
  - query builder correctness
  - dedupe + matched-tag merge behavior
  - deterministic ranking and output shape
- Output: executable tests that fail before implementation and pass after.

### Implementation Subagent (I1)
- Implement Octokit search module and CLI wrapper.
- Add package script entrypoints.
- Output: production-ready script with clear error handling.

### Review Subagent (C1)
- Run focused code review for correctness, regressions, and edge cases.
- Verify no accidental secret leakage in logs/output.
- Output: findings + fixes.

### Documentation Subagent (D1)
- Write usage docs with examples for:
  - default run
  - custom day windows
  - custom tags
  - JSON output for piping.
- Output: concise operator documentation.

---

## Acceptance Criteria

1. CLI command supports filtering by last N days and defaults to 60.
2. Default tags include original tags plus:
   - `macos`, `homebrew`, `nix-darwin`, `home-manager`, `terminal`, `shell`, `tmux`, `neovim`, `wezterm`, `ghostty`, `aerospace`, `karabiner-elements`.
3. Results are deduplicated by repository full name and include merged matched tags.
4. Output is deterministic and sorted by:
   - `pushedAt` desc, then `stars` desc, then `fullName` asc.
5. BDD tests pass locally with `node --test`.
6. Documentation includes setup, auth, and sample commands.

---

## Task Plan

### Task 1: Add BDD Test Suite

**Files:**
- Create: `tests/octokit-repo-discovery.bdd.test.mjs`

**Step 1: Write failing tests**
- Add BDD test names using `Given/When/Then` for core behaviors.

**Step 2: Run tests to verify failure**
- Run: `node --test tests/octokit-repo-discovery.bdd.test.mjs`
- Expected: module import/function-not-found failures.

### Task 2: Implement Octokit Discovery Module

**Files:**
- Create: `scripts/octokit/repo-discovery.mjs`

**Step 1: Implement minimal module to satisfy tests**
- Export default tags and pure functions:
  - `buildSinceDate(days, now)`
  - `buildTopicQuery(tag, since, minStars)`
  - `mergeAndRankRepositories(results)`
  - `discoverRepositories({octokit, tags, days, minStars, perTagLimit})`

**Step 2: Run tests**
- Run: `node --test tests/octokit-repo-discovery.bdd.test.mjs`
- Expected: green for pure-function and orchestration cases.

### Task 3: Implement CLI Wrapper

**Files:**
- Create: `scripts/octokit/find-bootstrap-repos.mjs`

**Step 1: Add argument parsing + env token handling**
- Flags: `--days`, `--tags`, `--min-stars`, `--per-tag-limit`, `--format`.

**Step 2: Wire module and print output**
- Formats: `json` and `table`.

**Step 3: Manual smoke run (requires token)**
- Run: `GITHUB_TOKEN=$(gh auth token) node scripts/octokit/find-bootstrap-repos.mjs --days 60 --format table`

### Task 4: Wire Scripts + Docs

**Files:**
- Modify: `package.json`
- Create: `docs/octokit-repo-discovery.md`

**Step 1: Add package scripts**
- `octokit:discover`
- `test:octokit-discovery`

**Step 2: Document usage**
- Include prerequisites, defaults, examples.

### Task 5: Review + Verification

**Files:**
- Modify as needed based on findings.

**Step 1: Run verification commands**
- `node --test tests/octokit-repo-discovery.bdd.test.mjs`
- `GITHUB_TOKEN=$(gh auth token) node scripts/octokit/find-bootstrap-repos.mjs --days 60 --format json`

**Step 2: Review for correctness**
- Check edge cases: empty results, duplicate repos across tags, invalid day values.

