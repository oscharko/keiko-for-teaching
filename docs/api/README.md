# Keiko API Documentation

This directory contains the OpenAPI specifications for all Keiko services.

## Overview

Keiko uses OpenAPI 3.1.0 to document all REST APIs. Each service has its own OpenAPI specification file.

## Services

### Gateway BFF
- **File**: `services/gateway-bff/openapi.yaml`
- **Port**: 8000
- **Description**: Backend-for-Frontend gateway that aggregates and proxies requests to backend services
- **Features**:
  - Authentication middleware
  - Rate limiting
  - Request logging
  - CORS handling

### Chat Service
- **File**: `services/chat-service/openapi.yaml`
- **Port**: 8001
- **Description**: AI chat service with Azure OpenAI integration
- **Features**:
  - Standard and streaming responses
  - RAG (Retrieval Augmented Generation)
  - Follow-up question generation
  - Response caching

### Search Service
- **File**: `services/search-service/openapi.yaml`
- **Port**: 8002
- **Description**: Document search with Azure AI Search
- **Features**:
  - Hybrid search (text + vector)
  - Semantic ranking
  - Result highlighting
  - Query caching

### Document Service
- **File**: `services/document-service/openapi.yaml`
- **Port**: 8003
- **Description**: Document management with Azure Blob Storage
- **Features**:
  - File upload/download
  - Metadata management
  - File type validation
  - Document processing status

### Ideas Service
- **File**: `services/ideas-service/openapi.yaml`
- **Port**: 8005
- **Description**: Innovation ideas management
- **Features**:
  - Idea submission
  - Similar ideas detection
  - Impact scoring
  - Status workflow

## Viewing the Documentation

### Using Swagger UI

You can view the API documentation using Swagger UI:

```bash
# Install swagger-ui-watcher globally
npm install -g swagger-ui-watcher

# View a specific service
swagger-ui-watcher services/chat-service/openapi.yaml
```

### Using Redoc

Alternatively, use Redoc for a different viewing experience:

```bash
# Install redoc-cli globally
npm install -g redoc-cli

# Generate static HTML
redoc-cli bundle services/chat-service/openapi.yaml -o docs/api/chat-service.html
```

### Using VS Code

Install the "OpenAPI (Swagger) Editor" extension for VS Code to view and edit OpenAPI files with syntax highlighting and validation.

## Generating Client SDKs

You can generate client SDKs from the OpenAPI specifications:

### TypeScript/JavaScript

```bash
# Install openapi-generator-cli
npm install -g @openapitools/openapi-generator-cli

# Generate TypeScript client
openapi-generator-cli generate \
  -i services/chat-service/openapi.yaml \
  -g typescript-fetch \
  -o packages/api-client-ts
```

### Python

```bash
# Generate Python client
openapi-generator-cli generate \
  -i services/chat-service/openapi.yaml \
  -g python \
  -o packages/api-client-py
```

## Validation

Validate OpenAPI specifications:

```bash
# Install openapi-cli
npm install -g @redocly/cli

# Validate a specification
redocly lint services/chat-service/openapi.yaml
```

## Best Practices

1. **Versioning**: All APIs use semantic versioning (e.g., v0.1.0)
2. **Error Responses**: Consistent error response format across all services
3. **Authentication**: JWT bearer token authentication where required
4. **Rate Limiting**: Documented in Gateway BFF
5. **Pagination**: Consistent pagination parameters (skip, limit)
6. **Filtering**: OData-style filter expressions where applicable

## Common Schemas

All services share common schemas:

- `HealthResponse`: Health check response
- `ErrorResponse`: Error response format
- `PaginatedResponse`: Paginated list response

## Protocol Buffers

For gRPC services (like the Ingestion Service), see the Protocol Buffers documentation:

- **Directory**: `packages/proto/`
- **Documentation**: `packages/proto-ts/README.md`

## Contributing

When adding or modifying APIs:

1. Update the OpenAPI specification file
2. Validate the specification
3. Update this README if adding a new service
4. Generate updated client SDKs if needed
5. Update integration tests

## Resources

- [OpenAPI Specification](https://spec.openapis.org/oas/v3.1.0)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [Redoc](https://redocly.com/redoc/)
- [OpenAPI Generator](https://openapi-generator.tech/)

