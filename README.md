# Keiko for Teaching

Enterprise AI Assistant - Monorepo with Turborepo.

## Quick Start

```bash
pnpm install
pnpm dev
```

## Structure

- `apps/frontend` - Next.js 15 Frontend
- `services/gateway-bff` - FastAPI Gateway BFF
- `services/chat-service` - FastAPI Chat/RAG Service
- `services/ingestion-service` - Rust Document Ingestion
- `packages/shared-types` - TypeScript Types
- `packages/proto` - Protobuf Definitions
- `infra/bicep` - Azure Bicep Templates
- `infra/kubernetes` - Kubernetes Manifests

## Development

```bash
docker compose up -d
pnpm dev
```

