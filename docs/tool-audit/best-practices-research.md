# Best Practices Research: macOS Dev Environment Alternatives

Audited: 2026-02-28
Scope: Compare this repository's shell-script-driven approach against well-known macOS development environment tooling and patterns.

---

## 0. This Repo's Current Architecture (Baseline)

Before evaluating alternatives, here is a summary of the approach used by `macos-development-environment`:

| Aspect | Implementation |
|--------|---------------|
| **Config deployment** | `scripts/ensure-managed-configs.sh` copies templates via `cp`/`install` with a `MANAGED_MARKER` guard |
| **Update lifecycle** | `scripts/macos-dev-maintenance.sh` runs Homebrew, mise, bun, uv, pixi updates sequentially |
| **Health validation** | `scripts/health-check.sh` checks commands, files, launchd jobs, keychain secrets, and log health |
| **Verification** | `scripts/verify-all.sh` orchestrates sub-verifiers (health-check, tmux, tooling, dashboard) |
| **Drift detection** | `scripts/mde-drift-check.sh` validates brew/mise runtime ownership, PATH ordering, conflicting managers |
| **Scheduling** | macOS `launchd` (12-hour interval via `StartInterval`) |
| **Secrets** | macOS Keychain + env file + optional 1Password CLI |
| **Runtime precedence** | Documented in `docs/toolchain-precedence.md`: mise > bun > pixi > uv > Homebrew |
| **Templates** | 7 template files in `templates/` (oh-my-zsh, tmux.conf, zprofile, secrets.env.example) |
| **Shell scripts** | 48 scripts in `scripts/`, 2 test files in `scripts/tests/` |
| **Shared library** | `scripts/lib/mde-json.sh` (JSON output helpers) |
| **Package manifest** | None (no Brewfile, no mise.toml task definitions, no Ansible playbook) |

### Key Strengths of the Current Approach

1. **Low dependency**: Only requires bash/zsh and standard macOS utilities.
2. **Explicit control**: Every update step is visible in shell functions; easy to debug.
3. **Marker-based safety**: Templates skip unmanaged files via `MANAGED_MARKER` grep.
4. **Strong drift detection**: Dedicated script checks for brew/mise conflicts, PATH ordering, duplicate binaries, and conflicting managers.
5. **Keychain-native secrets**: Integrates with macOS Keychain (no external password manager required).
6. **launchd-native scheduling**: Uses macOS-native automation without cron or external schedulers.

### Key Gaps in the Current Approach

1. **No diff/preview before deploy**: `ensure-managed-configs.sh` does a blind `cp` with no preview of what changes.
2. **No package manifest**: Homebrew packages are not declared anywhere; there is no way to reproduce the full package set.
3. **No idempotency guarantees**: Scripts use guards but have no formal idempotency model.
4. **No multi-machine support**: Templates contain hardcoded paths (e.g., `/Users/rmanaloto`).
5. **No encrypted secrets in repo**: Secrets live entirely outside the repo (Keychain/env file), with no option to version-encrypt them.
6. **Template sync is one-way**: No mechanism to detect local edits that diverge from templates.
7. **Large script surface**: 48 scripts with duplicated helper functions (`log()`, `have_cmd()`, `setup_path()`) across multiple files.

---

## 1. chezmoi

**What it is**: A single-binary dotfiles manager written in Go, with templates, encryption, multi-machine support, and password manager integration.

**Repository**: https://github.com/twpayne/chezmoi
**Current version**: 2.69.4

### What chezmoi provides that this repo does not

| Feature | Detail |
|---------|--------|
| **Diff/preview before apply** | `chezmoi diff` shows exactly what will change before writing files. This repo's `ensure-managed-configs.sh` copies blindly. |
| **Template engine** | Go template syntax with conditionals on hostname, OS, username. This repo's templates have hardcoded paths like `$HOME/dev/github/ray-manaloto/`. |
| **Multi-machine support** | Single dotfiles repo works across machines with per-host template variables. This repo is single-machine only. |
| **Encryption at rest** | `chezmoi add --encrypt` encrypts files with built-in `age` support. This repo has no way to version-control secrets. |
| **Password manager integration** | Native support for 1Password, Bitwarden, Keychain, LastPass, and more. This repo has 1Password support but it is custom shell code. |
| **Two-way merge** | Detects local modifications and offers merge strategies. `ensure-managed-configs.sh` only checks for the `MANAGED_MARKER` string. |
| **Declarative desired state** | Source directory defines the desired state; `chezmoi apply` converges. This repo has no convergence model. |
| **Dry-run mode** | `chezmoi apply --dry-run` simulates changes without writing. No equivalent exists here. |
| **Script lifecycle hooks** | `run_once_`, `run_onchange_` scripts for bootstrapping and migration. This repo has no equivalent. |

