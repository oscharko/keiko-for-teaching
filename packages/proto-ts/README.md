# @keiko/proto-ts

TypeScript types and clients generated from Protocol Buffers for Keiko services.

## Overview

This package contains TypeScript definitions and gRPC clients generated from the Protocol Buffer definitions in `packages/proto/`.

## Usage

```typescript
import { IngestionServiceClient } from '@keiko/proto-ts';

// Create a client instance
const client = new IngestionServiceClient('http://localhost:50051');

// Use the client
const response = await client.parseDocument({
  content: fileBuffer,
  filename: 'document.pdf',
  content_type: 'application/pdf',
  options: {
    max_tokens_per_chunk: 512,
    overlap_percent: 10,
    use_document_intelligence: true,
  },
});
```

## Generating Types

To regenerate the TypeScript types from the proto files:

```bash
npm run generate
```

This will:
1. Run `buf` to compile the proto files
2. Generate TypeScript types in `src/`
3. Generate gRPC client code

## Building

```bash
npm run build
```

This compiles the TypeScript code to JavaScript in the `dist/` directory.

## Dependencies

- `@bufbuild/protobuf` - Protocol Buffers runtime for TypeScript
- `@connectrpc/connect` - gRPC-Web and Connect RPC client

## Development

The source files in `src/` are auto-generated. Do not edit them manually.
Instead, modify the `.proto` files in `packages/proto/` and regenerate.

