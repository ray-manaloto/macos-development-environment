#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
POST_CREATE="$ROOT_DIR/.devcontainer/post-create.sh"
DEVCONTAINER_JSON="$ROOT_DIR/.devcontainer/devcontainer.json"
DEVCONTAINER_MISE="$ROOT_DIR/.devcontainer/mise.toml"
DOCKERFILE="$ROOT_DIR/.devcontainer/Dockerfile"
IMAGE_SMOKE="$ROOT_DIR/scripts/devcontainer-image-smoke.sh"
CONTAINER_CLEANUP="$ROOT_DIR/scripts/devcontainer-cleanup.sh"
LIFECYCLE_SMOKE="$ROOT_DIR/scripts/devcontainer-lifecycle-smoke.sh"
WORKFLOW_FILE="$ROOT_DIR/.github/workflows/devcontainer-image.yml"
DRIFT_SCRIPT="$ROOT_DIR/scripts/mde-drift-check.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

if grep -q 'export MDE_PLATFORM=devcontainer' "$POST_CREATE"; then
  pass "post-create sets MDE_PLATFORM=devcontainer"
else
  fail "post-create missing MDE_PLATFORM export"
fi

if [[ "$(jq -r '.image' "$DEVCONTAINER_JSON")" == '${localEnv:MDE_DEVCONTAINER_IMAGE:ghcr.io/ray-manaloto/macos-development-environment/devcontainer:main}' ]]; then
  pass "devcontainer consumes published GHCR image with local override support"
else
  fail "devcontainer image contract changed unexpectedly"
fi

if jq -e '.build' "$DEVCONTAINER_JSON" >/dev/null 2>&1; then
  fail "devcontainer should not retain build stanza once GHCR image is source of truth"
else
  pass "devcontainer no longer uses local build stanza"
fi

if [[ "$(jq -r '.remoteUser' "$DEVCONTAINER_JSON")" == "vscode" ]]; then
  pass "devcontainer remoteUser contract preserved"
else
  fail "devcontainer remoteUser changed unexpectedly"
fi

if [[ "$(jq -r '.containerEnv.MDE_PLATFORM' "$DEVCONTAINER_JSON")" == "devcontainer" ]] && [[ "$(jq -r '.containerEnv.MDE_ENV_AUTOLOAD' "$DEVCONTAINER_JSON")" == "0" ]] && [[ "$(jq -r '.containerEnv.MDE_AUTOLOAD_SECRETS' "$DEVCONTAINER_JSON")" == "0" ]]; then
  pass "devcontainer environment contract preserved"
else
  fail "devcontainer environment contract changed unexpectedly"
fi

if [[ "$(jq -r '.postCreateCommand' "$DEVCONTAINER_JSON")" == 'bash ${containerWorkspaceFolder}/.devcontainer/post-create.sh' ]]; then
  pass "devcontainer postCreateCommand contract preserved"
else
  fail "devcontainer postCreateCommand changed unexpectedly"
fi

if grep -Fq 'mise trust -y "$REPO_ROOT/.mise.toml"' "$POST_CREATE" && grep -Fq 'mise trust -y "$DEVCONTAINER_MISE_CONFIG"' "$POST_CREATE"; then
  pass "post-create trusts the repo and devcontainer mise configs explicitly"
else
  fail "post-create missing explicit mise trust steps"
fi

if grep -q '^export MDE_ENV_AUTOLOAD=0' "$POST_CREATE" && grep -q '^export MDE_AUTOLOAD_SECRETS=0' "$POST_CREATE"; then
  pass "post-create disables env and secret autoload in devcontainer"
else
  fail "post-create missing devcontainer autoload guardrails"
fi

if ! grep -q 'https://mise.run' "$POST_CREATE"; then
  pass "post-create no longer performs network mise bootstrap"
else
  fail "post-create still bootstraps mise from the network"
fi

if ! grep -q 'ohmyzsh/ohmyzsh' "$POST_CREATE"; then
  pass "post-create no longer installs oh-my-zsh from the network"
else
  fail "post-create still installs oh-my-zsh from the network"
fi

if grep -q 'curl -fsSL https://mise.run | sh' "$DOCKERFILE"; then
  pass "dockerfile bakes mise into the published devcontainer image"
else
  fail "dockerfile missing baked mise bootstrap"
fi

if ! grep -Eq 'mise settings set|mise tool-alias set|mise use -g --yes' "$DOCKERFILE"; then
  pass "dockerfile no longer mutates imperative mise config during image build"
else
  fail "dockerfile still mutates imperative mise config during image build"
fi

if grep -q '\.oh-my-zsh/custom' "$DOCKERFILE"; then
  pass "dockerfile prepares the managed oh-my-zsh surface"
else
  fail "dockerfile missing managed oh-my-zsh surface preparation"
fi

if ! grep -Eq 'curl -fsSL https://mise\.run|raw\.githubusercontent\.com/ohmyzsh' "$POST_CREATE"; then
  pass "post-create no longer bootstraps toolchains with curl installers"