### What this repo provides that chezmoi does not

| Feature | Detail |
|---------|--------|
| **Update lifecycle** | `macos-dev-maintenance.sh` handles Homebrew, mise, bun, uv, pixi updates. chezmoi only manages dotfiles, not package updates. |
| **Drift detection** | `mde-drift-check.sh` validates runtime ownership and PATH. chezmoi has no package/runtime drift model. |
| **Health checks** | `health-check.sh` validates launchd jobs, secrets, log health. chezmoi has no system health concept. |
| **launchd integration** | Native macOS scheduling for automated maintenance. chezmoi does not schedule anything. |
| **Wrapper scripts** | CLI wrappers (claude, gemini, fabric) with environment injection. Outside chezmoi's scope. |

### Migration effort: LOW-MEDIUM

- Template conversion is straightforward (add Go template conditionals).
- `ensure-managed-configs.sh` maps directly to `chezmoi apply`.
- The update lifecycle, drift detection, and health-check scripts would remain as-is; chezmoi would only replace the config deployment layer.
- Biggest effort: Converting hardcoded paths to template variables and establishing `chezmoi init` workflow.

### Key tradeoffs

- **Adopting chezmoi** eliminates the template-deploy sync gap (diff, preview, merge) and enables multi-machine support.
- **Cost**: Adds a binary dependency (though it is a single static binary with zero runtime deps).
- **Risk**: chezmoi and the custom scripts can coexist; migration can be incremental.
- **Recommendation**: Strongly consider for the config deployment layer. The diff/preview capability alone addresses the largest gap in the current approach.

---

## 2. nix-darwin + home-manager

**What it is**: Fully declarative macOS system configuration using the Nix package manager. nix-darwin manages system-level settings; home-manager manages user-level dotfiles and packages.

**Repository**: https://github.com/nix-darwin/nix-darwin
**home-manager**: https://github.com/nix-community/home-manager

### What nix-darwin provides that this repo does not

| Feature | Detail |
|---------|--------|
| **Fully declarative system state** | A single `.nix` file defines all packages, services, and configuration. This repo has no unified manifest. |
| **Atomic rollbacks** | Every generation is preserved; `darwin-rebuild switch --rollback` reverts the entire system. This repo has no rollback. |
| **Reproducibility** | Nix pins exact package versions via flakes. This repo gets "latest" from Homebrew. |
| **Garbage collection** | `nix-collect-garbage` removes unused packages. Homebrew cleanup is less thorough. |
| **Cross-platform** | home-manager works on Linux too. This repo is macOS-only. |
| **mise integration** | nix-darwin can call `mise use --global` in activation scripts for runtime management. |

### What this repo provides that nix-darwin does not

| Feature | Detail |
|---------|--------|
| **Zero learning curve** | Shell scripts require only bash/zsh knowledge. Nix has a notoriously steep learning curve. |
| **macOS Keychain integration** | Native `security` command usage for secrets. Nix has no Keychain concept. |
| **Incremental updates** | Homebrew updates individual packages. Nix rebuilds the entire generation (though it is fast due to caching). |
| **launchd integration** | Custom plist files. nix-darwin has its own launchd abstraction, but custom plists require additional work. |
| **Ecosystem familiarity** | Homebrew is the dominant macOS package manager; Nix is niche. |

### Migration effort: HIGH

- Requires learning the Nix language and flake ecosystem.
- All Homebrew packages must be re-expressed as Nix expressions or kept in a compatibility layer.
- Some macOS-specific tools (casks, App Store apps) require Homebrew anyway, leading to a hybrid approach.
- mise can coexist with nix-darwin, but the two have overlapping responsibilities for runtime management.
- Estimated time: 2-4 weeks for initial migration, ongoing maintenance learning curve.

### Key tradeoffs

- **Adopting nix-darwin** provides the strongest reproducibility guarantees of any option.
- **Cost**: Steep learning curve, niche ecosystem, potential for confusing error messages.
- **Risk**: Ecosystem lock-in; if you stop using Nix, there is no easy migration path out.
- **Recommendation**: Not recommended for this repo at this time. The learning curve and ecosystem lock-in outweigh the benefits for a single-machine personal environment. Revisit if multi-machine reproducibility becomes critical.

