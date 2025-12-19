# Build from repository root: docker build -t frontend -f apps/frontend/Dockerfile .
FROM node:20-alpine AS base

FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy workspace configuration files from root
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./

# Copy shared packages
COPY packages/ ./packages/

# Copy frontend package.json
COPY apps/frontend/package.json ./apps/frontend/

# Install dependencies using pnpm with workspace support
RUN corepack enable pnpm && pnpm install --frozen-lockfile

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/packages ./packages
COPY --from=deps /app/apps/frontend/node_modules ./apps/frontend/node_modules

# Copy frontend source code
COPY apps/frontend/ ./apps/frontend/

# Remove test files and directories to avoid TypeScript errors during build
RUN find ./apps/frontend -name "*.test.ts" -delete && \
    find ./apps/frontend -name "*.test.tsx" -delete && \
    find ./apps/frontend -name "*.spec.ts" -delete && \
    find ./apps/frontend -name "*.spec.tsx" -delete && \
    rm -rf ./apps/frontend/src/test 2>/dev/null || true && \
    find ./apps/frontend -type d -name "__tests__" -exec rm -rf {} + 2>/dev/null || true

WORKDIR /app/apps/frontend
ENV NEXT_TELEMETRY_DISABLED=1
RUN corepack enable pnpm && pnpm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy the standalone output - this includes server.js and the app structure
COPY --from=builder --chown=nextjs:nodejs /app/apps/frontend/.next/standalone ./

# Copy the frontend-specific node_modules (has correct symlinks for this location)
COPY --from=builder --chown=nextjs:nodejs /app/apps/frontend/node_modules ./apps/frontend/node_modules

# Copy the root node_modules with .pnpm store
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules

# Copy public folder to the correct location (apps/frontend/public)
COPY --from=builder /app/apps/frontend/public ./apps/frontend/public

# Copy static files to the correct location (apps/frontend/.next/static)
COPY --from=builder --chown=nextjs:nodejs /app/apps/frontend/.next/static ./apps/frontend/.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Set NODE_PATH so that node can find modules in apps/frontend/node_modules
ENV NODE_PATH=/app/apps/frontend/node_modules

# The server.js is in the root /app/ directory
CMD ["node", "server.js"]

