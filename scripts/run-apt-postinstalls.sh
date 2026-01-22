#!/usr/bin/env bash
set -euo pipefail

export DATABASE_URL="file:./dev.db"
export DIRECT_URL="file:./dev.db"

# Use Prisma 5 for this package's generate; avoid Prisma 7 schema validation.
bunx prisma@5.20.0 generate --schema node_modules/awesome-chatgpt-prompts/prisma/schema.prisma

# Trust and run remaining postinstalls for this package (with env set).
bun pm trust awesome-chatgpt-prompts