---

## 3. Ansible + Dotfiles

**What it is**: Playbook-driven infrastructure-as-code tool that can configure macOS environments. Commonly paired with a dotfiles repository.

**Notable example**: https://github.com/geerlingguy/mac-dev-playbook

### What Ansible provides that this repo does not

| Feature | Detail |
|---------|--------|
| **Declarative task model** | YAML playbooks define desired state; Ansible handles idempotency. This repo's scripts are imperative. |
| **Role-based modularity** | Roles (e.g., `dev-tools`, `terminal`, `neovim`) provide clean separation. This repo has 48 flat scripts. |
| **Tag-based selective runs** | `--tags homebrew,dotfiles` runs only selected roles. This repo has env-var toggles but no formal tagging. |
| **Built-in Homebrew module** | `community.general.homebrew` and `community.general.homebrew_cask` handle package management declaratively. |
| **Idempotency** | Ansible modules are designed to be idempotent by default. This repo's scripts have manual guards. |
| **Dry-run mode** | `--check` mode simulates changes. No equivalent in this repo. |
| **Fact gathering** | Ansible collects system facts (OS, hostname, architecture) automatically. This repo does not inspect system state. |

### What this repo provides that Ansible does not

| Feature | Detail |
|---------|--------|
| **No Python dependency** | This repo only needs bash/zsh. Ansible requires Python. |
| **Faster execution** | Shell scripts execute immediately. Ansible has startup overhead (1-3 seconds per playbook). |
| **launchd-native scheduling** | This repo uses macOS launchd. Ansible is typically run manually or via CI. |
| **Keychain integration** | Native `security` command. Ansible requires custom modules or `shell` tasks for Keychain. |
| **Runtime drift detection** | `mde-drift-check.sh` validates mise/brew ownership. Ansible has no built-in drift model for runtime managers. |

### Migration effort: MEDIUM

- `macos-dev-maintenance.sh` maps well to Ansible roles/tasks.
- Homebrew packages can be expressed in a playbook with the Homebrew module.
- Template deployment maps to Ansible's `template` module (Jinja2 templates).
- The 48 scripts would need to be audited and converted to tasks or kept as `shell` tasks.
- Python/pip dependency must be bootstrapped (though macOS ships with Python via Xcode CLI tools).

### Key tradeoffs

- **Adopting Ansible** provides a proven idempotency model and declarative task definitions.
- **Cost**: Adds Python dependency, YAML authoring overhead, and Ansible learning curve.
- **Risk**: Overkill for a single-machine environment. Ansible shines at multi-machine fleet management.
- **Recommendation**: Not a strong fit for this repo. The overhead of Python, YAML, and Ansible's multi-host model does not pay off for a single developer machine. The idempotency benefit is real but can be achieved more simply with chezmoi or Brewfile.

---

## 4. Brewfile (brew bundle)

**What it is**: Homebrew's built-in declarative package manifest. A `Brewfile` declares all formulae, casks, taps, and Mac App Store apps, and `brew bundle` installs/upgrades them.

**Documentation**: https://docs.brew.sh/Brew-Bundle-and-Brewfile

### What a Brewfile provides that this repo does not

| Feature | Detail |
|---------|--------|
| **Package manifest** | Single file declares all installed packages. This repo has NO record of what Homebrew packages should be installed. |
| **Reproducible installs** | `brew bundle install` on a fresh machine installs everything. This repo cannot reproduce the Homebrew state. |
| **Cleanup of unmanaged packages** | `brew bundle cleanup` removes formulae not in the Brewfile. This repo has no equivalent. |
| **Diff/audit** | `brew bundle check` reports what is missing. This repo has no package audit capability. |
| **Cask support** | Brewfile handles casks (GUI apps) declaratively. This repo upgrades casks but does not declare them. |
| **Mac App Store** | Brewfile supports `mas` entries for App Store apps. Not addressed by this repo. |
| **Descriptions** | `brew bundle dump --describe` adds comments explaining each package. |

### What this repo provides that a Brewfile does not

| Feature | Detail |
|---------|--------|
| **Runtime precedence enforcement** | `toolchain-precedence.md` and `mde-drift-check.sh` enforce mise > brew ordering. Brewfile has no concept of runtime precedence. |
| **Update orchestration** | `macos-dev-maintenance.sh` sequences updates across multiple package managers. Brewfile only covers Homebrew. |
| **Skip logic** | Cask skip logic for `osquery` and sudo-requiring casks. Brewfile has no conditional skip mechanism. |

