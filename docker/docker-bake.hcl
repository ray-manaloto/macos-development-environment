# docker/docker-bake.hcl
#
# Centralized build definitions for mde Docker images we build from source.
# Compose files handle runtime (up/down/networking/volumes) and pin pre-built images.
# Bake handles builds (multi-platform, attestations, build args).
#
# DESIGN DECISION: Only images we build from source get Bake targets.
# Pre-built images (Grafana, Tempo, Loki, PostgreSQL, Redis) are pinned by
# digest directly in their respective compose.yaml files. Bake cannot pull
# images — `docker buildx bake` is a build tool, not `docker pull`.
#
# Usage:
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
#     pgvector/pgvector:pg15-trixie@sha256:<pin at implementation time>
#     redis:8.2@sha256:<pin at implementation time>

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
# `docker buildx bake` with no args builds "default" (all buildable targets).
group "default" {
  targets = ["honcho-api", "honcho-deriver"]
}

# --- Memory targets ---
# Honcho API and deriver share the same upstream image but have different
# entrypoints. Both use the upstream ghcr.io/plastic-labs/honcho image
# directly — no custom Dockerfile needed unless we layer config on top.
#
# DECISION: Use upstream image directly in Compose (no custom build).
# These Bake targets exist as documentation and for future customization
# (e.g., adding a config overlay Dockerfile). They are currently no-ops
# because Compose references the upstream image by tag+digest.
# To enable custom builds, add a Dockerfile.honcho and update Compose
# to use `image: mde/honcho-api:latest` instead of the upstream ref.

target "honcho-api" {
  inherits   = ["_common"]
  context    = "memory"
  dockerfile = "Dockerfile.honcho"
  tags       = ["mde/honcho-api:latest"]
  args = {
    HONCHO_VERSION = "v3.0.3"
  }
}

target "honcho-deriver" {
  inherits   = ["_common"]
  context    = "memory"
  dockerfile = "Dockerfile.honcho"
  tags       = ["mde/honcho-deriver:latest"]
  args = {
    HONCHO_VERSION = "v3.0.3"
  }
}