else
  fail "post-create still contains curl-based installer flows"
fi

if ! grep -Eq 'install_oh_my_zsh_if_missing|mise use -g --yes chezmoi@latest|mise use -g --yes starship@latest' "$POST_CREATE"; then
  pass "post-create no longer owns shell/framework installation concerns"
else
  fail "post-create still owns shell/bootstrap installation concerns"
fi

if grep -Fq 'install -m 0644 "$DEVCONTAINER_MISE_CONFIG" "$GLOBAL_MISE_CONFIG"' "$POST_CREATE" && grep -Fq 'install -m 0644 "$DEVCONTAINER_MISE_LOCK" "$GLOBAL_MISE_LOCK"' "$POST_CREATE"; then
  pass "post-create syncs repo-owned devcontainer mise config into container home"
else
  fail "post-create missing repo-owned devcontainer mise sync"
fi

if grep -Fq 'bootstrap_manifest_hash' "$POST_CREATE" && grep -Fq 'BOOTSTRAP_HASH_FILE=' "$POST_CREATE"; then
  pass "post-create uses hash-gated bootstrap state"
else
  fail "post-create missing hash-gated bootstrap state"
fi

if grep -Fq 'mise install --locked' "$POST_CREATE"; then
  pass "post-create installs declared tooling explicitly via locked mise manifest"
else
  fail "post-create missing locked mise install step"
fi

if grep -q 'scripts/ensure-managed-configs.sh' "$POST_CREATE"; then
  pass "post-create syncs declarative managed configs after bootstrap install"
else
  fail "post-create missing declarative config sync"
fi

if grep -Fq 'mise run mde:verify' "$POST_CREATE" && grep -Fq 'mise run mde:drift' "$POST_CREATE" && grep -Fq 'mise run mde:status' "$POST_CREATE"; then
  pass "post-create runs verify, drift, and status checks"
else
  fail "post-create missing verify/drift/status checks"
fi

if [[ -f "$DEVCONTAINER_MISE" ]] && grep -Eq '^chezmoi = |^python = |^bun = |^uv = |^pixi = ' "$DEVCONTAINER_MISE"; then
  pass "devcontainer mise manifest pins required bootstrap tools"
else
  fail "devcontainer mise manifest missing required pinned tools"
fi

if ! grep -Fq 'bash .devcontainer/post-create.sh' "$IMAGE_SMOKE" && ! grep -Fq 'mise run mde:verify' "$IMAGE_SMOKE"; then
  pass "raw image smoke stays limited to baked image sanity"
else
  fail "raw image smoke still executes lifecycle verification"
fi

if [[ -f "$CONTAINER_CLEANUP" ]] && grep -Fq 'label=mde.devcontainer.smoke' "$CONTAINER_CLEANUP" && grep -Fq 'label=mde.devcontainer.repo=' "$CONTAINER_CLEANUP"; then
  pass "devcontainer cleanup script targets stale script-managed containers for this repo"
else
  fail "devcontainer cleanup script missing targeted stale-container filters"
fi

if [[ -f "$LIFECYCLE_SMOKE" ]] && grep -Fq 'devcontainer up' "$LIFECYCLE_SMOKE" && grep -Fq 'devcontainer exec' "$LIFECYCLE_SMOKE"; then
  pass "lifecycle smoke uses real devcontainer up/exec flow"
else
  fail "lifecycle smoke missing real devcontainer up/exec flow"
fi

if grep -Fq 'scripts/devcontainer-cleanup.sh' "$LIFECYCLE_SMOKE" && grep -Fq 'mde.devcontainer.repo=' "$LIFECYCLE_SMOKE" && grep -Fq 'mde.devcontainer.workspace=' "$LIFECYCLE_SMOKE"; then
  pass "lifecycle smoke drains stale containers before launch and labels new ones for cleanup"
else
  fail "lifecycle smoke missing stale-container cleanup and stable repo/workspace labels"
fi

if grep -Fq 'scripts/devcontainer-cleanup.sh' "$ROOT_DIR/scripts/devcontainer-image-build.sh"; then
  pass "image build drains stale script-managed containers before rebuilding"
else
  fail "image build missing stale-container cleanup"
fi

if [[ -f "$WORKFLOW_FILE" ]] && grep -Fq 'platform_slug: linux-arm64' "$WORKFLOW_FILE" && grep -Fq 'MDE_DEVCONTAINER_RUN_PLATFORM: ${{ matrix.platform }}' "$WORKFLOW_FILE"; then
  pass "CI smoke workflow covers arm64 image validation explicitly"
else
  fail "CI smoke workflow missing explicit arm64 image validation"
fi

if grep -Fq 'devcontainer_manifest_entries' "$DRIFT_SCRIPT" && grep -Fq "required mise-managed command '\$display_command'" "$DRIFT_SCRIPT"; then
  pass "drift check derives devcontainer requirements from the bootstrap manifest"
else
  fail "drift check is not sourcing devcontainer requirements from the bootstrap manifest"
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
