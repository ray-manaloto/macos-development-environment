# docker/docker-bake.hcl
#
# Centralized build definitions for mde Docker images.
# Compose files handle runtime (up/down/networking/volumes) and pin pre-built images.
# Bake handles builds (multi-platform, attestations, build args).
#
# CURRENT STATE: All mde Docker services use pre-built upstream images pinned
# by digest in their respective compose.yaml files. No custom builds are needed
# yet, so this file serves as the foundation for future custom builds.
#
# DESIGN DECISION: Bake is a BUILD tool, not a pull tool. Pre-built images
# are pinned by digest in Compose files only. Bake targets are added here
# only when we need to build custom images (e.g., layering config on top of
# an upstream image via a Dockerfile).
#
# FUTURE: To add a custom build for Honcho, create docker/memory/Dockerfile.honcho,
# uncomment the targets below, and update compose.yaml to reference
# `image: mde/honcho-api:latest` instead of the upstream image.
#
# Usage (once targets are enabled):
#   docker buildx bake -f docker/docker-bake.hcl              # build all
#   docker buildx bake -f docker/docker-bake.hcl honcho-api    # build single target
#
# Pre-built images (pinned in Compose, documented here for reference):
#   observability/compose.yaml:
#     otel/opentelemetry-collector-contrib:0.107.0@sha256:b6552779...
#     grafana/tempo:2.6.1@sha256:ef4384fc...
#     grafana/loki:2.9.10@sha256:35b02acc...
#     grafana/grafana:11.4.0@sha256:d8ea3779...
#   memory/compose.yaml:
#     ghcr.io/plastic-labs/honcho:v3.0.3@sha256:0d23755c...
#     pgvector/pgvector:pg15-trixie@sha256:73baaa70...
#     redis:8.2@sha256:9e38e6ea...

# --- Shared base target ---
# All buildable targets inherit from _common for consistent metadata.
# Underscore prefix means Bake won't build it directly.
target "_common" {
  annotations = ["org.opencontainers.image.source=https://github.com/ray-manaloto/macos-development-environment"]
  attest = [
    "type=provenance,mode=max",
    "type=sbom"
  ]
}

# --- Groups ---
# `docker buildx bake` with no args builds "default".
# Currently empty — no custom builds needed. Add targets here when
# a custom Dockerfile is created.
group "default" {
  targets = []
}

# --- Reserved Memory targets (disabled — using upstream images) ---
# Uncomment when docker/memory/Dockerfile.honcho exists.
#
# target "honcho-api" {
#   inherits   = ["_common"]
#   context    = "memory"
#   dockerfile = "Dockerfile.honcho"
#   tags       = ["mde/honcho-api:latest"]
#   args = {
#     HONCHO_VERSION = "v3.0.3"
#   }
# }
#
# target "honcho-deriver" {
#   inherits   = ["_common"]
#   context    = "memory"
#   dockerfile = "Dockerfile.honcho"
#   tags       = ["mde/honcho-deriver:latest"]
#   args = {
#     HONCHO_VERSION = "v3.0.3"
#   }
# }