### Migration effort: LOW

- Run `brew bundle dump --describe --global --force` to generate a Brewfile from current state.
- Commit the Brewfile to the repo.
- Optionally integrate `brew bundle install` into `macos-dev-maintenance.sh`.
- Total effort: 30 minutes to 2 hours.

### Key tradeoffs

- **Adopting a Brewfile** is the highest-value, lowest-effort improvement available.
- **Cost**: Essentially zero. Brewfile is a built-in Homebrew feature.
- **Risk**: None. Brewfile and the existing update scripts coexist perfectly.
- **Recommendation**: Strongly recommended. This is the single most impactful gap to close. Without a Brewfile, the Homebrew package state is undocumented and unreproducible.

---

## 5. mise Tasks

**What it is**: mise's built-in task runner that replaces Makefiles and shell scripts. Tasks are defined in `mise.toml` or as standalone scripts in a `.mise/tasks/` directory.

**Documentation**: https://mise.jdx.dev/tasks/

### What mise tasks provide that this repo does not

| Feature | Detail |
|---------|--------|
| **Unified task registry** | All tasks defined in `mise.toml` or `.mise/tasks/`. This repo has 48 scripts with no registry. |
| **Dependency graphs** | Tasks can declare `depends` on other tasks; mise runs them in correct order. This repo sequences manually. |
| **Parallel execution** | mise runs independent tasks in parallel by default. `macos-dev-maintenance.sh` runs sequentially. |
| **Last-modified checking** | mise skips tasks if inputs haven't changed. This repo always runs everything. |
| **Watch mode** | `mise watch` re-runs tasks on file changes. No equivalent in this repo. |
| **Cross-language support** | Tasks can use any shebang (bash, python, node, etc.). This repo is bash-only. |
| **Discoverability** | `mise tasks` lists all available tasks. This repo requires reading the README. |

### What this repo provides that mise tasks does not

| Feature | Detail |
|---------|--------|
| **launchd scheduling** | This repo uses macOS launchd for automated runs. mise tasks require manual invocation or external scheduling. |
| **Complex bash logic** | Scripts like `macos-dev-maintenance.sh` (535 lines) have extensive conditional logic, lock files, and error handling that would be awkward in mise.toml. |
| **Verification framework** | `verify-all.sh` with JSON output and severity levels is more than a simple task runner. |

### Migration effort: LOW-MEDIUM

- Simple scripts (health-check, drift-check, verify) map cleanly to mise tasks.
- Complex scripts (macos-dev-maintenance.sh) are better kept as standalone scripts referenced by mise.
- The `scripts/lib/mde-json.sh` shared library works naturally with mise file tasks.
- Can be adopted incrementally, starting with verification and status scripts.

### Key tradeoffs

- **Adopting mise tasks** reduces the 48-script sprawl by providing a discoverable task registry.
- **Cost**: Learning mise task syntax (minimal since this repo already uses mise heavily).
- **Risk**: mise tasks reached stable status in 2025, but the templating syntax is being deprecated. Stick to `run` commands with shell scripts.
- **Recommendation**: Good fit for discoverable task organization. Start by wrapping the verification and status scripts as mise tasks. Keep complex lifecycle scripts (maintenance, install) as standalone bash.

---

## 6. dotbot

**What it is**: A lightweight, zero-dependency dotfiles bootstrapper focused on symlinks and shell commands. Configuration is YAML-based.

**Repository**: https://github.com/anishathalye/dotbot

### What dotbot provides that this repo does not

| Feature | Detail |
|---------|--------|
| **Symlink management** | Creates/updates/validates symlinks declaratively. This repo copies files (breaks the link to the source). |
| **Declarative YAML config** | Single `install.conf.yaml` defines all mappings. `ensure-managed-configs.sh` uses hardcoded function calls. |
| **Broken symlink cleanup** | `clean` directive removes broken symlinks. No equivalent in this repo. |
| **One-command bootstrap** | `git clone && ./install` sets up everything. This repo requires reading the README. |
| **Plugin system** | Custom commands via Python plugins. |

### What this repo provides that dotbot does not

| Feature | Detail |
|---------|--------|
| **Update lifecycle** | dotbot is a bootstrapper, not an update manager. |
| **Health/drift checks** | dotbot has no system validation. |
| **Wrapper scripts** | dotbot manages dotfiles, not CLI wrappers. |
| **Secrets management** | dotbot has no encryption or secrets concept. |
| **Template variables** | dotbot does not support templates (unlike chezmoi). |

