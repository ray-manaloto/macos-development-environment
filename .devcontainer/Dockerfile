FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04@sha256:d94c97dd9cacf183d0a6fd12a8e87b526e9e928307674ae9c94139139c0c6eae

LABEL org.opencontainers.image.title="macos-development-environment devcontainer" \
      org.opencontainers.image.description="Published devcontainer image for the macos-development-environment repository." \
      org.opencontainers.image.source="https://github.com/ray-manaloto/macos-development-environment"

ENV PATH="/home/vscode/.local/share/mise/shims:/home/vscode/.local/share/mise/bin:/home/vscode/.local/bin:${PATH}"

RUN apt-get update \
  && apt-get install -y --no-install-recommends zsh ca-certificates curl git jq ripgrep unzip \
  && rm -rf /var/lib/apt/lists/*

RUN su vscode -lc 'curl -fsSL https://mise.run | sh' \
  && su vscode -lc 'mkdir -p "$HOME/.oh-my-zsh/custom" "$HOME/.oh-my-zsh/custom/completions"'
