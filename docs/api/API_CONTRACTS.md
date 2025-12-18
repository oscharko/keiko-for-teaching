# Keiko API Contracts

This document provides an overview of all API contracts in the Keiko platform.

## Overview

Keiko uses two main API contract formats:

1. **OpenAPI 3.1.0** for REST APIs
2. **Protocol Buffers (proto3)** for gRPC APIs

## REST APIs (OpenAPI)

### Gateway BFF (`/api/*`)

The Gateway BFF is the main entry point for all client applications. It provides:

- **Authentication**: JWT bearer token authentication
- **Rate Limiting**: Configurable rate limits per endpoint
- **Request Logging**: Comprehensive request/response logging
- **Service Proxying**: Routes requests to appropriate backend services

**Endpoints:**
- `POST /api/chat` - Chat with AI
- `POST /api/search` - Search documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/{id}` - Get document metadata
- `GET /api/documents/{id}/download` - Download document
- `DELETE /api/documents/{id}` - Delete document
- `GET /api/documents` - List documents
- `POST /api/ideas` - Create idea
- `GET /api/ideas` - List ideas
- `GET /api/ideas/{id}` - Get idea details
- `GET /api/news` - List news articles

**Specification:** `services/gateway-bff/openapi.yaml`

### Chat Service

AI-powered chat service with Azure OpenAI integration.

**Features:**
- Standard and streaming responses
- RAG (Retrieval Augmented Generation)
- Follow-up question generation
- Response caching with Redis

**Endpoints:**
- `POST /api/chat` - Send chat message and receive AI response

**Specification:** `services/chat-service/openapi.yaml`

### Search Service

Document search with Azure AI Search integration.

**Features:**
- Hybrid search (text + vector)
- Semantic ranking
- Result highlighting
- Query caching

**Endpoints:**
- `POST /api/search` - Search documents

**Specification:** `services/search-service/openapi.yaml`

### Document Service

Document management with Azure Blob Storage.

**Features:**
- File upload/download
- Metadata management
- File type validation
- Document processing status tracking

**Endpoints:**
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/{id}` - Get document metadata
- `GET /api/documents/{id}/download` - Download document
- `DELETE /api/documents/{id}` - Delete document
- `GET /api/documents` - List documents

**Specification:** `services/document-service/openapi.yaml`

### Ideas Service

Innovation ideas management system.

**Features:**
- Idea submission and management
- Similar ideas detection
- Impact and feasibility scoring
- Status workflow (draft → submitted → under_review → approved/rejected → implemented)

**Endpoints:**
- `POST /api/ideas` - Submit new idea
- `GET /api/ideas` - List ideas with filtering
- `GET /api/ideas/{id}` - Get idea details
- `PUT /api/ideas/{id}` - Update idea
- `DELETE /api/ideas/{id}` - Delete idea
- `GET /api/ideas/{id}/similar` - Find similar ideas

**Specification:** `services/ideas-service/openapi.yaml`

## gRPC APIs (Protocol Buffers)

### Ingestion Service

Document parsing and ingestion service built in Rust.

**Features:**
- Multiple document format support (PDF, DOCX, HTML)
- Azure Document Intelligence integration
- Text chunking with configurable overlap
- Streaming responses for large documents
- Image extraction

**RPC Methods:**
- `ParseDocument` - Parse document and return chunks
- `ParseDocumentStream` - Parse document with streaming response
- `GetSupportedFormats` - Get list of supported file formats
- `HealthCheck` - Service health check

**Specification:** `packages/proto/ingestion/v1/ingestion.proto`

## Shared Types

TypeScript types shared across frontend and backend:

### Chat Types (`@keiko/shared-types/chat`)
- `Message` - Chat message
- `ChatRequest` - Chat request payload
- `ChatResponse` - Chat response payload
- `ChatOverrides` - Configuration overrides
- `DataPoints` - Search result data points

### Document Types (`@keiko/shared-types/document`)
- `DocumentMetadata` - Document metadata
- `UploadResponse` - Upload result
- `DocumentListResponse` - List of documents
- `DocumentStatus` - Document processing status

### Ideas Types (`@keiko/shared-types/ideas`)
- `Idea` - Idea entity
- `IdeaSubmission` - Idea submission payload
- `SimilarIdea` - Similar idea result
- `IdeaStatus` - Idea workflow status
- `RecommendationClass` - Recommendation classification

### Search Types (`@keiko/shared-types/search`)
- `SearchRequest` - Search request payload
- `SearchResponse` - Search results
- `SearchResult` - Individual search result

### User Types (`@keiko/shared-types/user`)
- `UserProfile` - User profile information
- `UserPreferences` - User preferences
- `UserSettings` - Combined user settings

### News Types (`@keiko/shared-types/news`)
- `NewsArticle` - News article entity
- `NewsListResponse` - List of news articles
- `NewsCategory` - News category enum

### Error Types (`@keiko/shared-types/error`)
- `ApiError` - Standard API error
- `ErrorCode` - Error code enum
- `ValidationError` - Validation error details

### Common Types (`@keiko/shared-types/common`)
- `HealthResponse` - Health check response
- `PaginatedResponse<T>` - Generic paginated response
- `ApiResponse<T>` - Generic API response wrapper

## Authentication

All services (except health endpoints) require JWT bearer token authentication:

```
Authorization: Bearer <jwt_token>
```

Tokens are issued by the Auth Service and validated by the Gateway BFF.

## Error Handling

All services use a consistent error response format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "field_name",
    "message": "Detailed error message"
  }
}
```

Common error codes:
- `VALIDATION_ERROR` - Request validation failed
- `AUTHENTICATION_ERROR` - Authentication required or failed
- `AUTHORIZATION_ERROR` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `RATE_LIMIT_EXCEEDED` - Rate limit exceeded
- `INTERNAL_SERVER_ERROR` - Internal server error

## Versioning

All APIs follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Current version: **0.1.0** (pre-release)

## Tools

### Validation

Validate all OpenAPI specifications:

```bash
make validate-api
```

### Code Generation

Generate TypeScript types from Protocol Buffers:

```bash
make generate-proto
```

### Documentation

View API documentation with Swagger UI:

```bash
swagger-ui-watcher services/chat-service/openapi.yaml
```

## Resources

- [OpenAPI Specification](https://spec.openapis.org/oas/v3.1.0)
- [Protocol Buffers](https://protobuf.dev/)
- [gRPC](https://grpc.io/)
- [Buf](https://buf.build/)