### Migration effort: LOW

- Replace `ensure-managed-configs.sh` with a `install.conf.yaml` file.
- Switch from `cp` to symlinks for managed config files.
- Keep all other scripts unchanged.
- Total effort: 1-2 hours.

### Key tradeoffs

- **Adopting dotbot** simplifies config deployment but adds no template/encryption features.
- **Cost**: Very low. dotbot is embedded as a git submodule.
- **Risk**: None. dotbot and existing scripts coexist.
- **Recommendation**: Consider only if chezmoi is deemed too heavy. dotbot is simpler but lacks the diff/preview, encryption, and multi-machine features that address this repo's real gaps. For a repo that already has `ensure-managed-configs.sh` with marker-based safety, dotbot's value-add is limited.

---

## 7. Popular Dotfiles Patterns

Analysis of patterns from well-known dotfiles repositories that this repo could adopt.

### 7a. Topical Organization (Zach Holman style)

**Pattern**: Group files by topic (e.g., `git/`, `ruby/`, `zsh/`) rather than by type (e.g., `templates/`, `scripts/`). Each topic directory contains its own aliases, env setup, and install script.

**Applicability**: This repo's `templates/oh-my-zsh/` and `scripts/` separation is functional but not topical. A topical layout would group all mise-related config + scripts + docs together.

**Recommendation**: Not recommended for this repo. The current layout is already well-organized and the overhead of reorganization outweighs the benefit for a single-maintainer project.

### 7b. macOS Defaults Script (Mathias Bynens style)

**Pattern**: A single `.macos` script that configures macOS system preferences via `defaults write` commands (Dock, Finder, keyboard, trackpad, etc.).

**Repository**: https://github.com/mathiasbynens/dotfiles/blob/main/.macos

**Applicability**: This repo does not manage macOS system preferences at all. Adding a `scripts/macos-defaults.sh` with preferred Dock/Finder/keyboard settings would make machine setup more complete.

**Recommendation**: Consider adding a `scripts/macos-defaults.sh` for system preferences. This is a one-time setup script (not a maintenance script) and should be clearly documented as such.

### 7c. Brewfile as Source of Truth (Dries Vints style)

**Pattern**: The Brewfile is the definitive list of installed software. Combined with `mackup` for application settings backup.

**Applicability**: Directly relevant. This repo's biggest gap is the absence of a package manifest. See Section 4 above.

### 7d. GNU Stow for Symlinks (xero style)

**Pattern**: Use GNU Stow to create a "symlink farm" from the dotfiles directory to the home directory. Each package is a directory in the stow directory.

**Applicability**: Stow would replace `ensure-managed-configs.sh` with a standard symlink approach. However, chezmoi provides strictly more features.

**Recommendation**: Not recommended. chezmoi supersedes Stow for this use case.

### 7e. Makefile as Task Runner

**Pattern**: Many dotfiles repos use a `Makefile` as the entry point (e.g., `make install`, `make update`, `make test`).

**Applicability**: A `Makefile` or `mise.toml` task file would provide discoverability for the 48 scripts. See Section 5 above.

### 7f. Helper Function Library (DRY)

**Pattern**: Shared helper functions (`log()`, `info()`, `fail()`, `have_cmd()`, `confirm()`) in a single sourced file, avoiding duplication across scripts.

**Applicability**: This repo has `scripts/lib/mde-json.sh` but still duplicates `log()`, `have_cmd()`, and `setup_path()` across at least 5 scripts: `macos-dev-maintenance.sh`, `health-check.sh`, `verify-all.sh`, `mde-drift-check.sh`, and `ensure-managed-configs.sh`. A shared `scripts/lib/mde-common.sh` would reduce this duplication.

**Recommendation**: Recommended. Extract shared functions into `scripts/lib/mde-common.sh` and source it. Low effort, immediate maintainability improvement.

---

## Summary Matrix

