#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export DATABASE_URL="file:./dev.db"
export DIRECT_URL="file:./dev.db"

# Step 1: run generate with Prisma 5 to produce client locally in the package.
bunx prisma@5.20.0 generate --schema node_modules/awesome-chatgpt-prompts/prisma/schema.prisma

# Step 2: run postinstall with env set; Prisma 7 schema validation will still complain,
# so temporarily set PRISMA_HIDE_UPDATE_MESSAGE to reduce noise.
PRISMA_HIDE_UPDATE_MESSAGE=1 bun pm trust awesome-chatgpt-prompts || true

echo "If postinstall remains blocked, keep the generated client and skip trust." 