| Tool/Pattern | Provides (not in repo) | Repo provides (not in tool) | Migration effort | Recommendation |
|---|---|---|---|---|
| **chezmoi** | Diff/preview, templates, encryption, multi-machine, merge | Update lifecycle, drift detection, health checks, launchd | LOW-MEDIUM | **Strongly consider** for config deployment |
| **nix-darwin** | Full declarative state, atomic rollback, reproducibility | Low learning curve, Keychain, launchd, ecosystem familiarity | HIGH | Not recommended at this time |
| **Ansible** | Idempotency, roles, tags, dry-run, Homebrew module | No Python dep, faster exec, launchd, Keychain, drift | MEDIUM | Not recommended (overkill for single machine) |
| **Brewfile** | Package manifest, reproducible installs, cleanup, audit | Runtime precedence, multi-manager orchestration | **LOW** | **Strongly recommended** (highest ROI) |
| **mise tasks** | Task registry, dependencies, parallelism, discoverability | launchd scheduling, complex bash logic, verification | LOW-MEDIUM | Good fit for task organization |
| **dotbot** | Symlinks, YAML config, one-command bootstrap | Lifecycle, health, drift, secrets, templates | LOW | Consider only if chezmoi is too heavy |
| **Common patterns** | macOS defaults, DRY helpers, topical org | Existing structure is functional | LOW | Extract shared helpers; consider macOS defaults |

---

## Prioritized Recommendations

### Tier 1 - High value, low effort (do now)

1. **Add a Brewfile**: Run `brew bundle dump --describe --global --force`, commit the result, add `brew bundle check` to `health-check.sh`. Effort: <1 hour.
2. **Extract `scripts/lib/mde-common.sh`**: Move duplicated `log()`, `have_cmd()`, `setup_path()` into a shared library. Effort: 1-2 hours.

### Tier 2 - High value, moderate effort (plan next)

3. **Adopt chezmoi for config deployment**: Replace `ensure-managed-configs.sh` with `chezmoi apply`. Gains: diff/preview, template variables (remove hardcoded `/Users/rmanaloto`), encryption for secrets. Effort: 1-2 days.
4. **Wrap key scripts as mise tasks**: Add `mise.toml` `[tasks]` section for health-check, drift-check, verify-all, status-dashboard. Gains: discoverability (`mise tasks`), dependency ordering. Effort: half a day.

### Tier 3 - Nice to have (backlog)

5. **Add `scripts/macos-defaults.sh`**: Document and automate macOS system preferences. Effort: 2-4 hours.
6. **Evaluate dotbot as chezmoi fallback**: If chezmoi is too complex for the config deployment layer, dotbot is a simpler alternative. Effort: 1-2 hours.
7. **Re-evaluate nix-darwin**: If multi-machine reproducibility becomes a requirement, revisit nix-darwin + home-manager. Effort: 2-4 weeks.

---

## Sources

- [chezmoi official site](https://www.chezmoi.io/)
- [Why use chezmoi?](https://www.chezmoi.io/why-use-chezmoi/)
- [chezmoi GitHub](https://github.com/twpayne/chezmoi)
- [Dotfiles Secrets in Chezmoi](https://www.mikekasberg.com/blog/2026/01/31/dotfiles-secrets-in-chezmoi.html)
- [chezmoi and mise personal toolset](https://manuelchichi.com.ar/blog/personal-toolset-2025/)
- [nix-darwin GitHub](https://github.com/nix-darwin/nix-darwin)
- [Declarative macOS with nix-darwin](https://carlosvaz.com/posts/declarative-macos-management-with-nix-darwin-and-home-manager/)
- [Nix macOS Starter with Mise](https://www.bengubler.com/posts/2025-07-08-nix-macos-starter-mise)
- [home-manager](https://nix-community.github.io/home-manager/)
- [Ansible dotfiles introduction](https://phelipetls.github.io/posts/introduction-to-ansible/)
- [Ansible macOS dotfiles](https://github.com/frdmn/dotfiles)
- [Mastering macOS Dev Environment 2025](https://nerdleveltech.com/mastering-the-macos-development-environment-in-2025)
- [Homebrew Bundle documentation](https://docs.brew.sh/Brew-Bundle-and-Brewfile)
- [Declarative Brewfile management](https://matthiasportzel.com/brewfile/)
- [Brew Bundle tips](https://gist.github.com/ChristopherA/a579274536aab36ea9966f301ff14f3f)
- [mise tasks documentation](https://mise.jdx.dev/tasks/)
- [mise GitHub](https://github.com/jdx/mise)
- [dotbot GitHub](https://github.com/anishathalye/dotbot)
- [Dotfiles Management with Dotbot and Chezmoi](https://myhomelab.gr/automation/2025/06/26/dotfiles-management.html)
- [mathiasbynens/dotfiles](https://github.com/mathiasbynens/dotfiles)
- [awesome-dotfiles](https://github.com/webpro/awesome-dotfiles)
- [dotfiles.github.io](https://dotfiles.github.io/utilities/)
